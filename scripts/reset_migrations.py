import os
import shutil
import sqlite3
from pathlib import Path

def reset_migrations():
    """
    Script para resetear completamente las migraciones y la base de datos
    """
    print("🔄 Iniciando reset completo de migraciones...")
    
    # 1. Eliminar base de datos SQLite
    db_path = "db.sqlite3"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Base de datos eliminada")
    
    # 2. Eliminar archivos de migración (excepto __init__.py)
    migration_dirs = [
        "apps/diccionario/migrations",
        "apps/usuarios/migrations"
    ]
    
    for migration_dir in migration_dirs:
        if os.path.exists(migration_dir):
            for file in os.listdir(migration_dir):
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(migration_dir, file)
                    os.remove(file_path)
                    print(f"✅ Eliminado: {file_path}")
                elif file.endswith('.pyc'):
                    file_path = os.path.join(migration_dir, file)
                    os.remove(file_path)
    
    # 3. Eliminar carpetas __pycache__
    pycache_dirs = [
        "apps/diccionario/migrations/__pycache__",
        "apps/usuarios/migrations/__pycache__",
        "apps/diccionario/__pycache__",
        "apps/usuarios/__pycache__"
    ]
    
    for pycache_dir in pycache_dirs:
        if os.path.exists(pycache_dir):
            shutil.rmtree(pycache_dir)
            print(f"✅ Eliminado: {pycache_dir}")
    
    print("🎉 Reset completado. Ahora ejecuta:")
    print("1. python manage.py makemigrations")
    print("2. python manage.py migrate")
    print("3. python manage.py createsuperuser")

if __name__ == "__main__":
    reset_migrations()
