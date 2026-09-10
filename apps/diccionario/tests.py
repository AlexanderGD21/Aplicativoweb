import json
from io import StringIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Categoria, EstadisticaJuego, HistorialBusqueda, Palabra, RelacionPalabra
from .models import PalabraFavorita
from .services.clasificacion import (
    calcular_dificultad_pronunciacion,
    clasificar_textos,
)
from .services.ia_kichwa import obtener_configuracion_ia
from .services.relaciones import obtener_palabras_relacionadas


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
            nivel_dificultad='intermedio', dificultad='facil', apta_para_juegos=True,
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

    def test_detalle_incrementa_vistas(self):
        self.client.get(self.palabra.get_absolute_url())
        self.palabra.refresh_from_db()
        self.assertEqual(self.palabra.veces_vista, 1)

    def test_detalle_indica_favorita_del_usuario_actual(self):
        usuario = User.objects.create_user('killa', password='contrasena-segura-123')
        PalabraFavorita.objects.create(usuario=usuario, palabra=self.palabra)
        self.client.force_login(usuario)
        respuesta = self.client.get(self.palabra.get_absolute_url())
        self.assertTrue(respuesta.context['es_favorita'])

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
            {'termino': 'gato', 'categoria': self.animales.pk, 'dificultad': 'facil'},
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
            'juego_sopa_letras',
        ]
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(f'diccionario:{ruta}')).status_code, 200)

    def test_juegos_usan_el_corpus_y_no_filtran_la_respuesta_como_pista(self):
        traduccion = self.client.get(reverse('diccionario:juego_traduccion'))
        datos_traduccion = json.loads(traduccion.context['palabras_json'])
        self.assertEqual(datos_traduccion[0]['palabra_kichwa'], 'Misi')
        self.assertEqual(datos_traduccion[0]['descripcion_juego_espanol'], '')

        conexion = self.client.get(reverse('diccionario:juego_conexion'))
        self.assertContains(conexion, f'id: {self.misi.pk}')
        self.assertNotContains(conexion, 'id: 35, kichwa: "Pukllay"')

        sopa = self.client.get(reverse('diccionario:juego_sopa_letras'))
        palabra_sopa = sopa.context['palabras'][0]
        self.assertEqual(palabra_sopa.palabra_tablero, 'MISI')

    def test_inicio_usa_palabras_destacadas_reales_y_api_de_sugerencias(self):
        respuesta = self.client.get(reverse('diccionario:home'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, self.palabra.get_absolute_url())
        self.assertContains(respuesta, reverse('diccionario:obtener_sugerencias_ajax'))

    def test_auditoria_no_modifica_datos(self):
        salida = StringIO()
        call_command('auditar_diccionario', '--json', stdout=salida)
        self.assertIn('"total": 4', salida.getvalue())
        self.assertEqual(Palabra.objects.count(), 4)

    @override_settings(KICHWA_AI_PROVIDER='none')
    def test_ia_esta_desactivada_por_defecto(self):
        self.assertIsNone(obtener_configuracion_ia())
