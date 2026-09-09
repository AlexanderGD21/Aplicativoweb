#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.db import connection
from apps.diccionario.models import Categoria

def fix_categoria_color_field():
    """
    Corrige el problema del campo color faltante en la tabla diccionario_categoria
    """
    print("🔧 Iniciando corrección del campo color en Categoria...")
    
    try:
        # Verificar si la columna existe
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(diccionario_categoria);")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'color' not in columns:
                print("❌ Campo 'color' no encontrado. Agregando columna...")
                
                # Agregar la columna color con valor por defecto
                cursor.execute("""
                    ALTER TABLE diccionario_categoria 
                    ADD COLUMN color VARCHAR(7) DEFAULT '#007bff';
                """)
                
                print("✅ Columna 'color' agregada exitosamente")
                
                # Actualizar categorías existentes con colores por defecto
                categorias = Categoria.objects.all()
                colores_default = [
                    '#007bff', '#28a745', '#dc3545', '#ffc107', 
                    '#17a2b8', '#6f42c1', '#e83e8c', '#fd7e14'
                ]
                
                for i, categoria in enumerate(categorias):
                    color = colores_default[i % len(colores_default)]
                    cursor.execute(
                        "UPDATE diccionario_categoria SET color = ? WHERE id = ?",
                        [color, categoria.id]
                    )
                
                print(f"✅ Actualizadas {categorias.count()} categorías con colores por defecto")
                
            else:
                print("✅ Campo 'color' ya existe en la tabla")
                
    except Exception as e:
        print(f"❌ Error al corregir el campo color: {str(e)}")
        return False
    
    return True

def verify_fix():
    """
    Verifica que la corrección fue exitosa
    """
    try:
        # Intentar acceder al campo color
        categoria = Categoria.objects.first()
        if categoria:
            color = categoria.color
            print(f"✅ Verificación exitosa. Color de ejemplo: {color}")
            return True
    except Exception as e:
        print(f"❌ Verificación falló: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando corrección del error de búsqueda...")
    
    if fix_categoria_color_field():
        if verify_fix():
            print("🎉 Corrección completada exitosamente!")
            print("📝 La funcionalidad de búsqueda debería funcionar ahora.")
        else:
            print("⚠️ Corrección aplicada pero verificación falló.")
    else:
        print("❌ No se pudo aplicar la corrección.")
