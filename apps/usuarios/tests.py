from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PerfilUsuario


class RecuperacionContrasenaTests(TestCase):
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


class PerfilYProgresoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('sisa', password='clave-segura-123')
        self.client.force_login(self.usuario)

    def test_perfil_y_progreso_usan_la_relacion_correcta(self):
        self.assertTrue(PerfilUsuario.objects.filter(usuario=self.usuario).exists())
        self.assertEqual(self.client.get(reverse('usuarios:perfil')).status_code, 200)

        respuesta = self.client.post(reverse('usuarios:actualizar_puntos'), {'puntos': 25})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['puntos_totales'], 25)

        respuesta = self.client.post(reverse('usuarios:incrementar_palabras'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['palabras_aprendidas'], 1)

    def test_puntos_negativos_se_rechazan(self):
        respuesta = self.client.post(reverse('usuarios:actualizar_puntos'), {'puntos': -1})
        self.assertEqual(respuesta.status_code, 400)


class RegistroYSesionTests(TestCase):
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

    def test_registro_exige_terminos_y_correo_unico(self):
        sin_terminos = self._datos_registro()
        sin_terminos.pop('acepto_terminos')
        respuesta = self.client.post(reverse('usuarios:registro'), sin_terminos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username='killa').exists())

        respuesta = self.client.post(reverse('usuarios:registro'), self._datos_registro())
        self.assertRedirects(respuesta, reverse('usuarios:login'))
        self.assertTrue(User.objects.filter(email='killa@example.test').exists())

        respuesta = self.client.post(
            reverse('usuarios:registro'), self._datos_registro(username='killa2')
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Ya existe una cuenta registrada con este correo.')

    def test_cierre_de_sesion_exige_post(self):
        usuario = User.objects.create_user('inti', password='Clave-segura-123')
        self.client.force_login(usuario)
        url = reverse('usuarios:logout')
        self.assertEqual(self.client.get(url).status_code, 405)
        respuesta = self.client.post(url)
        self.assertRedirects(respuesta, reverse('diccionario:home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_inicio_de_sesion_valida_credenciales(self):
        User.objects.create_user('runa', password='Clave-segura-123')
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
