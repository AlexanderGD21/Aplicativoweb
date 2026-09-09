import os
import sys
import django
import sqlite3

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

def fix_duplicate_words():
    """
    Elimina palabras duplicadas usando SQL directo
    """
    db_path = 'db.sqlite3'
    
    try:
        # Conectar a la base de datos SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Buscando palabras duplicadas...")
        
        # Encontrar duplicados
        cursor.execute("""
            SELECT palabra_kichwa, categoria_id, COUNT(*) as count
            FROM diccionario_palabra 
            GROUP BY palabra_kichwa, categoria_id 
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        print(f"Encontrados {len(duplicates)} grupos de duplicados")
        
        if duplicates:
            for palabra_kichwa, categoria_id, count in duplicates:
                print(f"Palabra duplicada: {palabra_kichwa} (Categoría ID: {categoria_id})")
                print(f"Cantidad de duplicados: {count}")
            
            # Eliminar duplicados manteniendo solo el ID más pequeño
            cursor.execute("""
                DELETE FROM diccionario_palabra 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) 
                    FROM diccionario_palabra 
                    GROUP BY palabra_kichwa, categoria_id
                )
            """)
            
            deleted_count = cursor.rowcount
            print(f"✅ Eliminados {deleted_count} duplicados")
            
            # Confirmar cambios
            conn.commit()
        else:
            print("✅ No se encontraron duplicados")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_duplicate_words()
