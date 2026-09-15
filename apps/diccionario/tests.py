import json
from importlib import import_module
from datetime import date, timedelta
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image
from django.apps import apps
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.contrib.staticfiles import finders
from django.db import connection
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    ActividadUsuario, BusquedaPopularDiaria, CandidataImagenPexels, Categoria, EjemploUso, EstadisticaJuego, HistorialBusqueda, IntentoPalabraJuego, Palabra,
    PreparacionImagenVocabulario, ProgresoPalabraJuego, RelacionPalabra, SesionJuego,
)
from .models import PalabraFavorita
from apps.usuarios.models import PerfilUsuario
from .services.clasificacion import (
    calcular_dificultad_pronunciacion,
    clasificar_textos,
)
from .services.ia_kichwa import obtener_configuracion_ia
from .services.relaciones import obtener_palabras_relacionadas
from .services.reto_semanal import reto_semanal


class LimpiezaTerminosTests(TestCase):
    def test_guardado_e_importacion_quitan_puntos_terminales(self):
        categoria = Categoria.objects.create(nombre='Animales')
        palabra = Palabra.objects.create(
            palabra_kichwa=' Misi. ', traduccion_espanol=' Gato. ', categoria=categoria,
            apta_para_juegos=True,
        )
        palabra.refresh_from_db()
        self.assertEqual((palabra.palabra_kichwa, palabra.traduccion_espanol), ('Misi', 'Gato'))
        self.assertEqual((palabra.busqueda_kichwa, palabra.busqueda_espanol), ('misi', 'gato'))

        comando = import_module('apps.diccionario.management.commands.cargar_palabras_masivo').Command(stdout=StringIO())
        creadas, existentes = comando.cargar_palabras([('Misi.', 'Gato.', 'Animal doméstico')], 'kichwa_espanol')
        self.assertEqual((creadas, existentes), (0, 1))
        self.assertEqual(Palabra.objects.count(), 1)

    def test_migracion_unifica_duplicados_y_conserva_progreso_y_sesiones(self):
        categoria = Categoria.objects.create(nombre='Animales')
        usuario = User.objects.create_user('runa', password='clave-segura-123')
        principal = Palabra.objects.create(
            palabra_kichwa='misi', traduccion_espanol='gato', categoria=categoria,
            pronunciacion='mi-si',
        )
        duplicada = Palabra.objects.create(
            palabra_kichwa='misi variante', traduccion_espanol='gato', categoria=categoria,
            apta_para_juegos=True, descripcion_juego_kichwa='misi',
        )
        Palabra.objects.filter(pk=duplicada.pk).update(palabra_kichwa='misi.', pronunciacion='mi-si-.')
        tercera = Palabra.objects.create(
            palabra_kichwa='allku variante', traduccion_espanol='perro', categoria=categoria,
        )
        Palabra.objects.filter(pk=tercera.pk).update(palabra_kichwa='allku.', pronunciacion='al-lk-u.')
        PalabraFavorita.objects.create(usuario=usuario, palabra=principal)
        PalabraFavorita.objects.create(usuario=usuario, palabra=duplicada)
        BusquedaPopularDiaria.objects.create(palabra=principal, consultas=2)
        BusquedaPopularDiaria.objects.create(palabra=duplicada, consultas=3)
        ProgresoPalabraJuego.objects.create(usuario=usuario, palabra=principal, intentos=2, respuestas_correctas=1)
        ProgresoPalabraJuego.objects.create(usuario=usuario, palabra=duplicada, intentos=3, respuestas_correctas=2)
        sesion = SesionJuego.objects.create(
            usuario=usuario, tipo_juego='traduccion', dificultad='medio',
            palabras_ids=[duplicada.pk, tercera.pk], pistas_palabras_ids=[duplicada.pk],
        )
        IntentoPalabraJuego.objects.create(sesion=sesion, palabra=duplicada, correcta=True)
        RelacionPalabra.objects.create(origen=tercera, destino=duplicada, tipo='contexto')
        EjemploUso.objects.create(
            palabra=duplicada, oracion_kichwa='Misi shamun.',
            traduccion_espanol='El gato viene.', fuente='Prueba',
        )

        migracion = import_module('apps.diccionario.migrations.0026_limpiar_puntos_terminales')
        migracion.limpiar_puntos_terminales(apps, SimpleNamespace(connection=connection))

        self.assertFalse(Palabra.objects.filter(pk=duplicada.pk).exists())
        principal.refresh_from_db()
        tercera.refresh_from_db()
        sesion.refresh_from_db()
        self.assertEqual((principal.palabra_kichwa, principal.traduccion_espanol), ('misi', 'gato'))
        self.assertTrue(principal.apta_para_juegos)
        self.assertEqual(principal.descripcion_juego_kichwa, 'misi')
        self.assertEqual((tercera.palabra_kichwa, tercera.pronunciacion), ('allku', 'al-lk-u'))
        self.assertEqual(sesion.palabras_ids, [principal.pk, tercera.pk])
        self.assertEqual(sesion.pistas_palabras_ids, [principal.pk])
        self.assertEqual(IntentoPalabraJuego.objects.get(sesion=sesion).palabra_id, principal.pk)
        self.assertEqual(EjemploUso.objects.get().palabra_id, principal.pk)
        self.assertEqual(RelacionPalabra.objects.get().destino_id, principal.pk)
        self.assertEqual(PalabraFavorita.objects.filter(usuario=usuario, palabra=principal).count(), 1)
        self.assertEqual(BusquedaPopularDiaria.objects.get(palabra=principal).consultas, 5)
        progreso = ProgresoPalabraJuego.objects.get(usuario=usuario, palabra=principal)
        self.assertEqual((progreso.intentos, progreso.respuestas_correctas), (5, 3))


class DiccionarioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(nombre='General')
        cls.palabra = Palabra.objects.create(
            palabra_kichwa='Yaku', traduccion_espanol='Agua', definicion='Líquido.', categoria=cls.categoria
        )
        cls.coincidencia_parcial = Palabra.objects.create(
            palabra_kichwa='Yaku mama', traduccion_espanol='Madre del agua', categoria=cls.categoria
        )
        cls.coincidencia_espanol = Palabra.objects.create(
            palabra_kichwa='Mayu', traduccion_espanol='Agua corriente', categoria=cls.categoria
        )
        cls.animales = Categoria.objects.create(nombre='Animales')
        cls.misi = Palabra.objects.create(
            palabra_kichwa='Misi', traduccion_espanol='Gato', categoria=cls.animales,
            nivel_dificultad='intermedio', dificultad='medio', apta_para_juegos=True,
        )

    def test_categorias_no_falla_y_cuenta_palabras(self):
        respuesta = self.client.get(reverse('diccionario:categorias'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['categorias'].get(pk=self.categoria.pk).total_palabras, 3)

    def test_busqueda_autenticada_guarda_campos_reales(self):
        usuario = User.objects.create_user('mashi', password='contrasena-segura-123')
        self.client.force_login(usuario)
        self.client.get(reverse('diccionario:buscar'), {'termino': 'Yaku'})
        historial = HistorialBusqueda.objects.get(usuario=usuario)
        self.assertEqual(historial.termino_buscado, 'Yaku')
        self.assertEqual(historial.resultados_encontrados, 2)
        self.assertTrue(ActividadUsuario.objects.filter(usuario=usuario, tipo='busqueda', busqueda=historial).exists())

    def test_tendencia_se_cuenta_solo_para_entrada_exacta_y_sin_paginacion(self):
        url = reverse('diccionario:buscar')
        self.client.get(url, {'termino': 'Yaku'})
        self.client.get(url, {'termino': 'agua'})
        self.client.get(url, {'termino': 'yak'})
        self.client.get(url, {'termino': 'Yaku', 'page': '2'})
        conteo = BusquedaPopularDiaria.objects.get(palabra=self.palabra)
        self.assertEqual(conteo.consultas, 2)
        self.assertEqual(HistorialBusqueda.objects.count(), 0)

        BusquedaPopularDiaria.objects.create(
            palabra=self.misi, fecha=timezone.localdate() - timedelta(days=7), consultas=90,
        )
        inicio = self.client.get(reverse('diccionario:home'))
        self.assertEqual(inicio.context['tendencias'][0]['palabra'], self.palabra)
        self.assertEqual(inicio.context['tendencias'][0]['consultas'], 2)
        self.assertNotIn(self.misi, [item['palabra'] for item in inicio.context['tendencias']])

    def test_ranking_solo_incluye_cuentas_activas_con_participacion_voluntaria(self):
        visible = User.objects.create_user('amaru', password='clave-segura-123')
        privado = User.objects.create_user('killa', password='clave-segura-123')
        inactivo = User.objects.create_user('inti', password='clave-segura-123', is_active=False)
        PerfilUsuario.objects.filter(usuario=visible).update(puntos_totales=20, participa_ranking=True)
        PerfilUsuario.objects.filter(usuario=privado).update(puntos_totales=90)
        PerfilUsuario.objects.filter(usuario=inactivo).update(puntos_totales=100, participa_ranking=True)
        respuesta = self.client.get(reverse('diccionario:home'))
        self.assertEqual([item.usuario.username for item in respuesta.context['ranking']], ['amaru'])
        self.assertContains(respuesta, 'amaru')
        self.assertNotContains(respuesta, 'killa</span>')

    def test_reto_semanal_rota_los_lunes_y_no_muestra_avance_anonimo(self):
        lunes = date(2026, 9, 7)
        actual = reto_semanal(None, lunes)
        self.assertEqual(actual['inicio'], lunes)
        self.assertEqual(reto_semanal(None, lunes + timedelta(days=6))['tipo'], actual['tipo'])
        self.assertNotEqual(reto_semanal(None, lunes + timedelta(days=7))['tipo'], actual['tipo'])
        retos = [reto_semanal(None, lunes + timedelta(weeks=numero)) for numero in range(5)]
        self.assertEqual(len({reto['tipo'] for reto in retos}), 5)
        for reto in retos:
            self.assertTrue(reverse(reto['url']).startswith('/juegos/'))
        self.assertIsNone(actual['avance'])
        inicio = self.client.get(reverse('diccionario:home'))
        self.assertContains(inicio, 'Reto de esta semana')
        self.assertNotContains(inicio, 'Avance privado del reto semanal')

    def test_reto_semanal_cuenta_solo_aciertos_distintos_del_titular_y_semana(self):
        usuario = User.objects.create_user('reto', password='contrasena-segura-123')
        otro = User.objects.create_user('otro-reto', password='contrasena-segura-123')
        reto = reto_semanal(usuario)
        palabras = [self.palabra, self.misi]
        for numero in range(3):
            palabras.append(Palabra.objects.create(
                palabra_kichwa=f'Palabra {numero}', traduccion_espanol=f'Traducción {numero}',
                categoria=self.categoria,
            ))
        sesion = SesionJuego.objects.create(
            usuario=usuario, tipo_juego=reto['tipo'], dificultad='medio',
            palabras_ids=[palabra.pk for palabra in palabras],
        )
        for palabra in palabras[:4]:
            IntentoPalabraJuego.objects.create(sesion=sesion, palabra=palabra, correcta=True)
        IntentoPalabraJuego.objects.create(sesion=sesion, palabra=palabras[0], correcta=True)
        IntentoPalabraJuego.objects.create(sesion=sesion, palabra=palabras[4], correcta=False)
        otra_modalidad = 'completar' if reto['tipo'] == 'traduccion' else 'traduccion'
        sesion_distinta = SesionJuego.objects.create(
            usuario=usuario, tipo_juego=otra_modalidad, dificultad='medio',
            palabras_ids=[palabras[4].pk],
        )
        IntentoPalabraJuego.objects.create(sesion=sesion_distinta, palabra=palabras[4], correcta=True)
        anterior = IntentoPalabraJuego.objects.create(sesion=sesion, palabra=palabras[4], correcta=True)
        IntentoPalabraJuego.objects.filter(pk=anterior.pk).update(
            fecha=timezone.now() - timedelta(days=8),
        )
        otra_sesion = SesionJuego.objects.create(
            usuario=otro, tipo_juego=reto['tipo'], dificultad='medio',
            palabras_ids=[palabras[4].pk],
        )
        IntentoPalabraJuego.objects.create(sesion=otra_sesion, palabra=palabras[4], correcta=True)

        self.client.force_login(usuario)
        inicio = self.client.get(reverse('diccionario:home'))
        self.assertEqual(inicio.context['reto_semana']['avance'], 4)
        self.assertFalse(inicio.context['reto_semana']['completado'])
        self.assertContains(inicio, '4 de 5 palabras')
        IntentoPalabraJuego.objects.create(sesion=sesion, palabra=palabras[4], correcta=True)
        self.assertTrue(reto_semanal(usuario)['completado'])
        self.assertEqual(reto_semanal(usuario)['avance'], 5)

    def test_detalle_incrementa_vistas(self):
        self.client.get(self.palabra.get_absolute_url())
        self.palabra.refresh_from_db()
        self.assertEqual(self.palabra.veces_vista, 1)

    def test_ejemplos_solo_se_publican_tras_revision_y_se_retiran_al_editar(self):
        self.palabra.ejemplo_uso = 'Yaku - Agua'
        self.palabra.save(update_fields=['ejemplo_uso'])
        ejemplo = EjemploUso.objects.create(
            palabra=self.palabra, oracion_kichwa='Yaku shamun.',
            traduccion_espanol='El agua llega.', fuente='Material de prueba',
        )
        detalle = self.client.get(self.palabra.get_absolute_url())
        self.assertNotContains(detalle, 'Yaku - Agua')
        self.assertNotContains(detalle, 'Yaku shamun.')

        revisor = User.objects.create_superuser('revisor', 'revisor@example.com', 'clave-segura-123')
        self.client.force_login(revisor)
        respuesta = self.client.post(reverse('admin:diccionario_ejemplouso_changelist'), {
            'action': 'publicar_revisados', '_selected_action': [ejemplo.pk], 'index': 0,
        })
        self.assertEqual(respuesta.status_code, 302)
        ejemplo.refresh_from_db()
        self.assertEqual(ejemplo.estado, 'publicado')
        self.assertEqual(ejemplo.tipo_revision, 'humana')
        self.assertEqual(ejemplo.revisado_por, revisor)
        self.assertIsNotNone(ejemplo.fecha_revision)
        self.client.logout()
        detalle = self.client.get(self.palabra.get_absolute_url())
        self.assertContains(detalle, 'Yaku shamun.')
        self.assertContains(detalle, 'El agua llega.')
        self.assertContains(detalle, 'Material de prueba')

        self.client.force_login(revisor)
        self.client.post(reverse('admin:diccionario_ejemplouso_changelist'), {
            'action': 'retirar_publicacion', '_selected_action': [ejemplo.pk], 'index': 0,
        })
        ejemplo.refresh_from_db()
        self.assertEqual(ejemplo.estado, 'borrador')
        self.assertNotContains(self.client.get(self.palabra.get_absolute_url()), 'Yaku shamun.')
        self.client.post(reverse('admin:diccionario_ejemplouso_changelist'), {
            'action': 'publicar_revisados', '_selected_action': [ejemplo.pk], 'index': 0,
        })
        ejemplo.refresh_from_db()
        self.assertEqual(ejemplo.estado, 'publicado')
        self.client.logout()

        ejemplo.oracion_kichwa = 'Yaku chiri kan.'
        ejemplo.save(update_fields=['oracion_kichwa'])
        ejemplo.refresh_from_db()
        self.assertEqual(ejemplo.estado, 'borrador')
        self.assertIsNone(ejemplo.revisado_por)
        self.assertIsNone(ejemplo.fecha_revision)
        self.assertEqual(ejemplo.tipo_revision, '')
        self.assertNotContains(self.client.get(self.palabra.get_absolute_url()), 'Yaku chiri kan.')

    def test_ejemplo_rechaza_equivalencia_automatica_y_fuente_vacia(self):
        with self.assertRaises(ValidationError):
            EjemploUso.objects.create(
                palabra=self.palabra, oracion_kichwa='Yaku - Agua',
                traduccion_espanol='Agua', fuente='Material de prueba',
            )
        with self.assertRaises(ValidationError):
            EjemploUso.objects.create(
                palabra=self.palabra, oracion_kichwa='Yaku shamun.',
                traduccion_espanol='El agua llega.', fuente='   ',
            )
        borrador = EjemploUso.objects.create(
            palabra=self.palabra, oracion_kichwa='Yaku shamun.',
            traduccion_espanol='El agua llega.', fuente='Material de prueba',
        )
        EjemploUso.objects.filter(pk=borrador.pk).update(oracion_kichwa='Yaku - Agua')
        revisor = User.objects.create_superuser('revisor', 'revisor@example.com', 'clave-segura-123')
        self.client.force_login(revisor)
        self.client.post(reverse('admin:diccionario_ejemplouso_changelist'), {
            'action': 'publicar_revisados', '_selected_action': [borrador.pk], 'index': 0,
        })
        borrador.refresh_from_db()
        self.assertEqual(borrador.estado, 'borrador')
        self.assertIsNone(borrador.revisado_por)

    def test_migracion_limpia_solo_marcadores_automaticos(self):
        self.palabra.ejemplo_uso = 'Yaku - Agua'
        self.palabra.save(update_fields=['ejemplo_uso'])
        self.misi.ejemplo_uso = 'Texto heredado distinto para revisar.'
        self.misi.save(update_fields=['ejemplo_uso'])
        migracion = import_module('apps.diccionario.migrations.0025_ejemplos_uso_revisados')
        migracion.limpiar_equivalencias_automaticas(apps, SimpleNamespace(connection=connection))
        self.palabra.refresh_from_db()
        self.misi.refresh_from_db()
        self.assertIsNone(self.palabra.ejemplo_uso)
        self.assertEqual(self.misi.ejemplo_uso, 'Texto heredado distinto para revisar.')

    def test_modulo_autorizado_prepara_y_publica_cotejo_documental_sin_duplicar(self):
        from .management.commands.preparar_ejemplos_modulo_2023 import EJEMPLOS

        for kichwa, significado in {(fila[0], fila[1]) for fila in EJEMPLOS}:
            Palabra.objects.create(
                palabra_kichwa=kichwa, traduccion_espanol=significado, categoria=self.categoria,
            )
        salida = StringIO()
        call_command('preparar_ejemplos_modulo_2023', stdout=salida)
        self.assertEqual(EjemploUso.objects.count(), len(EJEMPLOS))
        self.assertEqual(EjemploUso.objects.filter(estado='publicado').count(), 0)
        self.assertTrue(EjemploUso.objects.filter(fuente__contains='página PDF 29').exists())
        call_command('preparar_ejemplos_modulo_2023', '--publicar-cotejados', stdout=salida)
        self.assertEqual(EjemploUso.objects.count(), len(EJEMPLOS))
        self.assertEqual(EjemploUso.objects.filter(
            estado='publicado', tipo_revision='documental', revisado_por__isnull=True,
        ).count(), len(EJEMPLOS))
        primera_fecha = EjemploUso.objects.order_by('pk').values_list('fecha_revision', flat=True).first()
        call_command('preparar_ejemplos_modulo_2023', '--publicar-cotejados', stdout=salida)
        self.assertEqual(
            EjemploUso.objects.order_by('pk').values_list('fecha_revision', flat=True).first(),
            primera_fecha,
        )
        shamuna = Palabra.objects.get(palabra_kichwa='shamuna')
        detalle = self.client.get(shamuna.get_absolute_url())
        self.assertContains(detalle, 'Kayman shamuy.')
        self.assertContains(detalle, 'Cotejado con la fuente citada')

    def test_imagen_original_se_asocia_a_la_acepcion_exacta(self):
        palabra = Palabra.objects.create(
            palabra_kichwa='yaku', traduccion_espanol='agua', categoria=self.categoria,
        )
        otra_acepcion = Palabra.objects.create(
            palabra_kichwa='yaku', traduccion_espanol='octubre', categoria=self.categoria,
        )
        migracion = import_module('apps.diccionario.migrations.0027_imagenes_y_revision_documental')
        migracion.asociar_imagenes(apps, SimpleNamespace(connection=connection))
        palabra.refresh_from_db()
        otra_acepcion.refresh_from_db()
        self.assertEqual(palabra.imagen_vocabulario, 'img/vocabulario/yaku-agua.webp')
        self.assertEqual(otra_acepcion.imagen_vocabulario, '')
        self.assertTrue(finders.find(palabra.imagen_vocabulario))
        detalle = self.client.get(palabra.get_absolute_url())
        self.assertContains(detalle, palabra.imagen_vocabulario)
        self.assertContains(detalle, palabra.descripcion_imagen)

    def test_lote_clasifica_todas_las_acepciones_y_prepara_solo_concretas(self):
        animales = self.animales
        acciones = Categoria.objects.create(nombre='Acciones y procesos')
        misi = Palabra.objects.create(
            palabra_kichwa='misi lote', traduccion_espanol='gato', categoria=animales,
            apta_para_juegos=True,
        )
        rina = Palabra.objects.create(
            palabra_kichwa='rina lote', traduccion_espanol='ir', categoria=acciones,
            apta_para_juegos=True,
        )

        call_command('preparar_lote_imagenes', '--solo-clasificar', stdout=StringIO())
        preparacion_misi = PreparacionImagenVocabulario.objects.get(palabra=misi)
        preparacion_rina = PreparacionImagenVocabulario.objects.get(palabra=rina)
        self.assertEqual(preparacion_misi.tipo_visual, 'ser_vivo')
        self.assertEqual(preparacion_rina.tipo_visual, 'accion')
        PreparacionImagenVocabulario.objects.exclude(palabra__in=[misi, rina]).update(estado='descartada')

        with TemporaryDirectory() as temporal:
            salida = Path(temporal) / 'lote.csv'
            call_command(
                'preparar_lote_imagenes', '--cantidad', '1', '--lote', '77',
                '--salida', str(salida), stdout=StringIO(),
            )
            self.assertTrue(salida.exists())
            self.assertIn('palabra_id', salida.read_text(encoding='utf-8-sig'))

        preparacion_misi.refresh_from_db()
        preparacion_rina.refresh_from_db()
        self.assertEqual((preparacion_misi.tipo_visual, preparacion_misi.estado), ('ser_vivo', 'preparada'))
        self.assertEqual((preparacion_misi.lote, preparacion_misi.orden_lote), (77, 1))
        self.assertIn('“misi lote”', preparacion_misi.prompt)
        self.assertEqual((preparacion_rina.tipo_visual, preparacion_rina.estado), ('accion', 'clasificada'))

    def test_admin_publica_imagen_solo_despues_de_revision(self):
        administrador = User.objects.create_superuser('imagenadmin', 'admin@example.com', 'clave-segura-123')
        palabra = Palabra.objects.create(
            palabra_kichwa='misi imagen', traduccion_espanol='gato', categoria=self.categoria,
        )
        otra_acepcion = Palabra.objects.create(
            palabra_kichwa='misi imagen', traduccion_espanol='felino', categoria=self.categoria,
        )
        preparacion = PreparacionImagenVocabulario.objects.create(
            palabra=palabra, tipo_visual='ser_vivo', estado='generada',
            ruta_candidata='img/vocabulario/misi-gato.webp',
            descripcion_candidata='Gato gris sentado sobre una estera tejida.',
            proveedor_candidato='pexels', autor_candidato='Killa Foto',
            autor_candidato_url='https://www.pexels.com/@killa-foto',
            fuente_candidata_url='https://www.pexels.com/photo/gato-123/',
            credito_candidato='Fotografía de Killa Foto en Pexels.',
        )
        self.client.force_login(administrador)
        listado = reverse('admin:diccionario_preparacionimagenvocabulario_changelist')
        self.client.post(listado, {
            'action': 'aprobar_revisadas', '_selected_action': [preparacion.pk], 'index': 0,
        })
        preparacion.refresh_from_db()
        self.assertEqual(preparacion.estado, 'revisada')
        self.assertEqual(preparacion.revisada_por, administrador)
        self.assertEqual(palabra.imagen_vocabulario, '')

        self.client.post(listado, {
            'action': 'publicar_aprobadas', '_selected_action': [preparacion.pk], 'index': 0,
        })
        preparacion.refresh_from_db()
        palabra.refresh_from_db()
        otra_acepcion.refresh_from_db()
        self.assertEqual(preparacion.estado, 'publicada')
        self.assertEqual(palabra.imagen_vocabulario, 'img/vocabulario/misi-gato.webp')
        self.assertEqual(palabra.proveedor_imagen, 'pexels')
        detalle = self.client.get(palabra.get_absolute_url())
        self.assertContains(detalle, 'Killa Foto')
        self.assertContains(detalle, 'https://www.pexels.com/photo/gato-123/')
        self.assertEqual(otra_acepcion.imagen_vocabulario, '')

    def test_pexels_guarda_candidatas_y_descarga_webp_sin_publicar(self):
        palabra = Palabra.objects.create(
            palabra_kichwa='challwa lote', traduccion_espanol='pez', categoria=self.animales,
        )
        preparacion = PreparacionImagenVocabulario.objects.create(
            palabra=palabra, tipo_visual='ser_vivo', estado='preparada', lote=88, orden_lote=1,
            prompt='Prompt de prueba', descripcion_candidata='Pez nadando en agua clara.',
        )
        respuesta_pexels = {
            'fotos': [{
                'pexels_id': 12345,
                'url_foto': 'https://www.pexels.com/photo/pez-12345/',
                'url_imagen': 'https://images.pexels.com/photos/12345/pez.jpeg',
                'fotografo': 'Runa Foto',
                'url_fotografo': 'https://www.pexels.com/@runa-foto',
                'descripcion_original': 'Fish underwater',
                'ancho': 1200,
                'alto': 1200,
                'color_promedio': '#336699',
            }],
            'limite': '20000', 'restantes': '19999', 'reinicio': '0',
        }
        with override_settings(PEXELS_API_KEY='clave-de-prueba'):
            with patch(
                'apps.diccionario.management.commands.buscar_candidatas_pexels.PexelsClient.buscar_fotos',
                return_value=respuesta_pexels,
            ):
                call_command(
                    'buscar_candidatas_pexels', '--lote', '88', '--seleccionar-primera',
                    stdout=StringIO(),
                )
        candidata = CandidataImagenPexels.objects.get(preparacion=preparacion)
        self.assertTrue(candidata.seleccionada)

        contenido = BytesIO()
        Image.new('RGB', (900, 700), '#336699').save(contenido, 'PNG')
        with TemporaryDirectory() as temporal:
            with override_settings(STATICFILES_DIRS=[Path(temporal)]):
                with patch(
                    'apps.diccionario.management.commands.descargar_candidatas_pexels.descargar_imagen_pexels',
                    return_value=contenido.getvalue(),
                ):
                    call_command('descargar_candidatas_pexels', '--lote', '88', stdout=StringIO())
            preparacion.refresh_from_db()
            archivo = Path(temporal) / preparacion.ruta_candidata
            self.assertTrue(archivo.exists())
            with Image.open(archivo) as imagen:
                self.assertEqual((imagen.format, imagen.size), ('WEBP', (768, 768)))

        palabra.refresh_from_db()
        self.assertEqual(preparacion.estado, 'generada')
        self.assertEqual(preparacion.proveedor_candidato, 'pexels')
        self.assertEqual(preparacion.autor_candidato, 'Runa Foto')
        self.assertEqual(palabra.imagen_vocabulario, '')

    def test_cliente_pexels_usa_autorizacion_y_busqueda_cuadrada_en_espanol(self):
        from .services.pexels import PexelsClient

        datos = json.dumps({
            'photos': [{
                'id': 44,
                'url': 'https://www.pexels.com/photo/gato-44/',
                'photographer': 'Killa Foto',
                'photographer_url': 'https://www.pexels.com/@killa-foto',
                'width': 1000,
                'height': 1000,
                'avg_color': '#abcdef',
                'alt': 'Cat',
                'src': {'large2x': 'https://images.pexels.com/photos/44/gato.jpeg'},
            }],
        }).encode('utf-8')

        class Respuesta:
            headers = {'X-Ratelimit-Limit': '20000', 'X-Ratelimit-Remaining': '19999'}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, _cantidad):
                return datos

        with patch('apps.diccionario.services.pexels.urlopen', return_value=Respuesta()) as abrir:
            resultado = PexelsClient(api_key='clave-segura-de-prueba', timeout=1).buscar_fotos('gato')
        solicitud = abrir.call_args.args[0]
        self.assertEqual(solicitud.get_header('Authorization'), 'clave-segura-de-prueba')
        self.assertIn('query=gato', solicitud.full_url)
        self.assertIn('orientation=square', solicitud.full_url)
        self.assertIn('locale=es-ES', solicitud.full_url)
        self.assertEqual(resultado['fotos'][0]['fotografo'], 'Killa Foto')

    def test_detalle_indica_favorita_del_usuario_actual(self):
        usuario = User.objects.create_user('killa', password='contrasena-segura-123')
        PalabraFavorita.objects.create(usuario=usuario, palabra=self.palabra)
        self.client.force_login(usuario)
        respuesta = self.client.get(self.palabra.get_absolute_url())
        self.assertTrue(respuesta.context['es_favorita'])
        self.assertTrue(ActividadUsuario.objects.filter(usuario=usuario, tipo='palabra', palabra=self.palabra).exists())

    def test_favoritas_tienen_diseno_actual_y_quitar_exige_post(self):
        usuario = User.objects.create_user('inti', password='contrasena-segura-123')
        PalabraFavorita.objects.create(usuario=usuario, palabra=self.palabra)
        self.client.force_login(usuario)
        pagina = self.client.get(reverse('diccionario:mis_favoritas'))
        self.assertContains(pagina, 'Palabras que guardaste')
        self.assertContains(pagina, self.palabra.palabra_kichwa)
        self.assertContains(pagina, 'style="--favorite-accent: #007bff"')
        quitar = reverse('diccionario:quitar_favorita', args=[self.palabra.pk])
        self.assertEqual(self.client.get(quitar).status_code, 405)
        self.assertRedirects(self.client.post(quitar), reverse('diccionario:mis_favoritas'))
        self.assertFalse(PalabraFavorita.objects.filter(usuario=usuario, palabra=self.palabra).exists())

    def test_relaciones_semanticas_no_rellenan_solo_por_categoria(self):
        tiempo = Categoria.objects.create(nombre='Tiempo')
        cuando = Palabra.objects.create(
            palabra_kichwa='¿hayka?', traduccion_espanol='¿cuándo?',
            definicion='Interrogativo de tiempo', categoria=tiempo,
        )
        equivalente = Palabra.objects.create(
            palabra_kichwa='hayka', traduccion_espanol='cuándo',
            definicion='Pregunta por el momento de un evento', categoria=self.categoria,
        )
        ahora = Palabra.objects.create(
            palabra_kichwa='kunan', traduccion_espanol='ahora',
            definicion='Momento presente', categoria=tiempo,
        )
        noviembre = Palabra.objects.create(
            palabra_kichwa='ayar', traduccion_espanol='noviembre',
            definicion='Undécimo mes del año', categoria=tiempo,
        )

        relacionadas = obtener_palabras_relacionadas(cuando)
        ids = [item.palabra.pk for item in relacionadas]
        self.assertIn(equivalente.pk, ids)
        self.assertIn(ahora.pk, ids)
        self.assertNotIn(noviembre.pk, ids)

    def test_relacion_editorial_tiene_prioridad(self):
        destino = Palabra.objects.create(
            palabra_kichwa='yakumama', traduccion_espanol='madre del agua', categoria=self.categoria,
        )
        RelacionPalabra.objects.create(
            origen=self.palabra, destino=destino, tipo='contexto', nota='Concepto cultural asociado',
        )
        primera = obtener_palabras_relacionadas(self.palabra)[0]
        self.assertEqual(primera.palabra, destino)
        self.assertEqual(primera.motivo, 'Concepto cultural asociado')
        self.assertEqual(primera.tipo, 'curada')

    def test_audio_rechaza_extension_invalida(self):
        self.palabra.audio = SimpleUploadedFile('yaku.txt', b'x')
        with self.assertRaises(ValidationError):
            self.palabra.full_clean()

    def test_categoria_con_palabras_no_se_elimina(self):
        with self.assertRaises(ProtectedError):
            self.categoria.delete()

    def test_estadistica_exige_sesion_y_csrf(self):
        url = reverse('diccionario:guardar_estadistica_juego')
        respuesta = self.client.post(url, data=json.dumps({'tipo_juego': 'traduccion'}), content_type='application/json')
        self.assertEqual(respuesta.status_code, 401)
        usuario = User.objects.create_user('chaska', password='contrasena-segura-123')
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(usuario)
        respuesta = cliente.post(url, data=json.dumps({'tipo_juego': 'traduccion'}), content_type='application/json')
        self.assertEqual(respuesta.status_code, 403)

    def test_api_publica_no_expone_administracion(self):
        respuesta = self.client.get(reverse('diccionario:api_palabras'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn('definicion', respuesta.json()['resultados'][0])

    def test_busqueda_prioriza_coincidencia_exacta_y_aplica_filtros(self):
        respuesta = self.client.get(reverse('diccionario:buscar'), {'termino': 'Yaku'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['page_obj'].object_list[0].pk, self.palabra.pk)

        respuesta = self.client.get(
            reverse('diccionario:buscar'),
            {'termino': 'agua', 'categoria': self.categoria.pk, 'dificultad': 'medio'},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['total_resultados'], 3)

    def test_busqueda_bilingue_combina_categoria_y_dificultad_pronunciacion(self):
        respuesta = self.client.get(
            reverse('diccionario:buscar'),
            {'termino': 'gato', 'categoria': self.animales.pk, 'dificultad': 'medio'},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(list(respuesta.context['page_obj'].object_list), [self.misi])

        respuesta = self.client.get(
            reverse('diccionario:buscar'),
            {'categoria': self.animales.pk, 'dificultad': 'dificil'},
        )
        self.assertEqual(respuesta.context['total_resultados'], 0)

    def test_busqueda_ignora_tildes_y_funciona_en_ambos_idiomas(self):
        maiz = Palabra.objects.create(
            palabra_kichwa='Sara',
            traduccion_espanol='Maíz',
            categoria=self.categoria,
        )
        respuesta = self.client.get(reverse('diccionario:buscar'), {'termino': 'maiz'})
        self.assertIn(maiz, respuesta.context['page_obj'].object_list)

        respuesta = self.client.get(reverse('diccionario:buscar'), {'termino': 'sara'})
        self.assertIn(maiz, respuesta.context['page_obj'].object_list)

    def test_clasificacion_evitar_subcadenas_y_asigna_temas_logicos(self):
        self.assertEqual(
            clasificar_textos('wasi', 'casa', 'Lugar o construcción').categoria,
            'Hogar y construcción',
        )
        self.assertEqual(
            clasificar_textos('misi', 'gato', 'Animal doméstico felino').categoria,
            'Animales',
        )
        resultado = clasificar_textos('killkana pata', 'escritorio', 'Mueble para escribir')
        self.assertEqual(resultado.categoria, 'Hogar y construcción')
        self.assertNotEqual(resultado.categoria, 'Territorio y lugares')

    def test_dificultad_pronunciacion_aumenta_con_complejidad(self):
        facil = calcular_dificultad_pronunciacion('misi')
        dificil = calcular_dificultad_pronunciacion('hatun-shimikunawan; rimay')
        self.assertEqual(facil[0], 'facil')
        self.assertEqual(dificil[0], 'dificil')
        self.assertGreater(dificil[2], facil[2])

    def test_busqueda_con_filtro_invalido_no_devuelve_error_500(self):
        respuesta = self.client.get(
            reverse('diccionario:buscar'), {'termino': 'Yaku', 'categoria': 'no-existe'}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['total_resultados'], 2)

    def test_sugerencias_consultan_el_corpus_y_respetan_relevancia(self):
        respuesta = self.client.get(reverse('diccionario:obtener_sugerencias_ajax'), {'q': 'Yaku'})
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(datos['palabras'][0]['id'], self.palabra.pk)
        self.assertNotIn('Mama', [item['palabra_kichwa'] for item in datos['palabras']])

    def test_busqueda_rapida_exige_dos_caracteres(self):
        respuesta = self.client.get(reverse('diccionario:buscar_palabras_ajax'), {'q': 'y'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {'palabras': [], 'total': 0})

    def test_api_usa_el_mismo_orden_de_relevancia(self):
        respuesta = self.client.get(reverse('diccionario:api_palabras'), {'q': 'Yaku'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['resultados'][0]['id'], self.palabra.pk)

    def test_favorita_solo_admite_post(self):
        url = reverse('diccionario:toggle_favorita_ajax', args=[self.palabra.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertTrue(self.client.post(url).json()['login_required'])

    def test_paginas_principales_y_juegos_responden(self):
        rutas = [
            'home', 'buscar', 'categorias', 'acerca_de', 'contacto', 'juegos',
            'juego_traduccion', 'juego_completar', 'juego_memoria', 'juego_conexion',
            'juego_sopa_letras', 'juego_escucha',
        ]
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(f'diccionario:{ruta}')).status_code, 200)

    def test_juegos_usan_el_corpus_y_no_filtran_la_respuesta_como_pista(self):
        filtros = {'categoria': self.animales.slug, 'dificultad': 'medio'}
        traduccion = self.client.get(reverse('diccionario:juego_traduccion'), filtros)
        datos_traduccion = json.loads(traduccion.context['palabras_json'])
        self.assertEqual(datos_traduccion[0]['palabra_kichwa'], 'Misi')
        self.assertEqual(datos_traduccion[0]['descripcion_juego_espanol'], '')

        conexion = self.client.get(reverse('diccionario:juego_conexion'), filtros)
        self.assertEqual(conexion.context['palabras'][0], self.misi)
        self.assertNotContains(conexion, 'Pukllay')

        sopa = self.client.get(reverse('diccionario:juego_sopa_letras'), filtros)
        palabra_sopa = sopa.context['palabras'][0]
        self.assertEqual(palabra_sopa.palabra_tablero, 'MISI')
        self.assertContains(sopa, 'horizontal, vertical o diagonal')
        self.assertContains(sopa, 'id="game-exit-prompt"')
        self.assertContains(sopa, 'id="game-sound-toggle"')

        portada = self.client.get(reverse('diccionario:juegos'))
        for tipo in ('traduccion', 'escucha', 'conectar', 'memoria', 'completar', 'sopa_letras'):
            self.assertContains(portada, f'learning-path__item--{tipo}')

    def test_escucha_usa_solo_grabaciones_y_guarda_aciertos_por_palabra(self):
        self.misi.audio = 'audios/misi.mp3'
        self.misi.save(update_fields=['audio'])
        filtros = {'categoria': self.animales.slug, 'dificultad': 'medio'}
        usuario = User.objects.create_user('escucha', password='contrasena-segura-123')
        self.client.force_login(usuario)

        pagina = self.client.get(reverse('diccionario:juego_escucha'), filtros)
        self.assertEqual(pagina.status_code, 200)
        self.assertEqual(pagina.context['palabras'], [self.misi])
        self.assertEqual(pagina.context['palabras_data'][0]['audio'], self.misi.audio.url)
        self.assertEqual(pagina.context['tipo_juego'], 'escucha')
        self.assertEqual(list(pagina.context['categorias_jugables']), [self.animales])
        self.assertNotContains(pagina, 'No hay grabaciones con estos filtros')
        self.assertContains(pagina, 'Escucha grabaciones del corpus')
        datos_api = self.client.get(reverse('diccionario:obtener_palabras_juego'), {
            'tipo': 'escucha', 'dificultad': 'medio', 'categoria': self.animales.slug,
        }).json()['palabras']
        self.assertEqual([item['id'] for item in datos_api], [self.misi.pk])
        self.assertEqual(datos_api[0]['audio'], self.misi.audio.url)

        respuesta = self.client.post(reverse('diccionario:registrar_respuesta_juego'), data=json.dumps({
            'sesion_id': pagina.context['sesion_id'], 'tipo_juego': 'escucha',
            'palabra_id': self.misi.pk, 'respuesta_id': self.misi.pk,
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()['correcta'])
        self.assertEqual(respuesta.json()['puntos_ganados'], 10)
        self.assertEqual(ProgresoPalabraJuego.objects.get(usuario=usuario, palabra=self.misi).respuestas_correctas, 1)
        cierre = self.client.post(reverse('diccionario:guardar_estadistica_juego'), data=json.dumps({
            'sesion_id': pagina.context['sesion_id'],
        }), content_type='application/json')
        self.assertEqual(cierre.status_code, 201)
        self.assertEqual(EstadisticaJuego.objects.get(usuario=usuario).tipo_juego, 'escucha')

        vacia = self.client.get(reverse('diccionario:juego_escucha'), {
            'categoria': self.categoria.slug, 'dificultad': 'medio',
        })
        self.assertEqual(vacia.context['palabras'], [])
        self.assertContains(vacia, 'No hay grabaciones con estos filtros')

    def test_filtros_de_juego_no_se_rellenan_con_otro_tema_o_dificultad(self):
        alimentos = Categoria.objects.create(nombre='Alimentos')
        Palabra.objects.create(
            palabra_kichwa='Papa', traduccion_espanol='Papa', categoria=alimentos,
            apta_para_juegos=True, dificultad='facil', dificultad_juego='facil',
        )
        respuesta = self.client.get(reverse('diccionario:juego_conexion'), {
            'categoria': self.animales.slug,
            'dificultad': 'facil',
        })
        self.assertEqual(respuesta.context['palabras'], [])
        self.assertContains(respuesta, 'No hay palabras disponibles con estos filtros')

    def test_tema_y_dificultad_se_aplican_en_todas_las_modalidades(self):
        self.misi.audio = 'audios/misi.mp3'
        self.misi.save(update_fields=['audio'])
        Palabra.objects.create(
            palabra_kichwa='Allku', traduccion_espanol='Perro', categoria=self.animales,
            apta_para_juegos=True, dificultad='facil', dificultad_juego='facil',
        )
        Palabra.objects.create(
            palabra_kichwa='Tanta', traduccion_espanol='Pan', categoria=self.categoria,
            apta_para_juegos=True, dificultad='medio', dificultad_juego='medio',
        )
        filtros = {'categoria': self.animales.slug, 'dificultad': 'medio'}
        for ruta in ('juego_traduccion', 'juego_escucha', 'juego_conexion', 'juego_memoria', 'juego_completar', 'juego_sopa_letras'):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(reverse(f'diccionario:{ruta}'), filtros)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.context['palabras'], [self.misi])
                self.assertEqual(respuesta.context['categoria_seleccionada'], self.animales.slug)
                self.assertEqual(respuesta.context['dificultad'], 'medio')

    def test_entradas_generales_claras_se_juegan_segun_su_dificultad(self):
        facil = Palabra.objects.create(
            palabra_kichwa='Allku', traduccion_espanol='Perro',
            categoria=self.animales, dificultad='facil', apta_para_juegos=False,
        )
        dificil = Palabra.objects.create(
            palabra_kichwa='Mishkichuspi', traduccion_espanol='Abeja',
            categoria=self.animales, dificultad='dificil', apta_para_juegos=False,
        )
        Palabra.objects.create(
            palabra_kichwa='Misi, allku', traduccion_espanol='Gato, perro',
            categoria=self.animales, dificultad='dificil', apta_para_juegos=False,
        )
        url = reverse('diccionario:juego_traduccion')
        faciles = self.client.get(url, {'dificultad': 'facil', 'categoria': self.animales.slug})
        dificiles = self.client.get(url, {'dificultad': 'dificil', 'categoria': self.animales.slug})
        self.assertEqual(faciles.context['palabras'], [facil])
        self.assertEqual(dificiles.context['palabras'], [dificil])
        self.assertEqual(dificiles.context['pistas_base'], 1)
        self.assertIn(self.animales, list(dificiles.context['categorias_jugables']))

        respuesta = self.client.post(reverse('diccionario:registrar_respuesta_juego'), data=json.dumps({
            'sesion_id': dificiles.context['sesion_id'], 'tipo_juego': 'traduccion',
            'palabra_id': dificil.pk, 'respuesta_id': dificil.pk,
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()['correcta'])

    def test_presupuesto_de_pistas_depende_de_dificultad_y_exige_cuenta_para_extras(self):
        palabras = [Palabra.objects.create(
            palabra_kichwa=f'Rimay{i}', traduccion_espanol=f'Palabra {i}',
            categoria=self.animales, apta_para_juegos=True, dificultad='dificil', dificultad_juego='dificil',
        ) for i in range(3)]
        for dificultad, limite in (('facil', 3), ('medio', 2), ('dificil', 1)):
            with self.subTest(dificultad=dificultad):
                pagina = self.client.get(reverse('diccionario:juego_traduccion'), {'dificultad': dificultad})
                self.assertEqual(pagina.context['pistas_base'], limite)

        pagina = self.client.get(reverse('diccionario:juego_traduccion'), {'dificultad': 'dificil'})
        sesion_id = pagina.context['sesion_id']
        url = reverse('diccionario:usar_pista_juego')
        def usar(palabra_id):
            return self.client.post(url, data=json.dumps({
                'sesion_id': sesion_id, 'palabra_id': palabra_id,
            }), content_type='application/json')

        primera = usar(palabras[0].pk)
        self.assertEqual(primera.status_code, 200)
        self.assertEqual(primera.json()['pistas_base_restantes'], 0)
        self.assertEqual(usar(palabras[0].pk).status_code, 409)
        segunda = usar(palabras[1].pk)
        self.assertEqual(segunda.status_code, 403)
        self.assertTrue(segunda.json()['login_required'])
        self.assertEqual(SesionJuego.objects.get(id=sesion_id).pistas_usadas, 1)

    def test_dos_pistas_extra_se_gastan_una_sola_vez_por_cuenta(self):
        usuario = User.objects.create_user('pukllay', password='Clave-segura-123')
        palabras = [Palabra.objects.create(
            palabra_kichwa=f'Yachay{i}', traduccion_espanol=f'Aprender {i}',
            categoria=self.animales, apta_para_juegos=True, dificultad='dificil', dificultad_juego='dificil',
        ) for i in range(4)]
        self.client.force_login(usuario)
        url = reverse('diccionario:usar_pista_juego')
        def abrir_partida():
            return self.client.get(reverse('diccionario:juego_memoria'), {'dificultad': 'dificil'}).context['sesion_id']
        def usar(sesion_id, palabra_id):
            return self.client.post(url, data=json.dumps({
                'sesion_id': sesion_id, 'palabra_id': palabra_id,
            }), content_type='application/json')

        sesion_id = abrir_partida()
        resultados = [usar(sesion_id, palabra.pk) for palabra in palabras]
        self.assertEqual([respuesta.status_code for respuesta in resultados], [200, 200, 200, 403])
        self.assertEqual([respuesta.json()['origen'] for respuesta in resultados[:3]], ['partida', 'extra', 'extra'])
        self.assertEqual(resultados[2].json()['pistas_extra_restantes'], 0)
        usuario.perfil.refresh_from_db()
        self.assertEqual(usuario.perfil.pistas_extra_disponibles, 0)

        self.client.logout()
        self.client.force_login(usuario)
        nueva_sesion = abrir_partida()
        self.assertEqual(usar(nueva_sesion, palabras[0].pk).status_code, 200)
        self.assertEqual(usar(nueva_sesion, palabras[1].pk).status_code, 403)
        usuario.perfil.refresh_from_db()
        self.assertEqual(usuario.perfil.pistas_extra_disponibles, 0)

    def test_pista_rechaza_sesion_ajena_palabra_ajena_y_sesion_finalizada(self):
        usuario = User.objects.create_user('urku', password='Clave-segura-123')
        otra = User.objects.create_user('sisa', password='Clave-segura-123')
        self.client.force_login(usuario)
        pagina = self.client.get(reverse('diccionario:juego_completar'), {
            'dificultad': 'medio', 'categoria': self.animales.slug,
        })
        sesion = SesionJuego.objects.get(id=pagina.context['sesion_id'])
        url = reverse('diccionario:usar_pista_juego')
        datos = {'sesion_id': str(sesion.id), 'palabra_id': self.misi.pk}
        self.assertEqual(self.client.post(url, data=json.dumps({**datos, 'palabra_id': self.palabra.pk}), content_type='application/json').status_code, 403)
        self.client.force_login(otra)
        self.assertEqual(self.client.post(url, data=json.dumps(datos), content_type='application/json').status_code, 403)
        self.client.force_login(usuario)
        sesion.finalizada_en = timezone.now()
        sesion.save(update_fields=['finalizada_en'])
        self.assertEqual(self.client.post(url, data=json.dumps(datos), content_type='application/json').status_code, 409)

    def test_respuesta_se_valida_en_servidor_y_actualiza_progreso(self):
        usuario = User.objects.create_user('inti', password='contrasena-segura-123')
        self.client.force_login(usuario)
        url = reverse('diccionario:registrar_respuesta_juego')
        juego = self.client.get(reverse('diccionario:juego_completar'), {'dificultad': 'medio'})
        sesion_id = juego.context['sesion_id']

        incorrecta = self.client.post(url, data=json.dumps({
            'sesion_id': sesion_id, 'tipo_juego': 'completar', 'palabra_id': self.misi.pk, 'respuesta': 'allku',
        }), content_type='application/json')
        correcta = self.client.post(url, data=json.dumps({
            'sesion_id': sesion_id, 'tipo_juego': 'completar', 'palabra_id': self.misi.pk, 'respuesta': 'mísí',
        }), content_type='application/json')

        self.assertFalse(incorrecta.json()['correcta'])
        self.assertTrue(correcta.json()['correcta'])
        progreso = ProgresoPalabraJuego.objects.get(usuario=usuario, palabra=self.misi)
        self.assertEqual(progreso.intentos, 2)
        self.assertEqual(progreso.respuestas_correctas, 1)
        self.assertEqual(progreso.dominio, 'aprendiendo')
        self.assertEqual(IntentoPalabraJuego.objects.filter(sesion_id=sesion_id).count(), 2)

    def test_sesion_rechaza_palabra_ajena_y_resultado_inventado(self):
        usuario = User.objects.create_user('sisa', password='contrasena-segura-123')
        ajena = Palabra.objects.create(
            palabra_kichwa='Tanta', traduccion_espanol='Pan', categoria=self.categoria,
            apta_para_juegos=True, dificultad='facil', dificultad_juego='facil',
        )
        self.client.force_login(usuario)
        juego = self.client.get(reverse('diccionario:juego_traduccion'), {
            'categoria': self.animales.slug, 'dificultad': 'medio',
        })
        sesion_id = juego.context['sesion_id']
        respuesta_url = reverse('diccionario:registrar_respuesta_juego')
        rechazada = self.client.post(respuesta_url, data=json.dumps({
            'sesion_id': sesion_id, 'tipo_juego': 'traduccion',
            'palabra_id': ajena.pk, 'respuesta_id': ajena.pk,
        }), content_type='application/json')
        self.assertEqual(rechazada.status_code, 403)

        validada = self.client.post(respuesta_url, data=json.dumps({
            'sesion_id': sesion_id, 'tipo_juego': 'traduccion',
            'palabra_id': self.misi.pk, 'respuesta_id': self.misi.pk,
        }), content_type='application/json')
        self.assertTrue(validada.json()['correcta'])
        cierre = self.client.post(reverse('diccionario:guardar_estadistica_juego'), data=json.dumps({
            'sesion_id': sesion_id, 'puntuacion': 999999, 'respuestas_correctas': 999,
        }), content_type='application/json')
        self.assertEqual(cierre.status_code, 201)
        estadistica = EstadisticaJuego.objects.get(usuario=usuario)
        self.assertEqual(estadistica.puntuacion, 10)
        self.assertEqual(estadistica.respuestas_correctas, 1)
        self.assertEqual(estadistica.respuestas_totales, 1)
        self.assertEqual(SesionJuego.objects.get(id=sesion_id).estadistica, estadistica)
        self.assertTrue(ActividadUsuario.objects.filter(usuario=usuario, tipo='juego', estadistica=estadistica).exists())

    def test_primer_acierto_suma_puntos_una_sola_vez_por_palabra(self):
        usuario = User.objects.create_user('urku', password='clave-segura-123')
        self.client.force_login(usuario)
        respuesta_url = reverse('diccionario:registrar_respuesta_juego')
        for _ in range(2):
            juego = self.client.get(reverse('diccionario:juego_completar'), {
                'categoria': self.animales.slug, 'dificultad': 'medio',
            })
            respuesta = self.client.post(respuesta_url, data=json.dumps({
                'sesion_id': juego.context['sesion_id'], 'tipo_juego': 'completar',
                'palabra_id': self.misi.pk, 'respuesta': 'Misi',
            }), content_type='application/json')
            self.assertEqual(respuesta.status_code, 200)
            self.assertEqual(respuesta.json()['puntos_ganados'], 10 if _ == 0 else 0)
        perfil = PerfilUsuario.objects.get(usuario=usuario)
        self.assertEqual(perfil.puntos_totales, 10)

    def test_seleccion_prioriza_palabras_nuevas_sobre_dominadas(self):
        usuario = User.objects.create_user('killa', password='contrasena-segura-123')
        nueva = Palabra.objects.create(
            palabra_kichwa='Allku', traduccion_espanol='Perro', categoria=self.animales,
            apta_para_juegos=True, dificultad_juego='medio',
        )
        ProgresoPalabraJuego.objects.create(
            usuario=usuario, palabra=self.misi, intentos=8, respuestas_correctas=8,
            racha_actual=8, mejor_racha=8, dominio='dominada',
        )
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse('diccionario:juego_traduccion'), {
            'categoria': self.animales.slug, 'dificultad': 'medio',
        })
        self.assertEqual(respuesta.context['palabras'][0], nueva)

    def test_inicio_usa_palabras_destacadas_reales_y_api_de_sugerencias(self):
        respuesta = self.client.get(reverse('diccionario:home'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, self.palabra.get_absolute_url())
        self.assertContains(respuesta, reverse('diccionario:obtener_sugerencias_ajax'))
        self.assertContains(respuesta, 'data-tooltip="Escribe una palabra completa')

        busqueda = self.client.get(reverse('diccionario:buscar'))
        self.assertContains(busqueda, 'data-tooltip="Limita los resultados a un tema')

    def test_auditoria_no_modifica_datos(self):
        salida = StringIO()
        call_command('auditar_diccionario', '--json', stdout=salida)
        reporte = json.loads(salida.getvalue())
        self.assertEqual(reporte['palabras']['total'], 4)
        self.assertEqual(reporte['palabras']['jugables_actuales'], 4)
        self.assertEqual(reporte['palabras']['jugables_generales_sin_marca'], 3)
        self.assertEqual(Palabra.objects.count(), 4)

    @override_settings(KICHWA_AI_PROVIDER='none')
    def test_ia_esta_desactivada_por_defecto(self):
        self.assertIsNone(obtener_configuracion_ia())
