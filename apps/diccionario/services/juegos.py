from django.db.models import Case, IntegerField, OuterRef, Subquery, Sum, Value, When

from ..models import Categoria, Palabra, ProgresoPalabraJuego, normalizar_texto_busqueda


DIFICULTADES_VALIDAS = {valor for valor, _ in Palabra.DIFICULTAD_CHOICES}


def filtros_juego(request, dificultad_predeterminada='medio'):
    dificultad = request.GET.get('dificultad', dificultad_predeterminada).strip().lower()
    if dificultad not in DIFICULTADES_VALIDAS:
        dificultad = dificultad_predeterminada
    categoria = request.GET.get('categoria', '').strip()
    return dificultad, categoria


def categorias_jugables():
    return Categoria.objects.filter(
        palabras__activa=True,
        palabras__apta_para_juegos=True,
    ).distinct().order_by('grupo', 'orden', 'nombre')


def _corpus_jugable(dificultad, categoria_slug=''):
    palabras = Palabra.objects.select_related('categoria').filter(
        activa=True,
        apta_para_juegos=True,
        dificultad_juego=dificultad,
    ).exclude(
        palabra_kichwa=''
    ).exclude(
        traduccion_espanol=''
    )
    if categoria_slug:
        palabras = palabras.filter(categoria__slug=categoria_slug)
    return palabras


def seleccionar_palabras_juego(usuario, dificultad, categoria_slug='', limite=10, filtro=None):
    """Prioriza vocabulario no visto o en aprendizaje sin mezclar filtros."""
    palabras = _corpus_jugable(dificultad, categoria_slug)
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

    if filtro is not None:
        palabras = [palabra for palabra in palabras if filtro(palabra)]
    else:
        palabras = list(palabras)

    seleccion = []
    vistos_kichwa = set()
    vistos_espanol = set()
    for palabra in palabras:
        kichwa = normalizar_texto_busqueda(palabra.palabra_kichwa)
        espanol = normalizar_texto_busqueda(palabra.traduccion_espanol)
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
