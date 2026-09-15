import re


TIPO_POR_CATEGORIA = {
    'animales': 'ser_vivo',
    'plantas-y-agricultura': 'ser_vivo',
    'cuerpo-y-salud': 'objeto',
    'alimentos-y-bebidas': 'objeto',
    'hogar-y-construccion': 'objeto',
    'vestimenta-y-cuidado-personal': 'objeto',
    'herramientas-y-objetos': 'objeto',
    'transporte-y-caminos': 'objeto',
    'naturaleza-y-clima': 'paisaje',
    'territorio-y-lugares': 'paisaje',
    'familia-y-relaciones': 'persona',
    'personas-oficios-y-educacion': 'persona',
    'acciones-y-procesos': 'accion',
    'emociones-y-cualidades': 'cualidad',
    'numeros-cantidades-y-medidas': 'diagrama',
    'espacio-y-ubicacion': 'diagrama',
    'tiempo-y-calendario': 'diagrama',
    'ideas-y-conceptos': 'diagrama',
    'gramatica-y-expresiones': 'no_recomendada',
    'cultura-y-espiritualidad': 'diagrama',
}


CUOTAS_LOTE_INICIAL = {
    'animales': 20,
    'plantas-y-agricultura': 12,
    'cuerpo-y-salud': 12,
    'naturaleza-y-clima': 10,
    'alimentos-y-bebidas': 12,
    'herramientas-y-objetos': 8,
    'territorio-y-lugares': 8,
    'hogar-y-construccion': 6,
    'vestimenta-y-cuidado-personal': 5,
    'transporte-y-caminos': 4,
    'personas-oficios-y-educacion': 3,
}


def tipo_visual_para_categoria(slug):
    return TIPO_POR_CATEGORIA.get(slug, 'no_recomendada')


def es_acepcion_apta_para_lote(palabra):
    traduccion = palabra.traduccion_espanol.strip()
    return bool(
        traduccion
        and len(traduccion) <= 48
        and len(traduccion.split()) <= 3
        and not re.search(r'[,;/()!?¿¡]', traduccion)
    )


def crear_prompt(palabra, tipo_visual):
    enfoque = {
        'ser_vivo': 'Muestra claramente el animal o la planta como elemento principal.',
        'objeto': 'Muestra el elemento concreto completo y fácil de reconocer.',
        'paisaje': 'Representa el lugar o fenómeno natural con una composición sencilla.',
        'persona': 'Representa a la persona o el oficio en una escena cotidiana respetuosa.',
        'accion': 'Representa la acción con una escena clara y una sola acción principal.',
        'cualidad': 'Representa la cualidad mediante una situación cotidiana comprensible.',
        'diagrama': 'Usa una composición educativa simple que explique visualmente el concepto.',
    }.get(tipo_visual, 'Representa la acepción con una composición educativa sencilla.')
    return (
        f'Ilustración cuadrada infantil y educativa para la acepción Kichwa '
        f'“{palabra.palabra_kichwa}”, que en español significa '
        f'“{palabra.traduccion_espanol}”. {enfoque} Estilo de libro ilustrado, '
        'contexto cultural respetuoso inspirado en el Ecuador andino y amazónico, '
        'fondo limpio, colores cálidos, contornos suaves, sin texto, letras, '
        'logotipos, firmas ni marcas de agua.'
    )


def crear_descripcion_candidata(palabra):
    return (
        f'Representación educativa de {palabra.traduccion_espanol}, '
        f'correspondiente a la acepción Kichwa {palabra.palabra_kichwa}.'
    )[:240]
