from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from apps.usuarios.models import PerfilUsuario
import random

class Command(BaseCommand):
    help = 'Crear usuarios de prueba para el diccionario Kichwa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=10,
            help='Cantidad de usuarios a crear (default: 10)'
        )
        parser.add_argument(
            '--admin',
            action='store_true',
            help='Crear también un usuario administrador'
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Eliminar usuarios de prueba existentes antes de crear nuevos'
        )

    def handle(self, *args, **options):
        cantidad = options['cantidad']
        crear_admin = options['admin']
        limpiar = options['limpiar']

        self.stdout.write(
            self.style.SUCCESS(f'🚀 Iniciando creación de {cantidad} usuarios de prueba...')
        )

        # Nombres Kichwa auténticos
        nombres_kichwa = [
            'Inti', 'Killa', 'Wayra', 'Mama', 'Tayta', 'Sumak', 'Kusi', 'Yaku',
            'Urku', 'Allpa', 'Runa', 'Warmi', 'Kari', 'Wawa', 'Hatun', 'Uchuy',
            'Phuyu', 'Qucha', 'Sacha', 'Llakta', 'Ayllu', 'Minka', 'Ayni', 'Tukuy',
            'Kawsay', 'Munay', 'Yachay', 'Llankay', 'Rimay', 'Pukllay'
        ]

        apellidos_kichwa = [
            'Condor', 'Puma', 'Amaru', 'Kuntur', 'Atik', 'Ukuku', 'Llama',
            'Waman', 'Chinchay', 'Taruka', 'Kuychi', 'Illapa', 'Chirapa',
            'Yakana', 'Mallku', 'Apu', 'Paccha', 'Rumi', 'Qhapaq', 'Sinchi'
        ]

        if limpiar:
            self.stdout.write('🧹 Limpiando usuarios de prueba existentes...')
            usuarios_prueba = User.objects.filter(username__startswith='usuario_')
            count = usuarios_prueba.count()
            usuarios_prueba.delete()
            self.stdout.write(f'✅ Eliminados {count} usuarios de prueba')

        usuarios_creados = 0
        errores = 0

        # Crear usuarios regulares
        for i in range(cantidad):
            try:
                with transaction.atomic():
                    # Generar datos únicos
                    nombre = random.choice(nombres_kichwa)
                    apellido = random.choice(apellidos_kichwa)
                    numero = random.randint(1, 9999)
                    
                    username = f'usuario_{nombre.lower()}_{numero}'
                    email = f'{username}@diccionariokichwa.test'
                    
                    # Verificar que no exista
                    if User.objects.filter(username=username).exists():
                        username = f'{username}_{random.randint(10, 99)}'
                    
                    if User.objects.filter(email=email).exists():
                        email = f'{username}_{random.randint(10, 99)}@diccionariokichwa.test'

                    # Crear usuario
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='kichwa123',
                        first_name=nombre,
                        last_name=apellido
                    )

                    # Crear o obtener perfil
                    perfil, created = PerfilUsuario.objects.get_or_create(
                        usuario=user,
                        defaults={
                            'fecha_nacimiento': None,
                            'ubicacion': f'Comunidad {apellido}',
                            'nivel_kichwa': random.choice(['principiante', 'intermedio', 'avanzado']),
                            'intereses': f'Aprender {nombre.lower()}, cultura andina',
                            'biografia': f'Estudiante de Kichwa interesado en {nombre.lower()}'
                        }
                    )

                    usuarios_creados += 1
                    self.stdout.write(f'✅ Usuario creado: {username} ({email})')

            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Error creando usuario {i+1}: {str(e)}')
                )

        # Crear usuario administrador
        if crear_admin:
            try:
                with transaction.atomic():
                    admin_username = 'admin_kichwa'
                    admin_email = 'admin@diccionariokichwa.test'
                    
                    # Verificar si ya existe
                    if not User.objects.filter(username=admin_username).exists():
                        admin_user = User.objects.create_superuser(
                            username=admin_username,
                            email=admin_email,
                            password='admin123',
                            first_name='Administrador',
                            last_name='Kichwa'
                        )

                        # Crear perfil de administrador
                        PerfilUsuario.objects.get_or_create(
                            usuario=admin_user,
                            defaults={
                                'ubicacion': 'Oficina Central',
                                'nivel_kichwa': 'experto',
                                'intereses': 'Administración del diccionario, preservación cultural',
                                'biografia': 'Administrador del Diccionario Kichwa Digital'
                            }
                        )

                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Administrador creado: {admin_username}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ El administrador {admin_username} ya existe')
                        )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error creando administrador: {str(e)}')
                )

        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'🎉 PROCESO COMPLETADO')
        )
        self.stdout.write(f'✅ Usuarios creados: {usuarios_creados}')
        if errores > 0:
            self.stdout.write(f'❌ Errores: {errores}')
        
        if crear_admin:
            self.stdout.write(f'👑 Administrador: admin_kichwa / admin123')
        
        self.stdout.write('\n📝 CREDENCIALES DE PRUEBA:')
        self.stdout.write('   Usuario: cualquier usuario_* / kichwa123')
        self.stdout.write('   Admin: admin_kichwa / admin123')
        self.stdout.write('\n🌟 ¡Usuarios listos para probar el diccionario!')
