import json
from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    ActividadUsuario, BusquedaPopularDiaria, Categoria, EstadisticaJuego, HistorialBusqueda, IntentoPalabraJuego, Palabra,
    ProgresoPalabraJuego, RelacionPalabra, SesionJuego,
)
from .models import PalabraFavorita
from apps.usuarios.models import PerfilUsuario
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
            'juego_sopa_letras',
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
        for tipo in ('traduccion', 'conectar', 'memoria', 'completar', 'sopa_letras'):
            self.assertContains(portada, f'learning-path__item--{tipo}')

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
        Palabra.objects.create(
            palabra_kichwa='Allku', traduccion_espanol='Perro', categoria=self.animales,
            apta_para_juegos=True, dificultad='facil', dificultad_juego='facil',
        )
        Palabra.objects.create(
            palabra_kichwa='Tanta', traduccion_espanol='Pan', categoria=self.categoria,
            apta_para_juegos=True, dificultad='medio', dificultad_juego='medio',
        )
        filtros = {'categoria': self.animales.slug, 'dificultad': 'medio'}
        for ruta in ('juego_traduccion', 'juego_conexion', 'juego_memoria', 'juego_completar', 'juego_sopa_letras'):
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
