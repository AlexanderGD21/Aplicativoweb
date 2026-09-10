import random

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Crea cuentas de prueba no autenticables únicamente en desarrollo.'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=10)
        parser.add_argument('--limpiar', action='store_true')

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Este comando solo puede ejecutarse con DEBUG=True.')

        cantidad = options['cantidad']
        if not 1 <= cantidad <= 100:
            raise CommandError('La cantidad debe estar entre 1 y 100.')

        if options['limpiar']:
            User.objects.filter(username__startswith='usuario_prueba_').delete()

        nombres = ['Inti', 'Killa', 'Wayra', 'Sumak', 'Kusi', 'Yaku', 'Allpa', 'Runa']
        apellidos = ['Kuntur', 'Puma', 'Amaru', 'Rumi', 'Sinchi']
        creados = 0

        for _ in range(cantidad):
            numero = random.SystemRandom().randint(1000, 999999)
            username = f'usuario_prueba_{numero}'
            if User.objects.filter(username=username).exists():
                continue

            with transaction.atomic():
                user = User(
                    username=username,
                    email=f'{username}@example.test',
                    first_name=random.choice(nombres),
                    last_name=random.choice(apellidos),
                    is_active=False,
                )
                user.set_unusable_password()
                user.save()
                user.perfil.biografia = 'Cuenta de prueba local no autenticable.'
                user.perfil.save(update_fields=['biografia', 'fecha_actualizacion', 'ultima_actividad'])
                creados += 1

        self.stdout.write(self.style.SUCCESS(f'Cuentas de prueba no autenticables creadas: {creados}.'))
