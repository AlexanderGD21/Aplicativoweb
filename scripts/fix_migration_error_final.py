import os
import sys
import django
import sqlite3

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.db import connection
from django.conf import settings

def fix_database_structure():
    """Arreglar la estructura de la base de datos directamente"""
    print("🔧 Reparando estructura de la base de datos...")
    
    # Conectar directamente a SQLite
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Verificar qué columnas existen
        cursor.execute("PRAGMA table_info(diccionario_palabra)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Columnas existentes: {columns}")
        
        # Agregar columnas faltantes si no existen
        columns_to_add = [
            ('apta_para_juegos', 'BOOLEAN DEFAULT 1'),
            ('dificultad_juego', 'VARCHAR(20) DEFAULT "medio"'),
            ('descripcion_juego_espanol', 'TEXT'),
            ('descripcion_juego_kichwa', 'TEXT'),
            ('nivel_dificultad', 'VARCHAR(20) DEFAULT "medio"'),
            ('palabras_correctas', 'INTEGER DEFAULT 0'),
            ('palabras_incorrectas', 'INTEGER DEFAULT 0'),
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE diccionario_palabra ADD COLUMN {column_name} {column_type}')
                    print(f"✅ Agregada columna: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        print(f"⚠️ Error agregando {column_name}: {e}")
        
        # Verificar tabla de estadísticas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diccionario_estadisticajuego (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                tipo_juego VARCHAR(50) NOT NULL,
                puntuacion INTEGER DEFAULT 0,
                respuestas_correctas INTEGER DEFAULT 0,
                respuestas_totales INTEGER DEFAULT 0,
                dificultad VARCHAR(20) DEFAULT 'medio',
                tiempo_jugado INTEGER DEFAULT 0,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES auth_user (id)
            )
        """)
        print("✅ Tabla de estadísticas verificada")
        
        conn.commit()
        print("✅ Estructura de base de datos reparada exitosamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database_structure()
