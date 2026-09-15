from django.db.models import Case, IntegerField, OuterRef, Subquery, Sum, Value, When
from django.utils.translation import get_language

from ..models import Categoria, Palabra, ProgresoPalabraJuego, normalizar_texto_busqueda


DIFICULTADES_VALIDAS = {valor for valor, _ in Palabra.DIFICULTAD_CHOICES}
SEPARADORES_AMBIGUOS = ',;:/[]()\n\r'


def entrada_jugable(palabra):
    """Acepta pares bilingües breves; descarta listas de variantes y glosas extensas."""
    kichwa = (palabra.palabra_kichwa or '').strip()
    equivalencia = (palabra.traduccion_localizada or '').strip()
    return (
        bool(normalizar_texto_busqueda(kichwa) and normalizar_texto_busqueda(equivalencia))
        and not any(separador in kichwa or separador in equivalencia for separador in SEPARADORES_AMBIGUOS)
        and len(kichwa) <= 48
        and len(equivalencia) <= 65
        and len(kichwa.split()) <= 3
        and len(equivalencia.split()) <= 5
    )


def filtros_juego(request, dificultad_predeterminada='medio'):
    dificultad = request.GET.get('dificultad', dificultad_predeterminada).strip().lower()
    if dificultad not in DIFICULTADES_VALIDAS:
        dificultad = dificultad_predeterminada
    categoria = request.GET.get('categoria', '').strip()
    return dificultad, categoria


def categorias_jugables(requiere_audio=False):
    candidatas = Palabra.objects.filter(activa=True).only(
        'categoria_id', 'palabra_kichwa', 'traduccion_espanol',
        'traduccion_ingles', 'estado_revision_ingles',
    )
    if requiere_audio:
        candidatas = candidatas.exclude(audio='').exclude(audio__isnull=True)
    if get_language() == 'en':
        candidatas = candidatas.filter(estado_revision_ingles='validada').exclude(traduccion_ingles='')
    categorias_ids = {palabra.categoria_id for palabra in candidatas if entrada_jugable(palabra)}
    return Categoria.objects.filter(pk__in=categorias_ids).order_by('grupo', 'orden', 'nombre')


def _corpus_jugable(dificultad, categoria_slug=''):
    palabras = Palabra.objects.select_related('categoria').filter(
        activa=True,
        dificultad=dificultad,
    ).exclude(
        palabra_kichwa=''
    ).exclude(
        traduccion_espanol=''
    )
    if categoria_slug:
        palabras = palabras.filter(categoria__slug=categoria_slug)
    if get_language() == 'en':
        palabras = palabras.filter(estado_revision_ingles='validada').exclude(traduccion_ingles='')
    return palabras


def seleccionar_palabras_juego(usuario, dificultad, categoria_slug='', limite=10, filtro=None, requiere_audio=False):
    """Prioriza vocabulario no visto o en aprendizaje sin mezclar filtros."""
    palabras = _corpus_jugable(dificultad, categoria_slug)
    if requiere_audio:
        palabras = palabras.exclude(audio='').exclude(audio__isnull=True)
    if getattr(usuario, 'is_authenticated', False):
        dominio_usuario = ProgresoPalabraJuego.objects.filter(
            usuario=usuario, palabra=OuterRef('pk'),
        ).values('dominio')[:1]
        palabras = palabras.annotate(
            dominio_usuario=Subquery(dominio_usuario),
            prioridad=Case(
                When(dominio_usuario='aprendiendo', then=Value(1)),
                When(dominio_usuario='practicando', then=Value(2)),
                When(dominio_usuario='dominada', then=Value(3)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('prioridad', '-frecuencia_uso', 'categoria__orden', 'palabra_kichwa', 'id')
    else:
        palabras = palabras.order_by('-frecuencia_uso', 'categoria__orden', 'palabra_kichwa', 'id')

    palabras = [
        palabra for palabra in palabras
        if entrada_jugable(palabra) and (filtro is None or filtro(palabra))
    ]

    seleccion = []
    vistos_kichwa = set()
    vistos_espanol = set()
    for palabra in palabras:
        kichwa = normalizar_texto_busqueda(palabra.palabra_kichwa)
        espanol = normalizar_texto_busqueda(palabra.traduccion_localizada)
        if not kichwa or not espanol or kichwa in vistos_kichwa or espanol in vistos_espanol:
            continue
        seleccion.append(palabra)
        vistos_kichwa.add(kichwa)
        vistos_espanol.add(espanol)
        if len(seleccion) >= limite:
            break
    return seleccion


def resumen_progreso(usuario):
    if not getattr(usuario, 'is_authenticated', False):
        return {'practicadas': 0, 'dominadas': 0, 'precision': 0}
    progresos = ProgresoPalabraJuego.objects.filter(usuario=usuario)
    agregados = progresos.aggregate(
        intentos=Sum('intentos'),
        correctas=Sum('respuestas_correctas'),
    )
    intentos = agregados['intentos'] or 0
    return {
        'practicadas': progresos.count(),
        'dominadas': progresos.filter(dominio='dominada').count(),
        'precision': round(((agregados['correctas'] or 0) / intentos) * 100) if intentos else 0,
    }
