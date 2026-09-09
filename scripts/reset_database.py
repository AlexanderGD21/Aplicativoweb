#!/usr/bin/env python
"""
Script para resetear completamente la base de datos
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
import sqlite3

def reset_database():
    """Resetea completamente la base de datos"""
    print("🗑️ RESETEANDO BASE DE DATOS COMPLETA")
    print("=" * 50)
    
    try:
        # Cerrar todas las conexiones
        connection.close()
        
        # Eliminar archivo de base de datos
        db_path = 'db.sqlite3'
        if os.path.exists(db_path):
            os.remove(db_path)
            print("✅ Base de datos eliminada")
        
        # Eliminar archivos de migración (excepto __init__.py)
        apps_dirs = ['apps/diccionario/migrations', 'apps/usuarios/migrations']
        
        for app_dir in apps_dirs:
            if os.path.exists(app_dir):
                for file in os.listdir(app_dir):
                    if file.endswith('.py') and file != '__init__.py':
                        file_path = os.path.join(app_dir, file)
                        os.remove(file_path)
                        print(f"✅ Eliminado: {file_path}")
        
        print("\n🎉 RESET COMPLETADO")
        print("=" * 50)
        print("Ahora ejecuta:")
        print("1. python manage.py makemigrations")
        print("2. python manage.py migrate")
        print("3. python manage.py createsuperuser")
        print("4. python manage.py cargar_palabras_masivo")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    respuesta = input("¿Estás seguro de que quieres resetear TODA la base de datos? (sí/no): ")
    
    if respuesta.lower() in ['sí', 'si', 'yes', 'y']:
        return 0 if reset_database() else 1
    else:
        print("❌ Operación cancelada")
        return 1

if __name__ == "__main__":
    sys.exit(main())
