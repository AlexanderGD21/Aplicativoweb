#!/usr/bin/env python
"""
Script para arreglar problemas de migración
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.db import connection
from apps.diccionario.models import Categoria, Palabra

def fix_migration_issue():
    """Arregla el problema de migración eliminando migraciones conflictivas"""
    
    print("🔧 Arreglando problema de migración...")
    
    try:
        # Crear una categoría por defecto si no existe
        categoria_default, created = Categoria.objects.get_or_create(
            nombre="General",
            defaults={
                'descripcion': 'Categoría general para palabras sin clasificar',
                'slug': 'general'
            }
        )
        
        if created:
            print(f"✅ Categoría por defecto creada: {categoria_default.nombre}")
        else:
            print(f"✅ Categoría por defecto ya existe: {categoria_default.nombre}")
        
        # Actualizar palabras sin categoría
        palabras_sin_categoria = Palabra.objects.filter(categoria__isnull=True)
        count = palabras_sin_categoria.count()
        
        if count > 0:
            palabras_sin_categoria.update(categoria=categoria_default)
            print(f"✅ {count} palabras actualizadas con categoría por defecto")
        else:
            print("✅ Todas las palabras ya tienen categoría asignada")
        
        print("🎉 Problema de migración solucionado!")
        return True
        
    except Exception as e:
        print(f"❌ Error al arreglar migración: {e}")
        return False

if __name__ == "__main__":
    fix_migration_issue()
