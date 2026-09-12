import json
import logging
import unicodedata
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Case, Count, F, IntegerField, Q, Sum, Value, When
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import (
    Categoria,
    BusquedaPopularDiaria,
    EstadisticaJuego,
    HistorialBusqueda,
    IntentoPalabraJuego,
    Palabra,
    PalabraFavorita,
    ProgresoPalabraJuego,
    RelacionPalabra,
    SesionJuego,
    normalizar_texto_busqueda,
)
from .forms import BusquedaForm, ContactoForm
from .services.relaciones import obtener_palabras_relacionadas
from .services.juegos import (
    categorias_jugables,
    filtros_juego,
    resumen_progreso,
    seleccionar_palabras_juego,
)
from apps.usuarios.models import PerfilUsuario


logger = logging.getLogger(__name__)
LIMITE_SUGERENCIAS = 8
PISTAS_BASE_DIFICULTAD = {'facil': 3, 'medio': 2, 'dificil': 1}


def _normalizar_palabra_tablero(texto):
    """Normaliza una palabra para una grilla: sin puntuación ni tildes editoriales."""
    texto = unicodedata.normalize('NFKD', texto or '')
    return ''.join(caracter for caracter in texto.upper() if caracter.isalpha())


def _pista_de_traduccion(palabra):
    """Devuelve solo una pista que no sea una copia de la respuesta esperada."""
    pista = (palabra.descripcion_juego_espanol or '').strip()
    if _normalizar_palabra_tablero(pista) == _normalizar_palabra_tablero(palabra.traduccion_espanol):
        return ''
    return pista


def _palabras_busqueda(termino='', incluir_campos_ampliados=False):
    """Consulta común, ordenada por relevancia y sin duplicar reglas de búsqueda."""
    palabras = Palabra.objects.select_related('categoria').filter(activa=True)
    termino_normalizado = normalizar_texto_busqueda(termino)
    if not termino_normalizado:
        return palabras

    coincidencias = (
        Q(busqueda_kichwa__icontains=termino_normalizado)
        | Q(busqueda_espanol__icontains=termino_normalizado)
    )
    if incluir_campos_ampliados:
        coincidencias |= Q(busqueda_contenido__icontains=termino_normalizado)

    return palabras.filter(coincidencias).annotate(
        relevancia=Case(
            When(busqueda_kichwa=termino_normalizado, then=Value(1)),
            When(busqueda_espanol=termino_normalizado, then=Value(2)),
            When(busqueda_kichwa__startswith=termino_normalizado, then=Value(3)),
            When(busqueda_espanol__startswith=termino_normalizado, then=Value(4)),
            default=Value(5),
            output_field=IntegerField(),
        )
    )


def _filtro_categoria_efectiva(categoria):
    """Filtra por la clasificación efectiva guardada en cada entrada."""
    return Q(categoria=categoria)


def _agrupar_categorias(categorias):
    grupos = []
    por_clave = {}
    etiquetas = dict(Categoria.GRUPO_CHOICES)
    for categoria in categorias:
        grupo = por_clave.get(categoria.grupo)
        if grupo is None:
            grupo = {
                'clave': categoria.grupo,
                'nombre': etiquetas.get(categoria.grupo, categoria.grupo),
                'categorias': [],
            }
            por_clave[categoria.grupo] = grupo
            grupos.append(grupo)
        grupo['categorias'].append(categoria)
    return grupos


def _ordenar_categorias(queryset):
    """Respeta el orden conceptual de los grupos, no el orden alfabético de sus claves."""
    return queryset.annotate(
        grupo_orden=Case(
            When(grupo='entorno', then=Value(1)),
            When(grupo='personas', then=Value(2)),
            When(grupo='cotidiano', then=Value(3)),
            When(grupo='lengua', then=Value(4)),
            When(grupo='acciones', then=Value(5)),
            default=Value(6),
            output_field=IntegerField(),
        )
    ).order_by('grupo_orden', 'orden', 'nombre')


def _seleccionar_palabras_destacadas(limite=6):
    """Elige entradas útiles y variadas de forma estable, sin azar."""
    candidatas = list(Palabra.objects.select_related('categoria').filter(
        activa=True,
    ).order_by('-veces_vista', '-frecuencia_uso', 'palabra_kichwa', 'pk')[:80])
    seleccionadas = []
    categorias_usadas = set()
    for palabra in candidatas:
        if palabra.categoria_id in categorias_usadas:
            continue
        seleccionadas.append(palabra)
        categorias_usadas.add(palabra.categoria_id)
        if len(seleccionadas) == limite:
            return seleccionadas
    for palabra in candidatas:
        if palabra not in seleccionadas:
            seleccionadas.append(palabra)
        if len(seleccionadas) == limite:
            break
    return seleccionadas

def home(request):
    """Vista principal del diccionario"""
    try:
        palabras_destacadas = _seleccionar_palabras_destacadas()
        categorias = _ordenar_categorias(Categoria.objects.annotate(
            total_palabras=Count('palabras', filter=Q(palabras__activa=True))
        ).filter(total_palabras__gt=0))
        
        # Estadísticas generales
        total_palabras = Palabra.objects.filter(activa=True).count()
        total_categorias = Categoria.objects.count()
        total_busquedas = HistorialBusqueda.objects.count()
        ranking = PerfilUsuario.objects.select_related('usuario').filter(
            participa_ranking=True, puntos_totales__gt=0, usuario__is_active=True,
        ).order_by('-puntos_totales', 'usuario__username')[:5]
        inicio_semana = timezone.localdate() - timedelta(days=6)
        conteos_populares = list(BusquedaPopularDiaria.objects.filter(
            fecha__gte=inicio_semana, palabra__activa=True,
        ).values('palabra_id').annotate(total=Sum('consultas')).order_by(
            '-total', 'palabra__palabra_kichwa', 'palabra_id',
        )[:5])
        palabras_populares = Palabra.objects.in_bulk(
            item['palabra_id'] for item in conteos_populares
        )
        tendencias = [
            {'palabra': palabras_populares[item['palabra_id']], 'consultas': item['total']}
            for item in conteos_populares if item['palabra_id'] in palabras_populares
        ]
        
        context = {
            'palabras_destacadas': palabras_destacadas,
            'categorias': categorias,
            'categorias_destacadas': list(categorias[:6]),
            'total_palabras': total_palabras,
            'total_categorias': total_categorias,
            'total_usuarios': User.objects.count(),
            'total_busquedas': total_busquedas,
            'ranking': ranking,
            'tendencias': tendencias,
        }
        
        return render(request, 'diccionario/home.html', context)
    
    except Exception as e:
        context = {
            'palabras_destacadas': [],
            'categorias': [],
            'total_palabras': 0,
            'total_categorias': 0,
            'total_usuarios': 0,
            'total_busquedas': 0,
            'ranking': [],
            'tendencias': [],
            'error': str(e)
        }
        return render(request, 'diccionario/home.html', context)

def buscar(request):
    """Vista de búsqueda con paginación mejorada"""
    form = BusquedaForm(request.GET)
    termino = ''
    categoria = None
    dificultad = ''
    formulario_valido = form.is_valid()

    # Si un filtro es inválido se conserva el término válido; así un enlace
    # mal formado no transforma una búsqueda puntual en todo el diccionario.
    termino = form.cleaned_data.get('termino', '')
    dificultad = form.cleaned_data.get('dificultad', '')
    if formulario_valido:
        categoria = form.cleaned_data.get('categoria')

    palabras = (
        Palabra.objects.none()
        if 'termino' in form.errors
        else _palabras_busqueda(termino, incluir_campos_ampliados=True)
    )
    if categoria:
        palabras = palabras.filter(_filtro_categoria_efectiva(categoria))
    if dificultad:
        palabras = palabras.filter(dificultad=dificultad)

    if termino:
        palabras = palabras.order_by('relevancia', 'palabra_kichwa', 'id')
    else:
        palabras = palabras.order_by('palabra_kichwa', 'id')
    
    paginator = Paginator(palabras, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    parametros_pagina = request.GET.copy()
    parametros_pagina.pop('page', None)
    categorias = _ordenar_categorias(Categoria.objects.annotate(
        total_palabras=Count('palabras', filter=Q(palabras__activa=True))
    ).filter(total_palabras__gt=0))
    filtros_activos = bool(termino or categoria or dificultad)

    if formulario_valido and termino and 'page' not in request.GET:
        if request.user.is_authenticated:
            HistorialBusqueda.objects.create(
                usuario=request.user,
                termino_buscado=termino,
                resultados_encontrados=paginator.count,
            )
        termino_exacto = normalizar_texto_busqueda(termino)
        coincidencias_exactas = list(palabras.filter(
            Q(busqueda_kichwa=termino_exacto) | Q(busqueda_espanol=termino_exacto)
        ).order_by().values_list('pk', flat=True)[:2])
        if len(coincidencias_exactas) == 1:
            with transaction.atomic():
                conteo, _ = BusquedaPopularDiaria.objects.get_or_create(
                    palabra_id=coincidencias_exactas[0], fecha=timezone.localdate(),
                )
                BusquedaPopularDiaria.objects.filter(pk=conteo.pk).update(consultas=F('consultas') + 1)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_resultados': paginator.count,
        'query': termino,
        'categoria_activa': categoria,
        'dificultad_activa': dificultad,
        'dificultad_activa_label': dict(Palabra.DIFICULTAD_CHOICES).get(dificultad, ''),
        'categorias_agrupadas': _agrupar_categorias(categorias),
        'parametros_pagina': parametros_pagina.urlencode(),
        'filtros_activos': filtros_activos,
    }
    
    return render(request, 'diccionario/buscar.html', context)

@require_http_methods(["GET"])
def buscar_palabras_ajax(request):
    """API endpoint para búsqueda en tiempo real"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'palabras': [], 'total': 0})
    
    try:
        palabras = _palabras_busqueda(query).order_by(
            'relevancia', 'palabra_kichwa', 'id'
        )[:LIMITE_SUGERENCIAS]
        
        resultados = []
        for palabra in palabras:
            resultados.append({
                'id': palabra.pk,
                'url': palabra.get_absolute_url(),
                'palabra_kichwa': palabra.palabra_kichwa,
                'traduccion_espanol': palabra.traduccion_espanol,
                'pronunciacion': getattr(palabra, 'pronunciacion', '') or '',
                'categoria': palabra.categoria.nombre if palabra.categoria else '',
                'dificultad': palabra.get_dificultad_display() if hasattr(palabra, 'get_dificultad_display') else 'Medio',
            })
        
        return JsonResponse({
            'palabras': resultados,
            'total': len(resultados)
        })
    
    except Exception:
        logger.exception('No se pudo ejecutar la búsqueda rápida.')
        return JsonResponse({'error': 'No se pudo completar la búsqueda.'}, status=500)

@require_http_methods(["GET"])
def obtener_sugerencias_ajax(request):
    """API endpoint para sugerencias de búsqueda"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'palabras': [], 'total': 0})
    
    try:
        palabras = _palabras_busqueda(query).order_by(
            'relevancia', 'palabra_kichwa', 'id'
        )[:LIMITE_SUGERENCIAS]
        
        resultados = []
        for palabra in palabras:
            resultados.append({
                'id': palabra.pk,
                'url': palabra.get_absolute_url(),
                'palabra_kichwa': palabra.palabra_kichwa,
                'traduccion_espanol': palabra.traduccion_espanol,
                'pronunciacion': getattr(palabra, 'pronunciacion', '') or '',
                'categoria': palabra.categoria.nombre if palabra.categoria else '',
            })
        
        return JsonResponse({
            'palabras': resultados,
            'total': len(resultados)
        })
    
    except Exception:
        logger.exception('No se pudieron obtener sugerencias de búsqueda.')
        return JsonResponse({'error': 'No se pudieron obtener sugerencias.'}, status=500)

def detalle_palabra(request, pk):
    """Vista de detalle de una palabra"""
    palabra = get_object_or_404(Palabra.objects.select_related('categoria'), pk=pk, activa=True)
    Palabra.objects.filter(pk=palabra.pk).update(veces_vista=F('veces_vista') + 1)
    palabra.refresh_from_db(fields=['veces_vista'])
    es_favorita = request.user.is_authenticated and PalabraFavorita.objects.filter(
        usuario=request.user, palabra=palabra
    ).exists()
    
    palabras_relacionadas = obtener_palabras_relacionadas(palabra)
    
    context = {
        'palabra': palabra,
        'palabras_relacionadas': palabras_relacionadas,
        'es_favorita': es_favorita,
    }
    
    return render(request, 'diccionario/detalle_palabra.html', context)

def categorias(request):
    """Vista de categorías"""
    categorias = _ordenar_categorias(Categoria.objects.annotate(
        total_palabras=Count('palabras', filter=Q(palabras__activa=True))
    ).filter(total_palabras__gt=0))
    
    context = {
        'categorias': categorias,
        'categorias_agrupadas': _agrupar_categorias(categorias),
    }
    
    return render(request, 'diccionario/categorias.html', context)

def palabras_por_categoria(request, categoria_id):
    """Vista de palabras por categoría"""
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    palabras = Palabra.objects.filter(
        activa=True
    ).filter(_filtro_categoria_efectiva(categoria)).order_by('palabra_kichwa')
    
    paginator = Paginator(palabras, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categoria': categoria,
        'page_obj': page_obj,
        'total_palabras': paginator.count,
    }
    
    return render(request, 'diccionario/palabras_por_categoria.html', context)

def acerca_de(request):
    """Vista de información sobre el diccionario"""
    return render(request, 'diccionario/acerca_de.html')

def contacto(request):
    """Vista de contacto"""
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Tu mensaje ha sido enviado correctamente.')
            return redirect('diccionario:contacto')
    else:
        form = ContactoForm()
    
    context = {'form': form}
    return render(request, 'diccionario/contacto.html', context)

JUEGOS_DISPONIBLES = [
    {
        'tipo': 'traduccion', 'etapa': 'Reconocer', 'nombre': 'Traducción guiada',
        'descripcion': 'Reconoce equivalencias en ambos sentidos y aprende a distinguir significados cercanos.',
        'url': 'diccionario:juego_traduccion', 'icono': 'fa-language', 'duracion': '3–5 min',
    },
    {
        'tipo': 'conectar', 'etapa': 'Asociar', 'nombre': 'Conectar significados',
        'descripcion': 'Une cada palabra Kichwa con su significado en español mediante selecciones claras.',
        'url': 'diccionario:juego_conexion', 'icono': 'fa-link', 'duracion': '3–4 min',
    },
    {
        'tipo': 'memoria', 'etapa': 'Recordar', 'nombre': 'Memoria bilingüe',
        'descripcion': 'Recupera parejas del mismo tema y fortalece el recuerdo visual del vocabulario.',
        'url': 'diccionario:juego_memoria', 'icono': 'fa-clone', 'duracion': '4–6 min',
    },
    {
        'tipo': 'completar', 'etapa': 'Producir', 'nombre': 'Completar en Kichwa',
        'descripcion': 'Escribe la palabra completa a partir de su significado y una pista gradual.',
        'url': 'diccionario:juego_completar', 'icono': 'fa-pen', 'duracion': '4–6 min',
    },
    {
        'tipo': 'sopa_letras', 'etapa': 'Explorar', 'nombre': 'Sopa de palabras',
        'descripcion': 'Localiza vocabulario en horizontal, vertical y diagonal, también en sentido inverso.',
        'url': 'diccionario:juego_sopa_letras', 'icono': 'fa-border-all', 'duracion': '5–7 min',
    },
]


def juegos(request):
    """Ruta de práctica y resumen personal de aprendizaje."""
    context = {
        'juegos_disponibles': JUEGOS_DISPONIBLES,
        'categorias_jugables': categorias_jugables(),
        'progreso': resumen_progreso(request.user),
    }
    return render(request, 'diccionario/juegos.html', context)

def mis_favoritas(request):
    """Vista de palabras favoritas del usuario"""
    if not request.user.is_authenticated:
        return redirect('usuarios:login')
    
    try:
        favoritas = PalabraFavorita.objects.filter(
            usuario=request.user
        ).select_related('palabra', 'palabra__categoria').order_by('-fecha_agregada')
        
        paginator = Paginator(favoritas, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'favoritas': page_obj,
            'total_favoritas': favoritas.count(),
        }
    except Exception:
        context = {
            'favoritas': None,
            'total_favoritas': 0,
        }
    
    return render(request, 'diccionario/mis_favoritas.html', context)

@require_http_methods(["POST"])
def toggle_favorita_ajax(request, palabra_id):
    """Toggle favorita via AJAX con manejo de usuarios no autenticados"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'login_required': True,
            'message': 'Debes iniciar sesión para guardar palabras favoritas'
        })
    
    palabra = get_object_or_404(Palabra, pk=palabra_id, activa=True)
    
    try:
        favorita, created = PalabraFavorita.objects.get_or_create(
            usuario=request.user, palabra=palabra
        )
        
        if not created:
            favorita.delete()
            es_favorita = False
            message = f'"{palabra.palabra_kichwa}" quitada de favoritas'
        else:
            es_favorita = True
            message = f'"{palabra.palabra_kichwa}" agregada a favoritas'
        
        return JsonResponse({
            'success': True,
            'es_favorita': es_favorita,
            'message': message,
            'login_required': False
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error al actualizar favoritos',
            'login_required': False
        })

@login_required
@require_http_methods(["POST"])
def agregar_favorita(request, palabra_id):
    """Agregar palabra a favoritas"""
    palabra = get_object_or_404(Palabra, pk=palabra_id, activa=True)
    
    try:
        favorita, created = PalabraFavorita.objects.get_or_create(
            usuario=request.user, palabra=palabra
        )
        
        if created:
            messages.success(request, f'"{palabra.palabra_kichwa}" agregada a favoritas.')
        else:
            messages.info(request, f'"{palabra.palabra_kichwa}" ya está en favoritas.')
    except Exception as e:
        messages.error(request, 'Error al agregar a favoritas.')
    
    return redirect('diccionario:detalle_palabra', pk=palabra_id)

@login_required
@require_http_methods(["POST"])
def quitar_favorita(request, palabra_id):
    """Quitar palabra de favoritas"""
    palabra = get_object_or_404(Palabra, pk=palabra_id)
    
    try:
        favorita = PalabraFavorita.objects.get(usuario=request.user, palabra=palabra)
        favorita.delete()
        messages.success(request, f'"{palabra.palabra_kichwa}" quitada de favoritas.')
    except PalabraFavorita.DoesNotExist:
        messages.error(request, 'La palabra no estaba en favoritas.')
    except Exception:
        messages.error(request, 'Error al quitar de favoritas.')
    
    return redirect('diccionario:detalle_palabra', pk=palabra_id)

# ==================== VISTAS DE JUEGOS ====================

def _datos_palabras_juego(palabras):
    return [
        {
            'id': palabra.id,
            'kichwa': palabra.palabra_kichwa,
            'espanol': palabra.traduccion_espanol,
            'pronunciacion': palabra.pronunciacion or '',
            'pista': _pista_de_traduccion(palabra),
            'tablero': getattr(palabra, 'palabra_tablero', ''),
            'categoria': palabra.categoria.nombre,
        }
        for palabra in palabras
    ]


def _contexto_juego(request, tipo, dificultad_predeterminada, limite, filtro=None):
    dificultad, categoria = filtros_juego(request, dificultad_predeterminada)
    palabras = seleccionar_palabras_juego(
        request.user, dificultad, categoria, limite=limite, filtro=filtro,
    )
    datos = _datos_palabras_juego(palabras)
    meta = next(juego for juego in JUEGOS_DISPONIBLES if juego['tipo'] == tipo)
    sesion = None
    if palabras:
        if not request.session.session_key:
            request.session.create()
        sesion = SesionJuego.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            clave_anonima='' if request.user.is_authenticated else request.session.session_key,
            tipo_juego=tipo,
            dificultad=dificultad,
            categoria=Categoria.objects.filter(slug=categoria).first() if categoria else None,
            palabras_ids=[palabra.id for palabra in palabras],
        )
    return {
        'juego_meta': meta,
        'tipo_juego': tipo,
        'palabras': palabras,
        'palabras_data': datos,
        'palabras_json': json.dumps([
            {
                'id': dato['id'],
                'palabra_kichwa': dato['kichwa'],
                'traduccion_espanol': dato['espanol'],
                'pronunciacion': dato['pronunciacion'],
                'descripcion_juego_espanol': dato['pista'],
                'descripcion_juego_kichwa': '',
            }
            for dato in datos
        ]),
        'dificultad': dificultad,
        'categoria_seleccionada': categoria,
        'categorias_jugables': categorias_jugables(),
        'total_palabras': len(palabras),
        'sesion_id': str(sesion.id) if sesion else '',
        'pistas_base': PISTAS_BASE_DIFICULTAD[dificultad],
        'pistas_extra_disponibles': (
            PerfilUsuario.objects.filter(usuario=request.user).values_list('pistas_extra_disponibles', flat=True).first() or 0
            if request.user.is_authenticated else 0
        ),
    }

def juego_traduccion(request):
    """Reconocimiento bilingüe con distractores del corpus filtrado."""
    try:
        return render(request, 'diccionario/juegos/traduccion.html', _contexto_juego(request, 'traduccion', 'medio', 12))
    except Exception as e:
        messages.error(request, f'Error al cargar el juego: {str(e)}')
        return redirect('diccionario:juegos')

def juego_completar(request):
    """Producción escrita de vocabulario Kichwa."""
    try:
        return render(request, 'diccionario/juegos/completar.html', _contexto_juego(request, 'completar', 'facil', 10))
    except Exception as e:
        messages.error(request, f'Error al cargar el juego: {str(e)}')
        return redirect('diccionario:juegos')

def juego_memoria(request):
    """Memoria bilingüe con parejas del mismo filtro."""
    try:
        return render(request, 'diccionario/juegos/memoria.html', _contexto_juego(request, 'memoria', 'medio', 6))
    except Exception as e:
        messages.error(request, f'Error al cargar el juego: {str(e)}')
        return redirect('diccionario:juegos')

def juego_conectar(request):
    """Asociación accesible por selección, también en pantallas táctiles."""
    try:
        return render(request, 'diccionario/juegos/conectar.html', _contexto_juego(request, 'conectar', 'medio', 6))
    except Exception as e:
        messages.error(request, f'Error al cargar el juego: {str(e)}')
        return redirect('diccionario:juegos')

def juego_sopa_letras(request):
    """Exploración visual con palabras que caben en el tablero."""
    try:
        def cabe_en_tablero(palabra):
            palabra.palabra_tablero = _normalizar_palabra_tablero(palabra.palabra_kichwa)
            return 2 <= len(palabra.palabra_tablero) <= 12

        return render(request, 'diccionario/juegos/sopa_letras.html', _contexto_juego(
            request, 'sopa_letras', 'medio', 6, filtro=cabe_en_tablero,
        ))
    except Exception as e:
        messages.error(request, f'Error al cargar el juego: {str(e)}')
        return redirect('diccionario:juegos')

API_MAX_CANTIDAD_JUEGO = 50


def _respuesta_error(mensaje, estado=400):
    return JsonResponse({'success': False, 'error': mensaje}, status=estado)


def _entero_no_negativo(datos, campo, maximo, default=None):
    valor = datos.get(campo, default)
    if isinstance(valor, bool) or valor is None:
        raise ValueError
    try:
        entero = int(valor)
    except (TypeError, ValueError) as error:
        raise ValueError from error
    if entero < 0 or entero > maximo:
        raise ValueError
    return entero


@require_http_methods(['POST'])
def usar_pista_juego(request):
    """Concede una pista por palabra y descuenta extras una sola vez por cuenta."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _respuesta_error('El cuerpo de la solicitud debe ser JSON válido.')
    if not isinstance(data, dict):
        return _respuesta_error('El cuerpo de la solicitud debe ser un objeto JSON.')
    try:
        palabra_id = _entero_no_negativo(data, 'palabra_id', 10_000_000)
    except ValueError:
        return _respuesta_error('La palabra no es válida.')

    with transaction.atomic():
        try:
            sesion = SesionJuego.objects.select_for_update().get(id=data.get('sesion_id'))
        except (SesionJuego.DoesNotExist, ValidationError, ValueError, TypeError):
            return _respuesta_error('La sesión de juego no es válida.', 404)
        if request.user.is_authenticated:
            autorizada = sesion.usuario_id == request.user.id
        else:
            autorizada = sesion.usuario_id is None and sesion.clave_anonima == request.session.session_key
        if not autorizada:
            return _respuesta_error('Esta sesión pertenece a otra persona.', 403)
        if sesion.finalizada_en:
            return _respuesta_error('La sesión ya terminó.', 409)
        if palabra_id not in sesion.palabras_ids:
            return _respuesta_error('La palabra no pertenece a esta sesión.', 403)
        if palabra_id in sesion.pistas_palabras_ids:
            return _respuesta_error('Ya usaste una pista para esta palabra.', 409)
        if sesion.intentos.filter(palabra_id=palabra_id, correcta=True).exists():
            return _respuesta_error('Esta palabra ya fue resuelta.', 409)

        base = PISTAS_BASE_DIFICULTAD[sesion.dificultad]
        usa_extra = sesion.pistas_usadas >= base
        extras_restantes = 0
        if usa_extra:
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'login_required': True,
                    'message': 'Agotaste las pistas de esta partida. Inicia sesión o crea una cuenta para disponer de dos pistas extra una sola vez.',
                }, status=403)
            PerfilUsuario.objects.get_or_create(usuario=request.user)
            descontadas = PerfilUsuario.objects.filter(
                usuario=request.user, pistas_extra_disponibles__gt=0,
            ).update(pistas_extra_disponibles=F('pistas_extra_disponibles') - 1)
            if not descontadas:
                return _respuesta_error('Ya usaste las dos pistas extra de tu cuenta.', 403)
        if request.user.is_authenticated:
            extras_restantes = PerfilUsuario.objects.get(usuario=request.user).pistas_extra_disponibles
        sesion.pistas_usadas += 1
        sesion.pistas_palabras_ids = [*sesion.pistas_palabras_ids, palabra_id]
        sesion.save(update_fields=['pistas_usadas', 'pistas_palabras_ids'])

    return JsonResponse({
        'success': True,
        'origen': 'extra' if usa_extra else 'partida',
        'pistas_base_restantes': max(base - sesion.pistas_usadas, 0),
        'pistas_extra_restantes': extras_restantes,
    })


@require_http_methods(['POST'])
def guardar_estadistica_juego(request):
    """Cierra una sesión y deriva el resultado desde intentos validados."""
    if not request.user.is_authenticated:
        return _respuesta_error('Debes iniciar sesión para guardar estadísticas.', 401)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _respuesta_error('El cuerpo de la solicitud debe ser JSON válido.')
    if not isinstance(data, dict):
        return _respuesta_error('El cuerpo de la solicitud debe ser un objeto JSON.')

    sesion_id = data.get('sesion_id')
    with transaction.atomic():
        try:
            sesion = SesionJuego.objects.select_for_update().get(id=sesion_id, usuario=request.user)
        except (SesionJuego.DoesNotExist, ValidationError, ValueError, TypeError):
            return _respuesta_error('La sesión de juego no es válida.', 404)
        if sesion.estadistica_id:
            return JsonResponse({'success': True, 'message': 'La sesión ya estaba guardada.'})

        ids_correctos = set(sesion.intentos.filter(correcta=True).values_list('palabra_id', flat=True))
        correctas = len(ids_correctos.intersection(set(sesion.palabras_ids)))
        totales = len(sesion.palabras_ids)
        tiempo_jugado = min(max(int((timezone.now() - sesion.iniciada_en).total_seconds()), 0), 86_400)
        estadistica = EstadisticaJuego.objects.create(
            usuario=request.user,
            tipo_juego=sesion.tipo_juego,
            puntuacion=correctas * 10,
            respuestas_correctas=correctas,
            respuestas_totales=totales,
            dificultad=sesion.dificultad,
            tiempo_jugado=tiempo_jugado,
        )
        sesion.estadistica = estadistica
        sesion.finalizada_en = timezone.now()
        sesion.save(update_fields=['estadistica', 'finalizada_en'])
    return JsonResponse({
        'success': True,
        'message': 'Estadísticas guardadas correctamente',
        'puntuacion': estadistica.puntuacion,
        'respuestas_correctas': correctas,
        'respuestas_totales': totales,
    }, status=201)


@require_http_methods(['POST'])
def registrar_respuesta_juego(request):
    """Valida una respuesta en el servidor y conserva progreso por palabra."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _respuesta_error('El cuerpo de la solicitud debe ser JSON válido.')
    if not isinstance(data, dict):
        return _respuesta_error('El cuerpo de la solicitud debe ser un objeto JSON.')

    try:
        sesion = SesionJuego.objects.get(id=data.get('sesion_id'))
    except (SesionJuego.DoesNotExist, ValidationError, ValueError, TypeError):
        return _respuesta_error('La sesión de juego no es válida.', 404)
    if request.user.is_authenticated:
        sesion_autorizada = sesion.usuario_id == request.user.id
    else:
        sesion_autorizada = sesion.usuario_id is None and sesion.clave_anonima == request.session.session_key
    if not sesion_autorizada:
        return _respuesta_error('Esta sesión pertenece a otra persona.', 403)
    if sesion.finalizada_en:
        return _respuesta_error('La sesión ya terminó.', 409)

    tipo = data.get('tipo_juego')
    if tipo != sesion.tipo_juego:
        return _respuesta_error('El tipo de juego no coincide con la sesión.')
    try:
        palabra_id = _entero_no_negativo(data, 'palabra_id', 10_000_000)
    except ValueError:
        return _respuesta_error('La palabra no es válida.')
    palabra = get_object_or_404(Palabra, pk=palabra_id, activa=True, apta_para_juegos=True)
    if palabra.id not in sesion.palabras_ids:
        return _respuesta_error('La palabra no pertenece a esta sesión.', 403)

    if tipo == 'completar':
        correcta = normalizar_texto_busqueda(data.get('respuesta', '')) == normalizar_texto_busqueda(palabra.palabra_kichwa)
    else:
        try:
            respuesta_id = _entero_no_negativo(data, 'respuesta_id', 10_000_000)
        except ValueError:
            return _respuesta_error('La respuesta no es válida.')
        correcta = respuesta_id == palabra.id

    progreso = None
    puntos_ganados = 0
    if request.user.is_authenticated:
        with transaction.atomic():
            IntentoPalabraJuego.objects.create(sesion=sesion, palabra=palabra, correcta=correcta)
            progreso, _ = ProgresoPalabraJuego.objects.select_for_update().get_or_create(
                usuario=request.user, palabra=palabra,
            )
            primer_acierto = correcta and progreso.respuestas_correctas == 0
            progreso.registrar_respuesta(correcta)
            if primer_acierto:
                PerfilUsuario.objects.get_or_create(usuario=request.user)
                PerfilUsuario.objects.filter(usuario=request.user).update(
                    puntos_totales=F('puntos_totales') + 10,
                )
                puntos_ganados = 10

    if tipo == 'completar' or data.get('direccion') == 'espanol_kichwa':
        respuesta_correcta = palabra.palabra_kichwa
    else:
        respuesta_correcta = palabra.traduccion_espanol

    return JsonResponse({
        'success': True,
        'correcta': correcta,
        'respuesta_correcta': respuesta_correcta,
        'progreso_guardado': progreso is not None,
        'dominio': progreso.dominio if progreso else None,
        'racha_palabra': progreso.racha_actual if progreso else 0,
        'puntos_ganados': puntos_ganados,
    })


@require_http_methods(['GET'])
def obtener_palabras_juego(request):
    """API de palabras previamente seleccionadas para juegos."""
    tipo_juego = request.GET.get('tipo', 'traduccion')
    dificultad = request.GET.get('dificultad', 'medio')
    if tipo_juego not in {valor for valor, _ in EstadisticaJuego.TIPO_JUEGO_CHOICES}:
        return _respuesta_error('El tipo de juego no es válido.')
    if dificultad not in {valor for valor, _ in Palabra.DIFICULTAD_CHOICES}:
        return _respuesta_error('La dificultad no es válida.')
    try:
        cantidad = _entero_no_negativo(request.GET, 'cantidad', API_MAX_CANTIDAD_JUEGO, 10)
    except ValueError:
        return _respuesta_error(f'cantidad debe ser un entero entre 0 y {API_MAX_CANTIDAD_JUEGO}.')

    categoria = request.GET.get('categoria', '').strip()
    palabras = seleccionar_palabras_juego(request.user, dificultad, categoria, cantidad)
    return JsonResponse({'palabras': [
        {
            'id': palabra.id,
            'palabra_kichwa': palabra.palabra_kichwa,
            'traduccion_espanol': palabra.traduccion_espanol,
            'pronunciacion': palabra.pronunciacion or '',
            'descripcion_juego_espanol': _pista_de_traduccion(palabra),
            'descripcion_juego_kichwa': palabra.descripcion_juego_kichwa or '',
        }
        for palabra in palabras
    ]})


@require_http_methods(['GET'])
def api_palabras(request):
    """API pública, paginada y de solo lectura del diccionario."""
    consulta = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    try:
        pagina = _entero_no_negativo(request.GET, 'pagina', 10_000, 1)
        tamano = _entero_no_negativo(request.GET, 'tamano', 50, 20)
        if pagina == 0 or tamano == 0:
            raise ValueError
    except ValueError:
        return _respuesta_error('pagina y tamano deben estar entre 1 y 50.')

    palabras = _palabras_busqueda(consulta)
    if categoria:
        palabras = palabras.filter(categoria__slug=categoria)
    orden = ('relevancia', 'palabra_kichwa', 'id') if consulta else ('palabra_kichwa', 'id')
    paginador = Paginator(palabras.order_by(*orden), tamano)
    pagina_obj = paginador.get_page(pagina)
    return JsonResponse({
        'count': paginador.count,
        'pagina': pagina_obj.number,
        'paginas': paginador.num_pages,
        'resultados': [
            {
                'id': palabra.pk,
                'url': palabra.get_absolute_url(),
                'kichwa': palabra.palabra_kichwa,
                'espanol': palabra.traduccion_espanol,
                'categoria': palabra.categoria.slug,
                'audio_disponible': bool(palabra.audio),
            }
            for palabra in pagina_obj
        ],
    })


@require_http_methods(['GET'])
def api_detalle_palabra(request, pk):
    palabra = get_object_or_404(Palabra.objects.select_related('categoria'), pk=pk, activa=True)
    return JsonResponse({
        'id': palabra.pk,
        'url': palabra.get_absolute_url(),
        'kichwa': palabra.palabra_kichwa,
        'espanol': palabra.traduccion_espanol,
        'definicion': palabra.definicion or '',
        'pronunciacion': palabra.pronunciacion or '',
        'categoria': {'nombre': palabra.categoria.nombre, 'slug': palabra.categoria.slug},
        'audio': palabra.audio.url if palabra.audio else None,
    })
