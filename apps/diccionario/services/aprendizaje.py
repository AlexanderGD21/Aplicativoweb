"""Niveles y objetivos privados calculados desde la práctica ya guardada."""

from ..models import EstadisticaJuego, ProgresoPalabraJuego


PUNTOS_POR_NIVEL = 100


def nivel_practica(puntos_totales):
    """El nivel de práctica no representa el dominio declarado del Kichwa."""
    nivel, puntos_en_nivel = divmod(max(0, puntos_totales), PUNTOS_POR_NIVEL)
    return {
        'numero': nivel + 1,
        'proximo_numero': nivel + 2,
        'puntos_en_nivel': puntos_en_nivel,
        'meta': PUNTOS_POR_NIVEL,
        'faltantes': PUNTOS_POR_NIVEL - puntos_en_nivel,
        'porcentaje': round(puntos_en_nivel / PUNTOS_POR_NIVEL * 100),
    }


def misiones_aprendizaje(usuario):
    """Los objetivos usan contadores monotónicos y no otorgan puntos duplicados."""
    aciertos_distintos = ProgresoPalabraJuego.objects.filter(
        usuario=usuario, respuestas_correctas__gt=0,
    ).count()
    racha_lograda = ProgresoPalabraJuego.objects.filter(
        usuario=usuario, mejor_racha__gte=3,
    ).exists()
    partidas_terminadas = EstadisticaJuego.objects.filter(usuario=usuario).count()
    objetivos = (
        ('Primer acierto', 'Acertar una palabra nueva', aciertos_distintos, 1),
        ('Cinco palabras', 'Acertar cinco palabras distintas', aciertos_distintos, 5),
        ('Tres partidas', 'Terminar tres partidas', partidas_terminadas, 3),
        ('Tres seguidas', 'Lograr tres aciertos seguidos en una palabra', int(racha_lograda), 1),
    )
    return [
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'avance': min(actual, meta),
            'meta': meta,
            'porcentaje': min(100, round(actual / meta * 100)),
            'completada': actual >= meta,
        }
        for nombre, descripcion, actual, meta in objetivos
    ]
