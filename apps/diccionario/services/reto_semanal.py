"""Reto semanal personal basado en respuestas validadas por los juegos."""

from datetime import datetime, time, timedelta

from django.utils import timezone
from django.utils.translation import gettext as _

from ..models import IntentoPalabraJuego


JUEGOS_SEMANALES = (
    ('traduccion', 'Traducción guiada', 'diccionario:juego_traduccion'),
    ('completar', 'Completar en Kichwa', 'diccionario:juego_completar'),
    ('memoria', 'Memoria bilingüe', 'diccionario:juego_memoria'),
    ('conectar', 'Conectar significados', 'diccionario:juego_conexion'),
    ('sopa_letras', 'Sopa de palabras', 'diccionario:juego_sopa_letras'),
)
META_PALABRAS = 5


def reto_semanal(usuario, fecha=None):
    """Cuenta palabras distintas acertadas de lunes a domingo en la modalidad elegida."""
    hoy = fecha or timezone.localdate()
    inicio = hoy - timedelta(days=hoy.weekday())
    fin_exclusivo = inicio + timedelta(days=7)
    tipo, modalidad, url = JUEGOS_SEMANALES[(inicio.toordinal() // 7) % len(JUEGOS_SEMANALES)]
    avance = None
    if getattr(usuario, 'is_authenticated', False):
        zona = timezone.get_current_timezone()
        desde = timezone.make_aware(datetime.combine(inicio, time.min), zona)
        hasta = timezone.make_aware(datetime.combine(fin_exclusivo, time.min), zona)
        avance = IntentoPalabraJuego.objects.filter(
            sesion__usuario=usuario,
            sesion__tipo_juego=tipo,
            correcta=True,
            fecha__gte=desde,
            fecha__lt=hasta,
        ).order_by().values('palabra_id').distinct().count()

    return {
        'inicio': inicio,
        'fin': fin_exclusivo - timedelta(days=1),
        'modalidad': _(modalidad),
        'tipo': tipo,
        'url': url,
        'meta': META_PALABRAS,
        'avance': min(avance, META_PALABRAS) if avance is not None else None,
        'completado': avance is not None and avance >= META_PALABRAS,
    }
