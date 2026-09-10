"""Selección explicable de vocabulario relacionado.

Las relaciones editoriales tienen prioridad. El respaldo automático exige una
señal léxica o conceptual; compartir categoría, por sí solo, nunca basta.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re

from ..models import Palabra, RelacionPalabra, normalizar_texto_busqueda


STOPWORDS = {
    'a', 'al', 'algo', 'como', 'con', 'de', 'del', 'el', 'en', 'es', 'esta',
    'este', 'la', 'las', 'lo', 'los', 'o', 'para', 'por', 'que', 'se', 'su',
    'un', 'una', 'y',
}

FACETAS = {
    'preguntas': {
        'interrogativo', 'pregunta', 'cuando', 'donde', 'quien', 'cual',
        'cuanto', 'cuanta', 'cuantos', 'cuantas', 'porque',
    },
    'tiempo_cercano': {
        'cuando', 'tiempo', 'momento', 'instante', 'ahora', 'hoy', 'ayer', 'manana',
        'antes', 'despues', 'luego', 'pronto', 'temprano', 'tarde', 'noche',
        'dia', 'presente', 'pasado', 'futuro', 'diario', 'diariamente',
    },
    'calendario': {
        'calendario', 'mes', 'semana', 'ano', 'decada', 'siglo', 'milenio',
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
        'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre', 'lunes',
        'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo',
    },
    'familia': {
        'familia', 'madre', 'padre', 'hijo', 'hija', 'hermano', 'hermana',
        'abuelo', 'abuela', 'tio', 'tia', 'primo', 'prima', 'esposo', 'esposa',
    },
    'alimentacion': {
        'alimento', 'comida', 'comer', 'bebida', 'beber', 'fruta', 'verdura',
        'semilla', 'carne', 'sopa', 'cocinar', 'dulce', 'salado',
    },
    'naturaleza': {
        'agua', 'rio', 'lago', 'lluvia', 'montana', 'bosque', 'tierra', 'sol',
        'luna', 'viento', 'nube', 'fuego', 'piedra', 'naturaleza',
    },
    'cuerpo': {
        'cuerpo', 'cabeza', 'cara', 'ojo', 'nariz', 'boca', 'mano', 'pie',
        'brazo', 'pierna', 'corazon', 'sangre', 'hueso', 'piel',
    },
    'hogar': {
        'casa', 'hogar', 'habitacion', 'cocina', 'puerta', 'ventana', 'techo',
        'pared', 'mesa', 'silla', 'cama', 'mueble',
    },
}

PRIORIDAD_TIEMPO = {
    'ahora': 9, 'hoy': 9, 'ayer': 8, 'manana': 8, 'antes': 6,
    'despues': 6, 'luego': 5, 'pronto': 4, 'tarde': 3, 'noche': 3,
    'dia': 3, 'presente': 3, 'pasado': 3, 'futuro': 3,
}

ETIQUETAS_TIPO = {
    'familia': 'Misma familia semántica',
    'sinonimo': 'Sinónimo o equivalente',
    'contraste': 'Contraste de significado',
    'contexto': 'Relacionado por contexto',
}


@dataclass(frozen=True)
class RelacionSugerida:
    palabra: Palabra
    motivo: str
    tipo: str
    puntuacion: int


def _texto(palabra: Palabra) -> str:
    return ' '.join(filter(None, (
        palabra.traduccion_espanol,
        palabra.definicion,
        palabra.sinonimos,
        palabra.notas_gramaticales,
    )))


@lru_cache(maxsize=8192)
def _tokens(texto: str) -> frozenset[str]:
    normalizado = normalizar_texto_busqueda(texto)
    return frozenset(
        token for token in re.findall(r'[a-zñ]+', normalizado)
        if len(token) >= 3 and token not in STOPWORDS
    )


def _facetas(tokens: frozenset[str]) -> set[str]:
    return {nombre for nombre, vocabulario in FACETAS.items() if tokens & vocabulario}


def _raiz_kichwa(palabra: Palabra) -> str:
    texto = normalizar_texto_busqueda(palabra.palabra_kichwa)
    return texto.split(',')[0].split(';')[0].strip(' ?!¡¿.')


def _puntuar(origen: Palabra, candidata: Palabra) -> tuple[int, str]:
    origen_traduccion = _tokens(origen.traduccion_espanol or '')
    candidata_traduccion = _tokens(candidata.traduccion_espanol or '')
    origen_contenido = _tokens(_texto(origen))
    candidata_contenido = _tokens(_texto(candidata))

    comunes_traduccion = origen_traduccion & candidata_traduccion
    comunes_contenido = origen_contenido & candidata_contenido
    # Las facetas se apoyan primero en la equivalencia visible. Así una palabra
    # como "podrido" no se relaciona con "cuándo" sólo porque su definición
    # menciona que algo se descompone con el tiempo.
    facetas_origen = _facetas(origen_traduccion) | (
        {'preguntas'} if 'interrogativo' in origen_contenido else set()
    )
    facetas_candidata = _facetas(candidata_traduccion)
    facetas_comunes = facetas_origen & facetas_candidata

    puntuacion = len(comunes_traduccion) * 18
    puntuacion += len(comunes_contenido - comunes_traduccion) * 4
    puntuacion += len(facetas_comunes) * 12
    if 'cuando' in origen_traduccion and 'tiempo_cercano' in facetas_candidata:
        puntuacion += max((PRIORIDAD_TIEMPO.get(token, 0) for token in candidata_traduccion), default=0)

    raiz_origen = _raiz_kichwa(origen)
    raiz_candidata = _raiz_kichwa(candidata)
    if raiz_origen and raiz_origen == raiz_candidata:
        puntuacion += 28
    elif min(len(raiz_origen), len(raiz_candidata)) >= 5:
        prefijo = 0
        for izquierda, derecha in zip(raiz_origen, raiz_candidata):
            if izquierda != derecha:
                break
            prefijo += 1
        if prefijo >= 5:
            puntuacion += 5

    # La categoría ayuda a ordenar señales ya existentes, pero nunca crea una.
    if origen.categoria_id == candidata.categoria_id and puntuacion:
        puntuacion += 2

    if comunes_traduccion:
        motivo = 'Comparte significado en español'
    elif raiz_origen and raiz_origen == raiz_candidata:
        motivo = 'Otra entrada del mismo término'
    elif 'preguntas' in facetas_comunes:
        motivo = 'Forma parte del vocabulario interrogativo'
    elif 'tiempo_cercano' in facetas_comunes:
        motivo = 'Comparte el mismo campo temporal'
    elif facetas_comunes:
        motivo = 'Comparte un campo de significado'
    else:
        motivo = 'Coincide en su definición'

    return puntuacion, motivo


def obtener_palabras_relacionadas(palabra: Palabra, limite: int = 4) -> list[RelacionSugerida]:
    """Devuelve relaciones curadas y sugerencias semánticas con explicación."""
    resultado: list[RelacionSugerida] = []
    ids_usados = {palabra.pk}

    salientes = RelacionPalabra.objects.filter(
        origen=palabra, destino__activa=True,
    ).select_related('destino', 'destino__categoria')
    entrantes = RelacionPalabra.objects.filter(
        destino=palabra, origen__activa=True,
    ).select_related('origen', 'origen__categoria')

    for relacion, relacionada in [
        *((item, item.destino) for item in salientes),
        *((item, item.origen) for item in entrantes),
    ]:
        if relacionada.pk in ids_usados:
            continue
        resultado.append(RelacionSugerida(
            palabra=relacionada,
            motivo=relacion.nota or ETIQUETAS_TIPO.get(relacion.tipo, 'Relación editorial'),
            tipo='curada',
            puntuacion=1000,
        ))
        ids_usados.add(relacionada.pk)
        if len(resultado) >= limite:
            return resultado

    sugerencias = []
    candidatas = Palabra.objects.select_related('categoria').filter(
        activa=True,
    ).exclude(pk__in=ids_usados)
    for candidata in candidatas.iterator(chunk_size=500):
        puntuacion, motivo = _puntuar(palabra, candidata)
        if puntuacion >= 8:
            sugerencias.append(RelacionSugerida(candidata, motivo, 'semantica', puntuacion))

    sugerencias.sort(key=lambda item: (
        -item.puntuacion,
        normalizar_texto_busqueda(item.palabra.palabra_kichwa),
        item.palabra.pk,
    ))
    resultado.extend(sugerencias[:max(0, limite - len(resultado))])
    return resultado
