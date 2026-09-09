import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from apps.diccionario.models import Palabra

def marcar_palabras_para_juegos():
    """Marcar todas las palabras como aptas para juegos"""
    print("🎮 Marcando palabras como aptas para juegos...")
    
    try:
        # Actualizar todas las palabras
        updated = Palabra.objects.all().update(
            apta_para_juegos=True,
            dificultad_juego='medio'
        )
        
        print(f"✅ {updated} palabras marcadas como aptas para juegos")
        
        # Verificar el resultado
        total_aptas = Palabra.objects.filter(apta_para_juegos=True).count()
        print(f"📊 Total de palabras aptas para juegos: {total_aptas}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    marcar_palabras_para_juegos()
