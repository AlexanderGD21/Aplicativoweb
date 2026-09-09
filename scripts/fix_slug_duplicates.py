#!/usr/bin/env python
"""
Script para arreglar slugs duplicados antes de aplicar migraciones
"""

import os
import sys
import django
from django.utils.text import slugify

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.db import connection, transaction
from apps.diccionario.models import Palabra

def fix_duplicate_slugs():
    """Arregla slugs duplicados en la tabla de palabras"""
    print("🔧 ARREGLANDO SLUGS DUPLICADOS")
    print("=" * 50)
    
    try:
        with connection.cursor() as cursor:
            # Verificar si la columna slug existe
            cursor.execute("PRAGMA table_info(diccionario_palabra)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'slug' not in columns:
                print("❌ La columna 'slug' no existe aún")
                return False
            
            # Obtener todas las palabras
            palabras = Palabra.objects.all().order_by('id')
            slugs_usados = set()
            palabras_actualizadas = 0
            
            with transaction.atomic():
                for palabra in palabras:
                    # Generar slug base
                    base_slug = slugify(f"{palabra.palabra_kichwa}-{palabra.traduccion_espanol}")
                    
                    # Si el slug actual es único, mantenerlo
                    if palabra.slug and palabra.slug not in slugs_usados:
                        slugs_usados.add(palabra.slug)
                        continue
                    
                    # Generar slug único
                    slug = base_slug
                    counter = 1
                    
                    while slug in slugs_usados:
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    
                    # Actualizar la palabra
                    palabra.slug = slug
                    palabra.save(update_fields=['slug'])
                    slugs_usados.add(slug)
                    palabras_actualizadas += 1
                    
                    print(f"✓ Actualizado: {palabra.palabra_kichwa} → {slug}")
            
            print(f"\n✅ {palabras_actualizadas} palabras actualizadas")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def reset_migrations():
    """Resetea las migraciones problemáticas"""
    print("\n🔄 RESETEANDO MIGRACIONES")
    print("=" * 50)
    
    try:
        with connection.cursor() as cursor:
            # Eliminar registros de migraciones problemáticas
            cursor.execute("""
                DELETE FROM django_migrations 
                WHERE app = 'diccionario' AND name LIKE '%0002%'
            """)
            
            cursor.execute("""
                DELETE FROM django_migrations 
                WHERE app = 'usuarios' AND name LIKE '%0002%'
            """)
            
            print("✅ Migraciones reseteadas")
            return True
            
    except Exception as e:
        print(f"❌ Error reseteando migraciones: {e}")
        return False

def main():
    print("🚀 INICIANDO REPARACIÓN DE BASE DE DATOS")
    print("=" * 60)
    
    # Paso 1: Arreglar slugs duplicados
    if not fix_duplicate_slugs():
        print("❌ No se pudieron arreglar los slugs")
        return 1
    
    # Paso 2: Resetear migraciones
    if not reset_migrations():
        print("❌ No se pudieron resetear las migraciones")
        return 1
    
    print("\n🎉 REPARACIÓN COMPLETADA")
    print("=" * 60)
    print("Ahora ejecuta:")
    print("1. python manage.py makemigrations diccionario")
    print("2. python manage.py makemigrations usuarios")
    print("3. python manage.py migrate")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
