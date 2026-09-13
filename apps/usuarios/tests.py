from django.contrib.auth.models import User
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.diccionario.models import ActividadUsuario, Categoria, EstadisticaJuego, Palabra, PalabraFavorita

from .forms import PerfilUsuarioForm, RegistroForm, UserForm
from .models import PerfilUsuario


class RecuperacionContrasenaTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_paginas_de_recuperacion_existen(self):
        for ruta in ('password_reset', 'password_reset_done', 'password_reset_complete'):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(f'usuarios:{ruta}')).status_code, 200)

        respuesta = self.client.get(
            reverse('usuarios:password_reset_confirm', args=['invalido', 'invalido'])
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Enlace no válido')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_solicitud_envia_enlace_con_ruta_del_proyecto(self):
        User.objects.create_user('maki', email='maki@example.test', password='clave-segura-123')
        respuesta = self.client.post(
            reverse('usuarios:password_reset'), {'email': 'maki@example.test'}
        )
        self.assertRedirects(respuesta, reverse('usuarios:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/usuarios/reset/', mail.outbox[0].body)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        PASSWORD_RESET_MAX_REQUESTS=1,
    )
    def test_recuperacion_limita_solicitudes_sin_revelar_la_cuenta(self):
        User.objects.create_user('mashi', email='mashi@example.test', password='Clave-segura-123')
        url = reverse('usuarios:password_reset')

        self.assertRedirects(self.client.post(url, {'email': 'mashi@example.test'}), reverse('usuarios:password_reset_done'))
        self.assertRedirects(self.client.post(url, {'email': 'mashi@example.test'}), reverse('usuarios:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)


class PerfilYProgresoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('sisa', password='clave-segura-123')
        self.client.force_login(self.usuario)

    def test_perfil_y_progreso_usan_la_relacion_correcta(self):
        self.assertTrue(PerfilUsuario.objects.filter(usuario=self.usuario).exists())
        respuesta = self.client.get(reverse('usuarios:perfil'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, '<strong>2</strong> de 2 disponibles', html=True)
        self.assertContains(respuesta, 'Actividad reciente')

    def test_perfil_publico_respeta_privacidad_de_progreso_y_ranking(self):
        perfil = self.usuario.perfil
        perfil.perfil_publico = True
        perfil.puntos_totales = 37
        perfil.save()
        self.client.logout()
        ruta = reverse('usuarios:perfil_usuario', args=[self.usuario.username])

        respuesta = self.client.get(ruta)
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, 'puntos compartidos en el ranking')
        self.assertNotContains(respuesta, 'Pistas extra')
        self.assertNotContains(respuesta, 'Actividad reciente')

        perfil.participa_ranking = True
        perfil.save(update_fields=['participa_ranking'])
        self.assertContains(self.client.get(ruta), '<strong>37</strong> puntos compartidos en el ranking', html=True)

        perfil.perfil_publico = False
        perfil.save(update_fields=['perfil_publico'])
        self.assertEqual(self.client.get(ruta).status_code, 404)

    def test_perfil_propio_exige_sesion(self):
        self.client.logout()
        respuesta = self.client.get(reverse('usuarios:perfil'))
        self.assertRedirects(respuesta, f"{reverse('usuarios:login')}?next={reverse('usuarios:perfil')}")

    def test_participacion_en_ranking_es_independiente_y_desactivada_por_defecto(self):
        perfil = self.usuario.perfil
        self.assertFalse(perfil.participa_ranking)
        self.assertFalse(perfil.perfil_publico)
        formulario = PerfilUsuarioForm({
            'participa_ranking': 'on', 'nivel_kichwa': 'principiante',
        }, instance=perfil)
        self.assertTrue(formulario.is_valid(), formulario.errors)
        formulario.save()
        perfil.refresh_from_db()
        self.assertTrue(perfil.participa_ranking)
        self.assertFalse(perfil.perfil_publico)

    def test_cambio_de_correo_exige_la_contrasena_actual(self):
        self.usuario.email = 'sisa@example.test'
        self.usuario.first_name = 'Sisa'
        self.usuario.last_name = 'Yaku'
        self.usuario.save()
        datos = {
            'first_name': 'Sisa',
            'last_name': 'Yaku',
            'email': 'nuevo@example.test',
            'current_password': 'incorrecta',
        }
        form = UserForm(datos, instance=self.usuario)
        self.assertFalse(form.is_valid())
        self.assertIn('current_password', form.errors)

        datos['current_password'] = 'clave-segura-123'
        form = UserForm(datos, instance=self.usuario)
        self.assertTrue(form.is_valid())

    def test_el_correo_no_se_puede_vaciar(self):
        self.usuario.email = 'sisa@example.test'
        self.usuario.save(update_fields=['email'])
        form = UserForm({
            'first_name': 'Sisa',
            'last_name': 'Yaku',
            'email': '',
            'current_password': '',
        }, instance=self.usuario)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_telefono_exige_diez_digitos_y_fecha_no_futura(self):
        for telefono in ('2323jjmmm', '123456789', '12345678901', '+593987654321', '123 456 7890', ' 0987654321 '):
            with self.subTest(telefono=telefono):
                form = PerfilUsuarioForm({'telefono': telefono, 'nivel_kichwa': 'principiante'}, instance=self.usuario.perfil)
                self.assertFalse(form.is_valid())
                self.assertIn('telefono', form.errors)
        form = PerfilUsuarioForm({'telefono': '0987654321', 'nivel_kichwa': 'principiante'}, instance=self.usuario.perfil)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['telefono'], '0987654321')
        manana = timezone.localdate() + timedelta(days=1)
        form = PerfilUsuarioForm({'fecha_nacimiento': manana.isoformat(), 'nivel_kichwa': 'principiante'}, instance=self.usuario.perfil)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_nacimiento', form.errors)

    def test_edad_y_calendario_se_muestran_en_edicion(self):
        hoy = timezone.localdate()
        self.usuario.perfil.fecha_nacimiento = hoy.replace(year=hoy.year - 20)
        self.usuario.perfil.save(update_fields=['fecha_nacimiento'])
        respuesta = self.client.get(reverse('usuarios:editar_perfil'))
        self.assertContains(respuesta, 'Edad actual: 20 años')
        self.assertContains(respuesta, 'type="date"')
        self.assertContains(respuesta, 'inputmode="numeric"')

    def test_cambiar_contrasena_exige_actual_y_confirmacion_y_mantiene_sesion(self):
        url = reverse('usuarios:cambiar_contrasena')
        self.assertContains(self.client.get(url), 'Contraseña actual')
        datos = {'old_password': 'incorrecta', 'new_password1': 'Otra-clave-segura-123', 'new_password2': 'Otra-clave-segura-123'}
        self.assertContains(self.client.post(url, datos), 'contraseña actual')
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('clave-segura-123'))
        datos['old_password'] = 'clave-segura-123'
        datos['new_password2'] = 'Clave-distinta-123'
        self.assertContains(self.client.post(url, datos), 'no coinciden')
        datos['new_password2'] = datos['new_password1']
        self.assertRedirects(self.client.post(url, datos), reverse('usuarios:perfil'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Otra-clave-segura-123'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.usuario.pk)

    def test_historial_y_estadisticas_son_privados_y_tienen_fecha_hora(self):
        categoria = Categoria.objects.create(nombre='Naturaleza')
        palabra = Palabra.objects.create(palabra_kichwa='Yaku', traduccion_espanol='Agua', categoria=categoria)
        self.client.get(reverse('diccionario:buscar'), {'termino': 'Yaku'})
        self.client.get(palabra.get_absolute_url())
        estadistica = EstadisticaJuego.objects.create(
            usuario=self.usuario, tipo_juego='traduccion', puntuacion=10,
            respuestas_correctas=1, respuestas_totales=1, tiempo_jugado=120,
        )
        ActividadUsuario.objects.create(usuario=self.usuario, tipo='juego', estadistica=estadistica)
        respuesta = self.client.get(reverse('usuarios:mi_actividad'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['total_actividad'], 3)
        self.assertContains(respuesta, 'Yaku')
        self.assertContains(respuesta, '2</strong><span>Minutos de juego', html=False)
        self.assertContains(respuesta, 'datetime="')
        self.assertEqual(self.client.get(reverse('usuarios:mi_actividad'), {'tipo': 'juego'}).context['pagina'].paginator.count, 1)

        otro = User.objects.create_user('ajeno', password='clave-segura-123')
        self.client.force_login(otro)
        self.assertNotContains(self.client.get(reverse('usuarios:mi_actividad')), 'Yaku')
        self.client.logout()
        self.assertEqual(self.client.get(reverse('usuarios:mi_actividad')).status_code, 302)


class RegistroYSesionTests(TestCase):
    def setUp(self):
        cache.clear()

    def _datos_registro(self, **cambios):
        datos = {
            'username': 'killa',
            'first_name': 'Killa',
            'last_name': 'Yaku',
            'email': 'killa@example.test',
            'password1': 'Clave-segura-123',
            'password2': 'Clave-segura-123',
            'acepto_terminos': 'on',
        }
        datos.update(cambios)
        return datos

    def test_acceso_y_registro_ofrecen_ayuda_contextual(self):
        acceso = self.client.get(reverse('usuarios:login'))
        self.assertContains(acceso, 'data-tooltip="Mostrar u ocultar la contraseña escrita')
        self.assertContains(acceso, 'data-tooltip="Puedes usar tu nombre de usuario')

        registro = self.client.get(reverse('usuarios:registro'))
        self.assertContains(registro, 'data-tooltip="Elige el nombre con el que iniciarás sesión')
        self.assertContains(registro, 'data-tooltip="Validar los datos y crear tu cuenta')
        self.assertContains(registro, 'id="first-name-help">Solo letras y espacios.')
        self.assertContains(registro, 'id="last-name-help">Solo letras y espacios.')
        self.assertNotContains(registro, 'class="auth-brand"')

    def test_nombre_y_apellido_admiten_letras_y_espacios_sin_numeros_ni_simbolos(self):
        formulario = RegistroForm(self._datos_registro(
            first_name='Anthony21', last_name='Yaku@',
        ))
        self.assertFalse(formulario.is_valid())
        self.assertIn('first_name', formulario.errors)
        self.assertIn('last_name', formulario.errors)
        self.assertIn('solo puede contener letras y espacios', formulario.errors['first_name'][0])
        self.assertEqual(formulario.fields['first_name'].widget.attrs['aria-invalid'], 'true')
        respuesta = self.client.post(reverse('usuarios:registro'), self._datos_registro(
            first_name='Anthony21', last_name='Yaku@',
        ))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'El nombre solo puede contener letras y espacios.')
        self.assertFalse(User.objects.filter(username='killa').exists())

        formulario = RegistroForm(self._datos_registro(
            first_name='María José', last_name='Ñusta Chumbi',
        ))
        self.assertTrue(formulario.is_valid(), formulario.errors)

    def test_registro_exige_terminos_y_correo_unico(self):
        sin_terminos = self._datos_registro()
        sin_terminos.pop('acepto_terminos')
        respuesta = self.client.post(reverse('usuarios:registro'), sin_terminos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username='killa').exists())

        respuesta = self.client.post(reverse('usuarios:registro'), self._datos_registro())
        self.assertRedirects(respuesta, reverse('usuarios:login'))
        usuario = User.objects.get(email='killa@example.test')
        self.assertIsNotNone(usuario.perfil.terminos_aceptados_en)
        self.assertEqual(usuario.perfil.version_terminos, '2026-09-10')
        self.assertEqual(usuario.perfil.version_privacidad, settings.LEGAL_PRIVACY_VERSION)
        self.assertFalse(usuario.perfil.notificaciones_email)

        respuesta = self.client.post(
            reverse('usuarios:registro'), self._datos_registro(username='killa2')
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Ya existe una cuenta registrada con este correo.')

    def test_novedades_son_optativas(self):
        respuesta = self.client.post(
            reverse('usuarios:registro'),
            self._datos_registro(recibir_novedades='on'),
        )
        self.assertRedirects(respuesta, reverse('usuarios:login'))
        self.assertTrue(User.objects.get(username='killa').perfil.notificaciones_email)

    def test_registro_conserva_un_destino_interno_y_descarta_uno_externo(self):
        destino = reverse('diccionario:mis_favoritas')
        respuesta = self.client.post(
            reverse('usuarios:registro'),
            self._datos_registro(next=destino),
        )
        self.assertRedirects(
            respuesta,
            f"{reverse('usuarios:login')}?next={destino.replace('/', '%2F')}",
            fetch_redirect_response=False,
        )

        cache.clear()
        respuesta = self.client.post(
            reverse('usuarios:registro'),
            self._datos_registro(
                username='killa2',
                email='killa2@example.test',
                next='https://example.com/robo',
            ),
        )
        self.assertRedirects(
            respuesta,
            reverse('usuarios:login'),
            fetch_redirect_response=False,
        )

    def test_cierre_de_sesion_exige_post(self):
        usuario = User.objects.create_user('inti', password='Clave-segura-123')
        self.client.force_login(usuario)
        url = reverse('usuarios:logout')
        self.assertEqual(self.client.get(url).status_code, 405)
        respuesta = self.client.post(url)
        self.assertRedirects(respuesta, reverse('diccionario:home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_inicio_de_sesion_valida_credenciales(self):
        User.objects.create_user('runa', email='runa@example.test', password='Clave-segura-123')
        respuesta = self.client.post(
            reverse('usuarios:login'),
            {'username': 'runa', 'password': 'Clave-segura-123'},
        )
        self.assertRedirects(respuesta, reverse('diccionario:home'))
        self.assertIn('_auth_user_id', self.client.session)

        cliente = self.client_class()
        respuesta = cliente.post(
            reverse('usuarios:login'), {'username': 'runa', 'password': 'incorrecta'}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn('_auth_user_id', cliente.session)

    def test_inicio_de_sesion_tambien_acepta_correo(self):
        User.objects.create_user('inti', email='inti@example.test', password='Clave-segura-123')
        respuesta = self.client.post(
            reverse('usuarios:login'),
            {'username': 'INTI@example.test', 'password': 'Clave-segura-123'},
        )
        self.assertRedirects(respuesta, reverse('diccionario:home'))

    @override_settings(LOGIN_MAX_ATTEMPTS=2)
    def test_inicio_de_sesion_bloquea_intentos_repetidos(self):
        User.objects.create_user('yaku', password='Clave-segura-123')
        url = reverse('usuarios:login')
        for _ in range(2):
            self.assertEqual(
                self.client.post(url, {'username': 'yaku', 'password': 'incorrecta'}).status_code,
                200,
            )
        respuesta = self.client.post(url, {'username': 'yaku', 'password': 'incorrecta'})
        self.assertEqual(respuesta.status_code, 429)
        self.assertContains(respuesta, 'Demasiados intentos', status_code=429)


class CuentaYLegalTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('sumak', password='Clave-segura-123')
        self.client.force_login(self.usuario)

    def test_eliminacion_muestra_confirmacion_y_exige_contrasena_correcta(self):
        url = reverse('usuarios:eliminar_cuenta')
        self.assertContains(self.client.get(url), 'name="password"')
        respuesta = self.client.post(url, {'password': 'incorrecta'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(User.objects.filter(pk=self.usuario.pk).exists())

        respuesta = self.client.post(url, {'password': 'Clave-segura-123'})
        self.assertRedirects(respuesta, reverse('diccionario:home'))
        self.assertFalse(User.objects.filter(pk=self.usuario.pk).exists())

    def test_paginas_legales_publican_version_y_navegacion(self):
        for ruta in ('terminos', 'privacidad'):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(reverse(f'usuarios:{ruta}'))
                self.assertEqual(respuesta.status_code, 200)
                version = settings.LEGAL_TERMS_VERSION if ruta == 'terminos' else settings.LEGAL_PRIVACY_VERSION
                self.assertContains(respuesta, version)
                self.assertContains(respuesta, reverse('diccionario:home'))
