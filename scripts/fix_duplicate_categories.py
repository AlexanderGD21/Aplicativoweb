import os
import sys
import django
import sqlite3
import re

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

def fix_duplicate_categories():
    """
    Arregla categorías con slugs duplicados o vacíos
    """
    db_path = 'db.sqlite3'
    
    try:
        # Conectar a la base de datos SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Verificando estructura de categorías...")
        
        # Verificar si existe la columna slug
        cursor.execute("PRAGMA table_info(diccionario_categoria)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'slug' not in column_names:
            print("⚠️ La columna 'slug' no existe aún. Esto es normal antes de la migración.")
            conn.close()
            return
        
        print("🔧 Arreglando slugs duplicados...")
        
        # Encontrar categorías con slugs duplicados o vacíos
        cursor.execute("""
            SELECT id, nombre, slug 
            FROM diccionario_categoria 
            WHERE slug IS NULL OR slug = '' OR slug IN (
                SELECT slug 
                FROM diccionario_categoria 
                WHERE slug IS NOT NULL AND slug != ''
                GROUP BY slug 
                HAVING COUNT(*) > 1
            )
            ORDER BY id
        """)
        
        categories_to_fix = cursor.fetchall()
        print(f"Encontradas {len(categories_to_fix)} categorías para arreglar")
        
        for cat_id, nombre, current_slug in categories_to_fix:
            # Generar slug base
            base_slug = re.sub(r'[^a-zA-Z0-9\s]', '', nombre.lower())
            base_slug = re.sub(r'\s+', '-', base_slug.strip())
            
            if not base_slug:
                base_slug = f"categoria-{cat_id}"
            
            # Hacer el slug único
            slug = base_slug
            counter = 1
            while True:
                cursor.execute("SELECT id FROM diccionario_categoria WHERE slug = ? AND id != ?", (slug, cat_id))
                if not cursor.fetchone():
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Actualizar el slug
            cursor.execute("UPDATE diccionario_categoria SET slug = ? WHERE id = ?", (slug, cat_id))
            print(f"  Categoría '{nombre}' -> slug: '{slug}'")
        
        # Confirmar cambios
        conn.commit()
        print("✅ Slugs de categorías corregidos")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_duplicate_categories()
