from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.usuarios.models import PerfilUsuario
from django.db import transaction

class Command(BaseCommand):
    help = 'Limpiar perfiles huérfanos y crear perfiles faltantes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Aplicar las correcciones automáticamente'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué se haría sin aplicar cambios'
        )

    def handle(self, *args, **options):
        fix = options['fix']
        dry_run = options['dry_run']

        self.stdout.write(
            self.style.SUCCESS('🔍 Analizando perfiles de usuario...')
        )

        # Encontrar usuarios sin perfil
        usuarios_sin_perfil = []
        for user in User.objects.all():
            try:
                user.perfil
            except PerfilUsuario.DoesNotExist:
                usuarios_sin_perfil.append(user)

        # Encontrar perfiles huérfanos
        perfiles_huerfanos = PerfilUsuario.objects.filter(usuario__isnull=True)

        # Mostrar resultados
        self.stdout.write(f'\n📊 ANÁLISIS COMPLETADO:')
        self.stdout.write(f'   Usuarios sin perfil: {len(usuarios_sin_perfil)}')
        self.stdout.write(f'   Perfiles huérfanos: {perfiles_huerfanos.count()}')

        if usuarios_sin_perfil:
            self.stdout.write(f'\n👤 USUARIOS SIN PERFIL:')
            for user in usuarios_sin_perfil:
                self.stdout.write(f'   - {user.username} ({user.email})')

        if perfiles_huerfanos.exists():
            self.stdout.write(f'\n👻 PERFILES HUÉRFANOS:')
            for perfil in perfiles_huerfanos:
                self.stdout.write(f'   - Perfil ID: {perfil.id}')

        # Aplicar correcciones si se solicita
        if fix and not dry_run:
            self.stdout.write(f'\n🔧 APLICANDO CORRECCIONES...')
            
            correcciones = 0
            
            # Crear perfiles faltantes
            for user in usuarios_sin_perfil:
                try:
                    with transaction.atomic():
                        PerfilUsuario.objects.create(
                            usuario=user,
                            ubicacion='No especificada',
                            nivel_kichwa='principiante',
                            intereses='Aprender Kichwa',
                            biografia=f'Usuario {user.username}'
                        )
                        correcciones += 1
                        self.stdout.write(f'✅ Perfil creado para: {user.username}')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error creando perfil para {user.username}: {e}')
                    )

            # Eliminar perfiles huérfanos
            if perfiles_huerfanos.exists():
                count = perfiles_huerfanos.count()
                perfiles_huerfanos.delete()
                correcciones += count
                self.stdout.write(f'✅ Eliminados {count} perfiles huérfanos')

            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 CORRECCIONES COMPLETADAS: {correcciones}')
            )

        elif dry_run:
            self.stdout.write(f'\n🔍 MODO DRY-RUN - No se aplicaron cambios')
            self.stdout.write(f'   Para aplicar correcciones usa: --fix')

        elif not fix:
            if usuarios_sin_perfil or perfiles_huerfanos.exists():
                self.stdout.write(f'\n💡 PARA CORREGIR PROBLEMAS:')
                self.stdout.write(f'   python manage.py limpiar_perfiles_huerfanos --fix')
            else:
                self.stdout.write(f'\n✅ No se encontraron problemas que corregir')

        self.stdout.write(f'\n🏁 Proceso completado')
