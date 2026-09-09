#!/usr/bin/env python
import os
import sys
import sqlite3
from pathlib import Path

def main():
    print("🔧 Arreglando problema de migración de forma directa...")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('manage.py'):
        print("❌ Error: Ejecuta este script desde el directorio raíz del proyecto")
        return
    
    db_path = 'db.sqlite3'
    
    try:
        # Conectar a la base de datos SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📋 Verificando estructura actual...")
        
        # Verificar si la tabla diccionario_categoria existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='diccionario_categoria';
        """)
        categoria_exists = cursor.fetchone() is not None
        
        if not categoria_exists:
            print("📝 Creando tabla diccionario_categoria...")
            cursor.execute("""
                CREATE TABLE "diccionario_categoria" (
                    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    "nombre" varchar(100) NOT NULL UNIQUE,
                    "descripcion" text NOT NULL,
                    "slug" varchar(50) NOT NULL UNIQUE,
                    "fecha_creacion" datetime NOT NULL
                );
            """)
            
            # Insertar categoría por defecto
            cursor.execute("""
                INSERT INTO diccionario_categoria 
                (nombre, descripcion, slug, fecha_creacion) 
                VALUES ('General', 'Categoría general para palabras', 'general', datetime('now'));
            """)
            print("✅ Tabla diccionario_categoria creada")
        else:
            # Verificar si existe la categoría General
            cursor.execute("SELECT id FROM diccionario_categoria WHERE nombre = 'General';")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO diccionario_categoria 
                    (nombre, descripcion, slug, fecha_creacion) 
                    VALUES ('General', 'Categoría general para palabras', 'general', datetime('now'));
                """)
                print("✅ Categoría General creada")
        
        # Verificar si la columna categoria_id existe en diccionario_palabra
        cursor.execute("PRAGMA table_info(diccionario_palabra);")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'categoria_id' not in columns:
            print("📝 Agregando columna categoria_id a diccionario_palabra...")
            cursor.execute("""
                ALTER TABLE diccionario_palabra 
                ADD COLUMN categoria_id integer REFERENCES diccionario_categoria(id);
            """)
            print("✅ Columna categoria_id agregada")
        
        # Asignar todas las palabras existentes a la categoría General
        print("📝 Asignando categoría General a palabras existentes...")
        cursor.execute("""
            UPDATE diccionario_palabra 
            SET categoria_id = (SELECT id FROM diccionario_categoria WHERE nombre = 'General')
            WHERE categoria_id IS NULL;
        """)
        
        # Verificar y agregar otras columnas si no existen
        missing_columns = {
            'etimologia': 'text',
            'definicion': 'text', 
            'sinonimos': 'text'
        }
        
        for col_name, col_type in missing_columns.items():
            if col_name not in columns:
                print(f"📝 Agregando columna {col_name}...")
                cursor.execute(f"""
                    ALTER TABLE diccionario_palabra 
                    ADD COLUMN {col_name} {col_type};
                """)
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        print("✅ Base de datos actualizada exitosamente")
        
        # Marcar migraciones como aplicadas
        print("⚡ Marcando migraciones como aplicadas...")
        os.system('python manage.py migrate --fake')
        
        print("🎉 ¡Problema resuelto completamente!")
        print("Ahora puedes ejecutar: python manage.py runserver")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Solución alternativa:")
        print("1. Haz backup de tus datos si los necesitas")
        print("2. Elimina db.sqlite3")
        print("3. Ejecuta: python manage.py migrate")
        print("4. Ejecuta: python manage.py createsuperuser")

if __name__ == '__main__':
    main()
