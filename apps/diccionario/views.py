import json
import logging
import unicodedata
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Case, Count, F, IntegerField, Q, Value, When
from django.views.decorators.http import require_http_methods
from .models import Palabra, Categoria, PalabraFavorita, HistorialBusqueda, EstadisticaJuego, RelacionPalabra
from .forms import BusquedaForm, ContactoForm


logger = logging.getLogger(__name__)
LIMITE_SUGERENCIAS = 8


def _consulta_palabras_para_juego(dificultad):
    """Devuelve el corpus jugable, sin registros incompletos ni inactivos."""
    palabras = Palabra.objects.filter(
        activa=True,
        apta_para_juegos=True,
    ).exclude(
        palabra_kichwa=''
    ).exclude(
        traduccion_espanol=''
    )

    if dificultad:
        por_dificultad = palabras.filter(dificultad_juego=dificultad)
        if por_dificultad.exists():
            palabras = por_dificultad

    return palabras


def _muestra_palabras_para_juego(dificultad, limite):
    """Selecciona una muestra aleatoria pequeña del corpus apto para juegos."""
    return list(_consulta_palabras_para_juego(dificultad).order_by('?')[:limite])


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
    if not termino:
        return palabras

    coincidencias = Q(palabra_kichwa__icontains=termino) | Q(traduccion_espanol__icontains=termino)
    if incluir_campos_ampliados:
        coincidencias |= Q(definicion__icontains=termino) | Q(pronunciacion__icontains=termino)

    return palabras.filter(coincidencias).annotate(
        relevancia=Case(
            When(palabra_kichwa__iexact=termino, then=Value(1)),
            When(traduccion_espanol__iexact=termino, then=Value(2)),
            When(palabra_kichwa__istartswith=termino, then=Value(3)),
            When(traduccion_espanol__istartswith=termino, then=Value(4)),
            default=Value(5),
            output_field=IntegerField(),
        )
    )


def _filtro_categoria_efectiva(categoria):
    """Incluye la clasificación revisada y la propuesta pendiente de curación.

    La categoría General representa las entradas que aún no tienen una
    propuesta. Así no se mezclan con las palabras que ya pueden explorarse por
    una categoría concreta, sin promover automáticamente una sugerencia a dato
    lingüístico definitivo.
    """
    if categoria.nombre == 'General':
        return Q(categoria=categoria, categoria_propuesta__isnull=True)
    return Q(categoria=categoria) | Q(categoria_propuesta=categoria)


def _conteos_categoria_efectiva():
    """Cuenta una sola categoría visible por palabra en una consulta ligera."""
    conteos = {}
    palabras = Palabra.objects.filter(activa=True).values_list(
        'categoria_id', 'categoria_propuesta_id'
    )
    for categoria_id, propuesta_id in palabras.iterator(chunk_size=1000):
        categoria_visible_id = propuesta_id or categoria_id
        conteos[categoria_visible_id] = conteos.get(categoria_visible_id, 0) + 1
    return conteos

def home(request):
    """Vista principal del diccionario"""
    try:
        # Obtener palabras destacadas (más vistas o favoritas) - CAMBIADO A 6
        palabras_destacadas = Palabra.objects.select_related('categoria').filter(
            activa=True
        ).order_by('-veces_vista', '-fecha_creacion')[:6]
        
        # Si no hay suficientes palabras con vistas, obtener palabras aleatorias
        if palabras_destacadas.count() < 6:
            palabras_destacadas = Palabra.objects.select_related('categoria').filter(
                activa=True
            ).order_by('?')[:6]
        
        # Obtener categorías para los filtros
        categorias = Categoria.objects.all().order_by('nombre')
        
        # Estadísticas generales
        total_palabras = Palabra.objects.filter(activa=True).count()
        total_categorias = Categoria.objects.count()
        total_busquedas = HistorialBusqueda.objects.count()
        
        context = {
            'palabras_destacadas': palabras_destacadas,
            'categorias': categorias,
            'total_palabras': total_palabras,
            'total_categorias': total_categorias,
            'total_usuarios': User.objects.count(),
            'total_busquedas': total_busquedas,
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
            'error': str(e)
        }
        return render(request, 'diccionario/home.html', context)

def buscar(request):
    """Vista de búsqueda con paginación mejorada"""
    form = BusquedaForm(request.GET)
    termino = ''
    categoria = None
    dificultad = ''
    nivel_pronunciacion = ''
    formulario_valido = form.is_valid()

    # Si un filtro es inválido se conserva el término válido; así un enlace
    # mal formado no transforma una búsqueda puntual en todo el diccionario.
    termino = form.cleaned_data.get('termino', '')
    dificultad = form.cleaned_data.get('dificultad', '')
    nivel_pronunciacion = form.cleaned_data.get('nivel_pronunciacion', '')
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
    if nivel_pronunciacion:
        palabras = palabras.filter(nivel_dificultad=nivel_pronunciacion)

    if termino:
        palabras = palabras.order_by('relevancia', 'palabra_kichwa', 'id')
    else:
        palabras = palabras.order_by('palabra_kichwa', 'id')
    
    paginator = Paginator(palabras, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if formulario_valido and termino and request.user.is_authenticated:
        HistorialBusqueda.objects.create(
            usuario=request.user,
            termino_buscado=termino,
            resultados_encontrados=paginator.count,
        )
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_resultados': paginator.count,
        'query': termino,
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
    
    palabras_relacionadas = []
    relacionadas_explicitas = RelacionPalabra.objects.filter(origen=palabra).select_related('destino')
    palabras_relacionadas = [relacion.destino for relacion in relacionadas_explicitas if relacion.destino.activa]
    if palabra.categoria:
        sugeridas_categoria = Palabra.objects.filter(
            categoria=palabra.categoria,
            activa=True
        ).exclude(pk__in=[palabra.pk, *[item.pk for item in palabras_relacionadas]])[:4 - len(palabras_relacionadas)]
        palabras_relacionadas.extend(sugeridas_categoria)
    
    context = {
        'palabra': palabra,
        'palabras_relacionadas': palabras_relacionadas,
        'es_favorita': es_favorita,
    }
    
    return render(request, 'diccionario/detalle_palabra.html', context)

def categorias(request):
    """Vista de categorías"""
    categorias = Categoria.objects.order_by('nombre')
    conteos = _conteos_categoria_efectiva()
    for categoria in categorias:
        categoria.total_palabras = conteos.get(categoria.pk, 0)
    
    context = {
        'categorias': categorias,
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

def juegos(request):
    """Vista principal de juegos"""
    context = {
        'juegos_disponibles': [
            {
                'nombre': 'Traducción',
                'descripcion': 'Traduce palabras del kichwa al español y viceversa',
                'url': 'diccionario:juego_traduccion',
                'icono': '🔄'
            },
            {
                'nombre': 'Completar',
                'descripcion': 'Completa las palabras con las letras faltantes',
                'url': 'diccionario:juego_completar',
                'icono': '✏️'
            },
            {
                'nombre': 'Memoria',
                'descripcion': 'Encuentra las parejas de palabras en kichwa y español',
                'url': 'diccionario:juego_memoria',
                'icono': '🧠'
            },
            {
                'nombre': 'Conexión',
                'descripcion': 'Conecta las palabras en kichwa con su traducción',
                'url': 'diccionario:juego_conexion',
                'icono': '🔗'
            },
            {
                'nombre': 'Sopa de Letras',
                'descripcion': 'Encuentra las palabras ocultas en la sopa de letras',
                'url': 'diccionario:juego_sopa_letras',
                'icono': '🔍'
            }
        ]
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

def juego_traduccion(request):
    """Juego de traducción"""
    try:
        dificultad = request.GET.get('dificultad', 'medio')
        palabras = _muestra_palabras_para_juego(dificultad, 15)
        
        palabras_data = []
        for palabra in palabras:
            palabras_data.append({
                'id': palabra.id,
                'palabra_kichwa': palabra.palabra_kichwa,
                'traduccion_espanol': palabra.traduccion_espanol,
                'pronunciacion': getattr(palabra, 'pronunciacion', '') or '',
                # Una pista opcional no debe revelar la traducción correcta.
                'descripcion_juego_espanol': _pista_de_traduccion(palabra),
                'descripcion_juego_kichwa': palabra.descripcion_juego_kichwa or '',
            })
        
        context = {
            'palabras': palabras,
            'palabras_json': json.dumps(palabras_data),
            'dificultad': dificultad,
            'total_palabras': len(palabras),
        }
        return render(request, 'diccionario/juegos/traduccion.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar el juego: {str(e)}')
        return redirect('diccionario:juegos')

def juego_completar(request):
    """Juego de completar palabras"""
    try:
        dificultad = request.GET.get('dificultad', 'facil')
        
        palabras = _muestra_palabras_para_juego(dificultad, 15)
        
        context = {
            'palabras': palabras,
            'dificultad': dificultad,
        }
        return render(request, 'diccionario/juegos/completar.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar el juego: {str(e)}')
        return redirect('diccionario:juegos')

def juego_memoria(request):
    """Juego de memoria"""
    try:
        dificultad = request.GET.get('dificultad', 'medio')
        
        palabras = _muestra_palabras_para_juego(dificultad, 15)
        
        # Preparar datos para el juego de memoria
        cartas_data = []
        for palabra in palabras:
            cartas_data.append({
                'texto': palabra.palabra_kichwa,
                'traduccion': palabra.traduccion_espanol,
                'id': palabra.id,
                'pareja': palabra.id
            })
        
        context = {
            'palabras': palabras,
            'cartas_json': json.dumps(cartas_data),
            'dificultad': dificultad,
        }
        return render(request, 'diccionario/juegos/memoria.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar el juego: {str(e)}')
        return redirect('diccionario:juegos')

def juego_conectar(request):
    """Juego de conectar palabras"""
    try:
        dificultad = request.GET.get('dificultad', 'medio')
        
        palabras = _muestra_palabras_para_juego(dificultad, 6)
        
        context = {
            'palabras': palabras,
            'dificultad': dificultad,
        }
        return render(request, 'diccionario/juegos/conectar.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar el juego: {str(e)}')
        return redirect('diccionario:juegos')

def juego_sopa_letras(request):
    """Juego de sopa de letras"""
    try:
        dificultad = request.GET.get('dificultad', 'medio')
        
        # Se toma un grupo mayor y solo se conservan palabras que caben en la
        # grilla de 15 celdas. La puntuación editorial no forma parte del reto.
        candidatas = _muestra_palabras_para_juego(dificultad, 80)
        palabras = []
        for palabra in candidatas:
            palabra_tablero = _normalizar_palabra_tablero(palabra.palabra_kichwa)
            if 2 <= len(palabra_tablero) <= 15:
                palabra.palabra_tablero = palabra_tablero
                palabras.append(palabra)
            if len(palabras) == 8:
                break
        
        context = {
            'palabras': palabras,
            'dificultad': dificultad,
        }
        return render(request, 'diccionario/juegos/sopa_letras.html', context)
        
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
def guardar_estadistica_juego(request):
    """Guarda una partida autenticada con valores de rango controlado."""
    if not request.user.is_authenticated:
        return _respuesta_error('Debes iniciar sesión para guardar estadísticas.', 401)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _respuesta_error('El cuerpo de la solicitud debe ser JSON válido.')
    if not isinstance(data, dict):
        return _respuesta_error('El cuerpo de la solicitud debe ser un objeto JSON.')

    tipos_validos = {valor for valor, _ in EstadisticaJuego.TIPO_JUEGO_CHOICES}
    dificultades_validas = {valor for valor, _ in Palabra.DIFICULTAD_CHOICES}
    tipo_juego = data.get('tipo_juego')
    dificultad = data.get('dificultad', 'medio')
    if tipo_juego not in tipos_validos or dificultad not in dificultades_validas:
        return _respuesta_error('El tipo de juego o la dificultad no son válidos.')
    try:
        puntuacion = _entero_no_negativo(data, 'puntuacion', 1_000_000)
        tiempo_jugado = _entero_no_negativo(data, 'tiempo_jugado', 86_400)
        correctas = _entero_no_negativo(
            data,
            'respuestas_correctas' if 'respuestas_correctas' in data else 'palabras_correctas',
            1_000,
        )
        if 'respuestas_totales' in data:
            totales = _entero_no_negativo(data, 'respuestas_totales', 1_000)
        else:
            totales = correctas + _entero_no_negativo(data, 'palabras_incorrectas', 1_000)
    except ValueError:
        return _respuesta_error('Las puntuaciones, respuestas y tiempo deben ser enteros válidos.')
    if correctas > totales:
        return _respuesta_error('Las respuestas correctas no pueden superar el total.')

    EstadisticaJuego.objects.create(
        usuario=request.user,
        tipo_juego=tipo_juego,
        puntuacion=puntuacion,
        respuestas_correctas=correctas,
        respuestas_totales=totales,
        dificultad=dificultad,
        tiempo_jugado=tiempo_jugado,
    )
    return JsonResponse({'success': True, 'message': 'Estadísticas guardadas correctamente'}, status=201)


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

    palabras_query = Palabra.objects.filter(activa=True, apta_para_juegos=True)
    por_dificultad = palabras_query.filter(dificultad_juego=dificultad)
    if por_dificultad.exists():
        palabras_query = por_dificultad
    palabras = palabras_query.order_by('?')[:cantidad]
    return JsonResponse({'palabras': [
        {
            'id': palabra.id,
            'palabra_kichwa': palabra.palabra_kichwa,
            'traduccion_espanol': palabra.traduccion_espanol,
            'pronunciacion': palabra.pronunciacion or '',
            'descripcion_juego_espanol': palabra.descripcion_juego_espanol or palabra.traduccion_espanol,
            'descripcion_juego_kichwa': palabra.descripcion_juego_kichwa or palabra.palabra_kichwa,
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
        'kichwa': palabra.palabra_kichwa,
        'espanol': palabra.traduccion_espanol,
        'definicion': palabra.definicion or '',
        'pronunciacion': palabra.pronunciacion or '',
        'categoria': {'nombre': palabra.categoria.nombre, 'slug': palabra.categoria.slug},
        'audio': palabra.audio.url if palabra.audio else None,
    })
