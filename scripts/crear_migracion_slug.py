#!/usr/bin/env python
"""
Script para crear migración que agregue el campo slug a Categoria
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

def verificar_columna_slug():
    """Verificar si la columna slug existe"""
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(diccionario_categoria)")
        columnas = cursor.fetchall()
        columnas_existentes = [col[1] for col in columnas]
        return 'slug' in columnas_existentes

def main():
    print("🔍 VERIFICANDO CAMPO SLUG EN CATEGORIA")
    print("=" * 40)
    
    tiene_slug = verificar_columna_slug()
    
    if tiene_slug:
        print("✅ La columna 'slug' ya existe")
        print("No es necesario crear migración")
        return 0
    
    print("❌ La columna 'slug' NO existe")
    print("Creando migración...")
    
    try:
        # Crear migración
        execute_from_command_line([
            'manage.py', 'makemigrations', 'diccionario',
            '--name', 'add_slug_to_categoria'
        ])
        
        print("✅ Migración creada exitosamente")
        print("\nAhora ejecuta:")
        print("python manage.py migrate")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error creando migración: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
