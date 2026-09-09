import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from apps.diccionario.models import Palabra, Categoria

def verificar_datos():
    """Verificar que los datos estén intactos"""
    print("🔍 Verificando integridad de los datos...")
    
    try:
        # Contar palabras y categorías
        total_palabras = Palabra.objects.count()
        total_categorias = Categoria.objects.count()
        
        print(f"📊 Total de palabras: {total_palabras}")
        print(f"📊 Total de categorías: {total_categorias}")
        
        # Mostrar algunas palabras de ejemplo
        print("📝 Primeras 5 palabras:")
        for palabra in Palabra.objects.all()[:5]:
            print(f"  - {palabra.palabra_kichwa} -> {palabra.traduccion_espanol}")
        
        # Verificar palabras aptas para juegos
        palabras_juegos = Palabra.objects.filter(apta_para_juegos=True).count()
        print(f"🎮 Palabras aptas para juegos: {palabras_juegos}")
        
        print("✅ Verificación completada")
        
    except Exception as e:
        print(f"❌ Error durante verificación: {e}")

if __name__ == "__main__":
    verificar_datos()
