#!/usr/bin/env python
"""
Script para crear las migraciones necesarias
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.core.management import execute_from_command_line

def main():
    """Crear migraciones para todos los modelos"""
    print("Creando migraciones...")
    
    # Crear migraciones para usuarios
    print("1. Creando migraciones para usuarios...")
    execute_from_command_line(['manage.py', 'makemigrations', 'usuarios'])
    
    # Crear migraciones para diccionario
    print("2. Creando migraciones para diccionario...")
    execute_from_command_line(['manage.py', 'makemigrations', 'diccionario'])
    
    # Aplicar migraciones
    print("3. Aplicando migraciones...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    print("✅ Migraciones creadas y aplicadas exitosamente!")

if __name__ == '__main__':
    main()
