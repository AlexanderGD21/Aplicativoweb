#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.core.management import execute_from_command_line

def main():
    """Crear migración para los nuevos campos de juegos"""
    print("Creando migración para campos de juegos...")
    
    try:
        # Crear la migración
        execute_from_command_line(['manage.py', 'makemigrations', 'diccionario', '--name', 'agregar_campos_juegos'])
        print("✅ Migración creada exitosamente")
        
        # Aplicar la migración
        print("Aplicando migración...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migración aplicada exitosamente")
        
        print("\n🎮 Los campos para juegos han sido agregados al modelo Palabra:")
        print("   - apta_para_juegos (Boolean)")
        print("   - dificultad_juego (CharField)")
        print("   - descripcion_juego_espanol (TextField)")
        print("   - descripcion_juego_kichwa (TextField)")
        print("   - nivel_dificultad (CharField)")
        print("   - frecuencia_uso (PositiveInteger)")
        
    except Exception as e:
        print(f"❌ Error al crear/aplicar migración: {e}")
        return False
    
    return True

if __name__ == '__main__':
    main()
