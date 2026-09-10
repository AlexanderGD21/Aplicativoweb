from getpass import getpass

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Crea un superusuario sin exponer la contraseña en argumentos o salida.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nombre de usuario')
        parser.add_argument('--email', type=str, help='Correo electrónico')

    def handle(self, *args, **options):
        username = (options.get('username') or input('Usuario: ')).strip()
        email = (options.get('email') or input('Correo: ')).strip()

        if User.objects.filter(username__iexact=username).exists():
            raise CommandError('Ese nombre de usuario ya existe.')
        if email and User.objects.filter(email__iexact=email).exists():
            raise CommandError('Ese correo ya está asociado a otra cuenta.')

        password = getpass('Contraseña: ')
        confirmation = getpass('Confirma la contraseña: ')
        if password != confirmation:
            raise CommandError('Las contraseñas no coinciden.')

        candidate = User(username=username, email=email)
        try:
            validate_password(password, user=candidate)
        except ValidationError as exc:
            raise CommandError(' '.join(exc.messages)) from exc

        with transaction.atomic():
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            perfil = user.perfil
            perfil.nivel_kichwa = 'avanzado'
            perfil.biografia = 'Administración del Diccionario Kichwa'
            perfil.save(update_fields=['nivel_kichwa', 'biografia', 'fecha_actualizacion', 'ultima_actividad'])

        self.stdout.write(self.style.SUCCESS(f'Superusuario {username} creado.'))
