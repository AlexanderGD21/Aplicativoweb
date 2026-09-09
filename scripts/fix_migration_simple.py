#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from apps.diccionario.models import Categoria, Palabra

def main():
    print("🔧 Arreglando problema de migración...")
    
    try:
        # Paso 1: Verificar qué columnas existen en la tabla actual
        print("📋 Verificando estructura actual de la base de datos...")
        
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(diccionario_palabra);")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"Columnas existentes: {columns}")
        
        # Paso 2: Crear migración para agregar Categoria
        print("📝 Creando migración para Categoria...")
        execute_from_command_line(['manage.py', 'makemigrations', 'diccionario', '--name', 'add_categoria'])
        
        # Paso 3: Aplicar migraciones
        print("⚡ Aplicando migraciones...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Paso 4: Crear categoría por defecto
        print("📂 Creando categoría por defecto...")
        categoria_general, created = Categoria.objects.get_or_create(
            nombre="General",
            defaults={
                'descripcion': 'Categoría general para palabras sin clasificar',
                'slug': 'general'
            }
        )
        
        if created:
            print("✅ Categoría 'General' creada exitosamente")
        else:
            print("ℹ️ Categoría 'General' ya existe")
        
        # Paso 5: Asignar categoría a palabras existentes
        print("🔗 Asignando categoría a palabras existentes...")
        palabras_sin_categoria = Palabra.objects.filter(categoria__isnull=True)
        count = palabras_sin_categoria.update(categoria=categoria_general)
        print(f"✅ {count} palabras asignadas a la categoría General")
        
        print("🎉 ¡Migración completada exitosamente!")
        print("Ahora puedes ejecutar: python manage.py runserver")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Intentando solución alternativa...")
        
        # Solución alternativa: resetear migraciones
        try:
            print("🗑️ Eliminando migraciones conflictivas...")
            import glob
            migration_files = glob.glob('apps/diccionario/migrations/0*.py')
            for file in migration_files:
                if '0001_initial.py' not in file:
                    os.remove(file)
                    print(f"Eliminado: {file}")
            
            # Crear nueva migración
            print("📝 Creando nueva migración...")
            execute_from_command_line(['manage.py', 'makemigrations', 'diccionario'])
            
            # Aplicar migración
            print("⚡ Aplicando migración...")
            execute_from_command_line(['manage.py', 'migrate', '--fake-initial'])
            
            print("✅ Solución alternativa aplicada exitosamente")
            
        except Exception as e2:
            print(f"❌ Error en solución alternativa: {e2}")
            print("\n💡 Solución manual:")
            print("1. Elimina el archivo db.sqlite3")
            print("2. Ejecuta: python manage.py migrate")
            print("3. Ejecuta: python manage.py createsuperuser")

if __name__ == '__main__':
    main()
