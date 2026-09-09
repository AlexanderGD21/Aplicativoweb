import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from apps.diccionario.models import Palabra
from django.db.models import Count

def find_and_fix_duplicates():
    print("Buscando palabras duplicadas...")
    
    # Encontrar duplicados
    duplicates = (Palabra.objects
                 .values('palabra_kichwa', 'categoria')
                 .annotate(count=Count('id'))
                 .filter(count__gt=1))
    
    print(f"Encontrados {len(duplicates)} grupos de duplicados")
    
    if not duplicates:
        print("✅ No se encontraron duplicados")
        return
    
    for duplicate in duplicates:
        palabra_kichwa = duplicate['palabra_kichwa']
        categoria_id = duplicate['categoria']
        
        # Obtener todas las instancias duplicadas
        palabras_duplicadas = Palabra.objects.filter(
            palabra_kichwa=palabra_kichwa,
            categoria_id=categoria_id
        ).order_by('id')
        
        print(f"\nPalabra duplicada: {palabra_kichwa} (Categoría ID: {categoria_id})")
        print(f"Cantidad de duplicados: {palabras_duplicadas.count()}")
        
        # Mantener solo la primera, eliminar el resto
        primera_palabra = palabras_duplicadas.first()
        duplicados_a_eliminar = palabras_duplicadas.exclude(id=primera_palabra.id)
        
        print(f"Manteniendo: ID {primera_palabra.id}")
        print(f"Eliminando: {[p.id for p in duplicados_a_eliminar]}")
        
        # Eliminar duplicados
        count_eliminados = duplicados_a_eliminar.count()
        duplicados_a_eliminar.delete()
        print(f"✅ Eliminados {count_eliminados} duplicados")
    
    print("\n🎉 ¡Duplicados eliminados exitosamente!")
    
    # Verificar que no quedan duplicados
    remaining_duplicates = (Palabra.objects
                           .values('palabra_kichwa', 'categoria')
                           .annotate(count=Count('id'))
                           .filter(count__gt=1))
    
    if remaining_duplicates:
        print(f"⚠️ ADVERTENCIA: Aún quedan {len(remaining_duplicates)} duplicados")
        for dup in remaining_duplicates:
            print(f"  - {dup['palabra_kichwa']} (Categoría: {dup['categoria']})")
    else:
        print("✅ No quedan duplicados en la base de datos")

if __name__ == "__main__":
    find_and_fix_duplicates()
