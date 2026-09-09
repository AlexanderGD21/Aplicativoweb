"""Taxonomía y reglas auditables para el corpus Kichwa–español.

Las reglas usan palabras completas o frases normalizadas. Esto evita errores de
subcadena como clasificar ``escritorio`` por contener ``río``. La salida siempre
incluye una confianza y un motivo: nunca se elige una categoría al azar.
"""

from dataclasses import dataclass
import re
import unicodedata


GRUPOS = {
    'entorno': 'Entorno natural',
    'personas': 'Personas y comunidad',
    'cotidiano': 'Vida cotidiana',
    'lengua': 'Lengua, tiempo y pensamiento',
    'acciones': 'Acciones y cualidades',
}


@dataclass(frozen=True)
class DefinicionCategoria:
    nombre: str
    grupo: str
    orden: int
    descripcion: str
    color: str
    terminos: tuple[str, ...]


TAXONOMIA = (
    DefinicionCategoria(
        'Animales', 'entorno', 10,
        'Fauna doméstica y silvestre, insectos, aves, peces y sus partes.', '#167C67',
        ('animal', 'fauna', 'ave', 'pajaro', 'insecto', 'mamifero', 'reptil', 'anfibio',
         'pez', 'serpiente', 'boa', 'perro', 'gato', 'caballo', 'vaca', 'toro', 'cerdo',
         'oveja', 'llama', 'alpaca', 'puma', 'jaguar', 'mono', 'raton', 'rana', 'sapo',
         'hormiga', 'abeja', 'mariposa', 'libelula', 'mosca', 'mosquito', 'arana',
         'cangrejo', 'caracol', 'gusano', 'molusco', 'babosa', 'pava', 'aguila',
         'felino', 'camelido', 'pluma', 'pico', 'garra', 'cola de animal'),
    ),
    DefinicionCategoria(
        'Plantas y agricultura', 'entorno', 20,
        'Plantas, árboles, flores, semillas, cultivos, siembra y cosecha.', '#4D7C3B',
        ('planta', 'arbol', 'arbusto', 'flor', 'semilla', 'hoja', 'tallo', 'rama',
         'corteza', 'madera', 'raiz vegetal', 'hierba', 'hongo', 'musgo', 'maiz',
         'cultivo', 'cultivar', 'sembrar', 'siembra', 'cosecha', 'cosechar', 'chacra',
         'agricultura', 'agricola', 'huerta', 'grano', 'paja', 'bejuco', 'palmera',
         'calabaza', 'jengibre', 'achera', 'moho'),
    ),
    DefinicionCategoria(
        'Naturaleza y clima', 'entorno', 30,
        'Agua, cielo, clima, fenómenos naturales y elementos del entorno.', '#287A8A',
        ('naturaleza', 'lluvia', 'llover', 'viento', 'clima', 'nube', 'neblina', 'trueno',
         'relampago', 'rayo', 'tormenta', 'frio', 'calor', 'sol', 'luna', 'estrella',
         'cielo', 'agua', 'fuego', 'humo', 'ceniza', 'barro', 'piedra', 'mineral',
         'tierra', 'suelo', 'polvo', 'sombra', 'luz', 'oscuridad', 'arcoiris',
         'planeta', 'astronomia', 'jupiter', 'venus'),
    ),
    DefinicionCategoria(
        'Territorio y lugares', 'entorno', 40,
        'Relieve, ríos, caminos, regiones, espacios y lugares geográficos.', '#3568A8',
        ('rio', 'laguna', 'lago', 'quebrada', 'cascada', 'mar', 'playa', 'montana',
         'cerro', 'volcan', 'valle', 'bosque', 'selva', 'paramo', 'cueva', 'isla',
         'territorio', 'region', 'continente', 'pais', 'pueblo', 'ciudad', 'lugar',
         'oriente', 'occidente', 'norte', 'sur', 'paisaje'),
    ),
    DefinicionCategoria(
        'Familia y relaciones', 'personas', 10,
        'Parentesco, etapas de vida y vínculos afectivos o sociales.', '#A24B70',
        ('familia', 'madre', 'mama', 'padre', 'papa', 'hijo', 'hija', 'hermano',
         'hermana', 'abuelo', 'abuela', 'nieto', 'nieta', 'tio', 'tia', 'primo',
         'prima', 'esposo', 'esposa', 'marido', 'mujer casada', 'pariente', 'padrino',
         'madrina', 'bebe',
         'nino', 'nina', 'joven', 'adolescente', 'anciano', 'amistad', 'amigo',
         'companero', 'novio', 'amante', 'matrimonio'),
    ),
    DefinicionCategoria(
        'Personas, oficios y educación', 'personas', 20,
        'Personas, roles comunitarios, profesiones, autoridades y aprendizaje.', '#7557A8',
        ('persona', 'hombre', 'mujer', 'gente', 'poblacion', 'trabajador', 'artesano',
         'cazador', 'pescador', 'agricultor', 'curandero', 'medico', 'maestro',
         'profesor', 'estudiante', 'alumno', 'escuela', 'colegio', 'universidad',
         'ensenanza', 'educacion', 'oficio', 'profesion', 'autoridad', 'jefe',
         'lider', 'sabio', 'poeta', 'musico', 'vecino', 'enemigo'),
    ),
    DefinicionCategoria(
        'Cuerpo y salud', 'personas', 30,
        'Partes del cuerpo, sentidos, enfermedades, medicina y bienestar.', '#B94A48',
        ('cuerpo', 'cabeza', 'cabello', 'pelo', 'cara', 'rostro', 'ojo', 'oreja',
         'nariz', 'boca', 'diente', 'lengua corporal', 'cuello', 'brazo', 'mano',
         'dedo', 'pierna', 'pie', 'espalda', 'pecho', 'vientre', 'estomago', 'corazon',
         'sangre', 'hueso', 'piel', 'saliva', 'enfermedad', 'enfermo', 'salud',
         'dolor', 'herida', 'fiebre', 'medicina', 'medicinal', 'cutaneo', 'ganglio',
         'linfatico', 'hinchazon', 'curar', 'sanar',
         'embarazo', 'parto', 'respirar', 'hambre', 'sed'),
    ),
    DefinicionCategoria(
        'Cultura y espiritualidad', 'personas', 40,
        'Cosmovisión, ceremonias, música, arte, comunidad y saberes ancestrales.', '#7B4B94',
        ('cultura', 'cosmovision', 'ancestral', 'tradicion', 'costumbre', 'ceremonia',
         'ritual', 'fiesta', 'danza', 'musica', 'cancion', 'poesia', 'cuento', 'leyenda',
         'mito', 'dios', 'divinidad', 'espiritu', 'alma', 'sagrado', 'templo', 'iglesia',
         'rezar', 'plegaria', 'ofrenda', 'inca', 'tawantin suyu', 'pachamama',
         'artesania', 'tejido tradicional'),
    ),
    DefinicionCategoria(
        'Alimentos y bebidas', 'cotidiano', 10,
        'Comidas, frutas, verduras, bebidas, ingredientes y preparaciones.', '#B86622',
        ('alimento', 'comida', 'comestible', 'bebida', 'beber', 'sopa', 'caldo',
         'mazamorra', 'chicha', 'carne', 'pescado', 'fruta', 'fruto comestible',
         'verdura', 'hortaliza', 'tuberculo', 'papa', 'camote', 'yuca', 'platano',
         'cereal', 'harina', 'pan', 'sal', 'azucar', 'miel', 'leche', 'queso', 'huevo',
         'cocina', 'cocinar', 'asado', 'hervido', 'dulce', 'sabor', 'insipido',
         'condimento'),
    ),
    DefinicionCategoria(
        'Hogar y construcción', 'cotidiano', 20,
        'Vivienda, espacios domésticos, muebles y elementos de construcción.', '#98633B',
        ('casa', 'vivienda', 'hogar', 'choza', 'habitacion', 'cuarto', 'cocina de casa',
         'pared', 'techo', 'puerta', 'ventana', 'piso', 'escalera', 'patio', 'corral',
         'cerca', 'mueble', 'mesa', 'silla', 'cama', 'construccion', 'construir',
         'ladrillo', 'viga', 'columna', 'cemento'),
    ),
    DefinicionCategoria(
        'Vestimenta y cuidado personal', 'cotidiano', 30,
        'Ropa, calzado, adornos y objetos de higiene o cuidado personal.', '#A54949',
        ('ropa', 'prenda', 'vestimenta', 'vestir', 'camisa', 'pantalon', 'falda',
         'anaco', 'poncho', 'sombrero', 'zapato', 'calzado', 'media', 'cinturon',
         'manta', 'collar', 'pulsera', 'arete', 'adorno', 'peine', 'jabon', 'lavarse',
         'banarse', 'higiene'),
    ),
    DefinicionCategoria(
        'Herramientas y objetos', 'cotidiano', 40,
        'Utensilios, recipientes, materiales, instrumentos y objetos de uso diario.', '#5E6E7D',
        ('objeto', 'herramienta', 'utensilio', 'recipiente', 'vasija', 'olla', 'plato',
         'vaso', 'cuchara', 'cuchillo', 'canasta', 'botella', 'cuerda', 'soga', 'hilo',
         'aguja', 'martillo', 'hacha', 'machete', 'pala', 'red', 'trampa', 'arma',
         'instrumento', 'material', 'metal', 'cobre', 'oro', 'plata', 'papel', 'libro',
         'cuaderno', 'lapiz', 'paquete', 'bulto', 'carga'),
    ),
    DefinicionCategoria(
        'Transporte y caminos', 'cotidiano', 50,
        'Vehículos, desplazamientos, rutas y medios de transporte.', '#3E7191',
        ('transporte', 'vehiculo', 'carro', 'automovil', 'camion', 'bus', 'barco',
         'canoa', 'avion', 'bicicleta', 'camino', 'carretera', 'calle', 'puente',
         'viaje', 'viajar', 'pasajero'),
    ),
    DefinicionCategoria(
        'Gramática y expresiones', 'lengua', 10,
        'Pronombres, partículas, conectores, interjecciones y expresiones.', '#46506D',
        ('expresion', 'exclamacion', 'interjeccion', 'pronombre', 'adverbio',
         'adjetivo demostrativo', 'conjuncion', 'preposicion', 'particula', 'sufijo',
         'prefijo', 'conector', 'afirmacion', 'negacion', 'saludo', 'despedida',
         'pregunta', 'respuesta', 'ademas', 'tambien', 'palabra afirmativa'),
    ),
    DefinicionCategoria(
        'Tiempo y calendario', 'lengua', 20,
        'Momentos del día, fechas, duración, ciclos y calendario.', '#7A6930',
        ('tiempo', 'dia', 'noche', 'manana', 'tarde', 'madrugada', 'hora', 'minuto',
         'semana', 'mes', 'ano', 'calendario', 'fecha', 'ayer', 'hoy', 'pasado manana',
         'estacion del ano', 'epoca', 'periodo', 'instante', 'siglo'),
    ),
    DefinicionCategoria(
        'Números, cantidades y medidas', 'lengua', 30,
        'Números, cantidades, tamaños, pesos, distancias y unidades de medida.', '#8A6C2D',
        ('numero', 'cantidad', 'contar', 'primero', 'segundo', 'tercero', 'mitad',
         'doble', 'unidad', 'medida', 'medir', 'peso', 'pesar', 'distancia', 'metro',
         'kilometro', 'litro', 'libra', 'cardinal', 'uno', 'dos', 'tres', 'cuatro',
         'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez', 'mucho', 'poco',
         'bastante', 'todo', 'ninguno'),
    ),
    DefinicionCategoria(
        'Espacio y ubicación', 'lengua', 40,
        'Posiciones, direcciones, orientación y relaciones espaciales.', '#536E8A',
        ('arriba', 'abajo', 'encima', 'debajo', 'delante', 'detras', 'dentro', 'fuera',
         'interior', 'exterior', 'izquierda', 'derecha', 'cerca de', 'lejos', 'centro',
         'borde', 'lado', 'direccion', 'posicion', 'vertical', 'horizontal'),
    ),
    DefinicionCategoria(
        'Ideas y conceptos', 'lengua', 50,
        'Conceptos abstractos que no pertenecen de forma fiable a otro tema.', '#646B73',
        ('idea', 'concepto', 'razon', 'verdad', 'mentira', 'causa', 'efecto', 'problema',
         'solucion', 'forma', 'tipo', 'clase', 'orden', 'valor', 'nombre', 'significado'),
    ),
    DefinicionCategoria(
        'Acciones y procesos', 'acciones', 10,
        'Verbos, movimientos, cambios y actividades.', '#A34538',
        ('verbo', 'accion', 'proceso', 'actividad', 'movimiento', 'acto de'),
    ),
    DefinicionCategoria(
        'Emociones y cualidades', 'acciones', 20,
        'Emociones, estados, colores, formas y características descriptivas.', '#9A4D78',
        ('emocion', 'sentimiento', 'alegria', 'tristeza', 'miedo', 'temor', 'enojo',
         'ira', 'amor', 'carino', 'odio', 'verguenza', 'orgullo', 'feliz', 'triste',
         'color', 'rojo', 'azul', 'verde', 'amarillo', 'blanco', 'negro', 'grande',
         'pequeno', 'largo', 'corto', 'ancho', 'estrecho', 'duro', 'blando', 'suave',
         'fuerte', 'debil', 'rapido', 'lento', 'bonito', 'feo', 'limpio', 'sucio'),
    ),
)


POR_NOMBRE = {categoria.nombre: categoria for categoria in TAXONOMIA}


def _patron_termino(termino):
    termino = normalizar(termino)
    return re.compile(rf'(?<![a-z0-9]){re.escape(termino)}(?![a-z0-9])')


@dataclass(frozen=True)
class ResultadoClasificacion:
    categoria: str
    confianza: str
    motivo: str
    puntaje: int


def normalizar(texto):
    texto = unicodedata.normalize('NFKD', (texto or '').casefold())
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', texto).strip()


def _contiene(texto, termino):
    termino = normalizar(termino)
    return bool(re.search(rf'(?<![a-z0-9]){re.escape(termino)}(?![a-z0-9])', texto))


PATRONES = {
    categoria.nombre: tuple((termino, _patron_termino(termino)) for termino in categoria.terminos)
    for categoria in TAXONOMIA
}


def _parece_verbo(traduccion, definicion):
    if definicion.startswith(('verbo ', 'accion de ', 'acto de ', 'proceso de ')):
        return True
    alternativas = [item.strip() for item in re.split(r'[,;]', traduccion) if item.strip()]
    primera = alternativas[0].split()[0] if alternativas else ''
    sustantivos_ambiguos = {
        'altar', 'azucar', 'bar', 'celular', 'collar', 'familiar', 'hogar', 'jaguar',
        'jupiter', 'lugar', 'mar', 'militar', 'mujer', 'pilar', 'placer', 'poder',
        'saber', 'solar', 'taller',
    }
    return bool(
        primera not in sustantivos_ambiguos
        and re.fullmatch(r'[a-z]+(?:ar|er|ir)(?:se)?', primera)
    )


def _parece_cualidad(traduccion, definicion):
    return definicion.startswith(('adjetivo ', 'cualidad ', 'que describe ', 'estado de ')) or any(
        _contiene(traduccion, termino)
        for termino in ('bueno', 'malo', 'grande', 'pequeno', 'duro', 'blando', 'claro',
                        'oscuro', 'rapido', 'lento', 'limpio', 'sucio', 'hermoso')
    )


def clasificar_textos(palabra_kichwa, traduccion_espanol, definicion=''):
    traduccion = normalizar(traduccion_espanol)
    detalle = normalizar(definicion)
    puntajes = {}
    coincidencias = {}

    for categoria in TAXONOMIA:
        encontrados = []
        puntaje = 0
        for termino, patron in PATRONES[categoria.nombre]:
            if patron.search(traduccion):
                puntaje += 5
                encontrados.append(termino)
            elif patron.search(detalle):
                puntaje += 2
                encontrados.append(termino)
        puntajes[categoria.nombre] = puntaje
        coincidencias[categoria.nombre] = encontrados

    # Las marcas gramaticales explícitas describen el tipo de entrada y tienen
    # prioridad sobre coincidencias incidentales en la explicación.
    if traduccion.startswith(('expresion ', 'interjeccion ')) or detalle.startswith(
        ('exclamacion ', 'interjeccion ', 'adverbio ', 'pronombre ', 'conjuncion ')
    ):
        puntajes['Gramática y expresiones'] += 12

    if _parece_verbo(traduccion, detalle):
        # Una traducción en infinitivo ayuda, pero no desplaza una señal temática
        # directa como "cocinar" dentro de Alimentos o "Júpiter" como planeta.
        puntajes['Acciones y procesos'] += 4
        coincidencias['Acciones y procesos'].append('forma verbal')

    if _parece_cualidad(traduccion, detalle):
        puntajes['Emociones y cualidades'] += 4
        coincidencias['Emociones y cualidades'].append('forma descriptiva')

    # Python conserva el orden declarado de la taxonomía en los empates.
    ordenados = sorted(TAXONOMIA, key=lambda categoria: -puntajes[categoria.nombre])
    mejor = ordenados[0]
    puntaje = puntajes[mejor.nombre]
    segundo = puntajes[ordenados[1].nombre]

    if puntaje == 0:
        if _parece_verbo(traduccion, detalle):
            mejor = POR_NOMBRE['Acciones y procesos']
            motivo = 'La traducción presenta una forma verbal.'
        elif _parece_cualidad(traduccion, detalle):
            mejor = POR_NOMBRE['Emociones y cualidades']
            motivo = 'La definición presenta una cualidad o estado.'
        else:
            mejor = POR_NOMBRE['Ideas y conceptos']
            motivo = 'No hubo una señal temática suficiente; requiere revisión humana.'
        return ResultadoClasificacion(mejor.nombre, 'baja', motivo, 0)

    margen = puntaje - segundo
    confianza = 'alta' if puntaje >= 10 and margen >= 4 else 'media' if puntaje >= 4 and margen > 0 else 'baja'
    terminos = ', '.join(dict.fromkeys(coincidencias[mejor.nombre])) or 'estructura de la entrada'
    motivo = f'Coincidencias: {terminos}. Puntaje {puntaje}; margen {margen}.'
    if margen == 0:
        motivo += ' Hay empate temático; requiere revisión humana.'
    return ResultadoClasificacion(mejor.nombre, confianza, motivo[:255], puntaje)


def calcular_dificultad_pronunciacion(palabra_kichwa):
    """Estima la carga articulatoria a partir de la forma escrita en Kichwa."""
    original = (palabra_kichwa or '').strip()
    principal = re.split(r'[;:]', original, maxsplit=1)[0]
    normalizada = normalizar(principal)
    tokens = normalizada.split()
    letras = ''.join(tokens)
    mayor = max((len(token) for token in tokens), default=0)
    puntaje = 0

    if mayor >= 12:
        puntaje += 3
    elif mayor >= 9:
        puntaje += 2
    elif mayor >= 6:
        puntaje += 1

    if len(tokens) > 1:
        puntaje += min(2, len(tokens) - 1)
    if ';' in original or ':' in original:
        puntaje += 2
    if '-' in original or "'" in original or '’' in original:
        puntaje += 1

    grupos = sum(letras.count(grupo) for grupo in ('ch', 'sh', 'll', 'ts', 'zh', 'kh', 'ph', 'th'))
    if grupos >= 4:
        puntaje += 2
    elif grupos >= 2:
        puntaje += 1

    if len(letras) >= 16:
        puntaje += 1

    if puntaje <= 1:
        return 'facil', 'basico', puntaje
    if puntaje <= 3:
        return 'medio', 'intermedio', puntaje
    return 'dificil', 'avanzado', puntaje
