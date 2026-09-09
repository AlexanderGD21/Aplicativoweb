#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def fix_migration_error():
    """
    Script para solucionar errores de migración
    """
    print("🔧 Solucionando errores de migración...")
    
    # Eliminar migraciones problemáticas
    migrations_to_delete = [
        'apps/diccionario/migrations/0008_alter_categoria_options_and_more.py',
        'apps/usuarios/migrations/0005_alter_perfilusuario_options_and_more.py'
    ]
    
    for migration_file in migrations_to_delete:
        if os.path.exists(migration_file):
            os.remove(migration_file)
            print(f"✅ Eliminado: {migration_file}")
    
    print("🔄 Migraciones problemáticas eliminadas")
    print("📝 Ahora ejecuta:")
    print("python manage.py makemigrations usuarios")
    print("python manage.py makemigrations diccionario")
    print("python manage.py migrate")

if __name__ == '__main__':
    fix_migration_error()
