from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

class Command(BaseCommand):
    help = 'Crear un superusuario para el diccionario Kichwa'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nombre de usuario')
        parser.add_argument('--email', type=str, help='Email del usuario')
        parser.add_argument('--password', type=str, help='Contraseña')

    def handle(self, *args, **options):
        username = options.get('username') or input('Username: ')
        email = options.get('email') or input('Email: ')
        password = options.get('password') or input('Password: ')
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'El usuario {username} ya existe')
            )
            return
        
        try:
            with transaction.atomic():
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Actualizar perfil
                perfil = user.perfil
                perfil.nivel_kichwa = 'experto'
                perfil.biografia = 'Administrador del Diccionario Kichwa'
                perfil.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Superusuario {username} creado exitosamente')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando superusuario: {e}')
            )
