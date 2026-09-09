#!/usr/bin/env python
import os
import sys
import sqlite3
import shutil
from pathlib import Path

def main():
    print("🔄 Reseteando migraciones completamente...")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('manage.py'):
        print("❌ Error: Ejecuta este script desde el directorio raíz del proyecto")
        return
    
    try:
        # Hacer backup de la base de datos
        if os.path.exists('db.sqlite3'):
            shutil.copy2('db.sqlite3', 'db_backup.sqlite3')
            print("📋 Backup creado: db_backup.sqlite3")
        
        # Eliminar archivos de migración (excepto __init__.py)
        migration_dirs = [
            'apps/diccionario/migrations',
            'apps/usuarios/migrations'
        ]
        
        for migration_dir in migration_dirs:
            if os.path.exists(migration_dir):
                for file in os.listdir(migration_dir):
                    if file.endswith('.py') and file != '__init__.py':
                        os.remove(os.path.join(migration_dir, file))
                        print(f"🗑️ Eliminado: {migration_dir}/{file}")
                
                # Limpiar __pycache__
                pycache_dir = os.path.join(migration_dir, '__pycache__')
                if os.path.exists(pycache_dir):
                    shutil.rmtree(pycache_dir)
        
        # Eliminar base de datos actual
        if os.path.exists('db.sqlite3'):
            os.remove('db.sqlite3')
            print("🗑️ Base de datos eliminada")
        
        # Crear nuevas migraciones
        print("📝 Creando nuevas migraciones...")
        os.system('python manage.py makemigrations diccionario')
        os.system('python manage.py makemigrations usuarios')
        
        # Aplicar migraciones
        print("⚡ Aplicando migraciones...")
        os.system('python manage.py migrate')
        
        # Crear categoría por defecto
        print("📝 Creando categoría por defecto...")
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO diccionario_categoria 
            (nombre, descripcion, slug, fecha_creacion) 
            VALUES ('General', 'Categoría general para palabras', 'general', datetime('now'));
        """)
        
        conn.commit()
        conn.close()
        
        print("🎉 ¡Migraciones reseteadas completamente!")
        print("💡 Ahora puedes:")
        print("   1. python manage.py createsuperuser")
        print("   2. python manage.py runserver")
        print("   3. Restaurar datos desde db_backup.sqlite3 si es necesario")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if os.path.exists('db_backup.sqlite3'):
            print("💡 Puedes restaurar desde: db_backup.sqlite3")

if __name__ == '__main__':
    main()
