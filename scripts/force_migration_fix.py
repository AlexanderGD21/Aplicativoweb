import os
import sys
import django
import sqlite3

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

def force_fix_database():
    """
    Fuerza la corrección de la base de datos para permitir migraciones
    """
    db_path = 'db.sqlite3'
    
    try:
        # Conectar a la base de datos SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Forzando corrección de base de datos...")
        
        # 1. Verificar y limpiar duplicados en palabras
        print("1. Limpiando duplicados en palabras...")
        cursor.execute("""
            DELETE FROM diccionario_palabra 
            WHERE rowid NOT IN (
                SELECT MIN(rowid) 
                FROM diccionario_palabra 
                GROUP BY palabra_kichwa, categoria_id
            )
        """)
        print(f"   Eliminados {cursor.rowcount} duplicados de palabras")
        
        # 2. Verificar estructura de categorías
        cursor.execute("PRAGMA table_info(diccionario_categoria)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 3. Si existe la columna slug, limpiar duplicados
        if 'slug' in column_names:
            print("2. Limpiando slugs duplicados en categorías...")
            
            # Primero, poner NULL a todos los slugs duplicados
            cursor.execute("""
                UPDATE diccionario_categoria 
                SET slug = NULL 
                WHERE slug IN (
                    SELECT slug 
                    FROM diccionario_categoria 
                    WHERE slug IS NOT NULL AND slug != ''
                    GROUP BY slug 
                    HAVING COUNT(*) > 1
                )
            """)
            print(f"   Limpiados {cursor.rowcount} slugs duplicados")
            
            # Luego, generar slugs únicos
            cursor.execute("SELECT id, nombre FROM diccionario_categoria WHERE slug IS NULL")
            categories = cursor.fetchall()
            
            for cat_id, nombre in categories:
                import re
                base_slug = re.sub(r'[^a-zA-Z0-9\s]', '', nombre.lower())
                base_slug = re.sub(r'\s+', '-', base_slug.strip())
                
                # Hacer el slug único
                slug = base_slug
                counter = 1
                while True:
                    cursor.execute("SELECT id FROM diccionario_categoria WHERE slug = ?", (slug,))
                    if not cursor.fetchone():
                        break
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                cursor.execute("UPDATE diccionario_categoria SET slug = ? WHERE id = ?", (slug, cat_id))
        
        # 4. Confirmar cambios
        conn.commit()
        print("✅ Base de datos corregida exitosamente")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    force_fix_database()
