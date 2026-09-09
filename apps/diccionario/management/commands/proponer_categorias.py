import re
import unicodedata
from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.diccionario.models import Categoria, Palabra


REGLAS = {
    'Animales': ('animal', 'ave', 'pajaro', 'pez', 'insecto', 'perro', 'gato', 'serpiente', 'rana', 'mamifero'),
    'Alimentación': ('alimento', 'comida', 'bebida', 'cocinar', 'comestible', 'fruta', 'pan', 'sopa'),
    'Cuerpo y salud': ('cuerpo', 'cabeza', 'mano', 'pie', 'ojo', 'enfermedad', 'salud', 'dolor', 'piel'),
    'Familia y sociedad': ('familia', 'madre', 'padre', 'hermano', 'hija', 'hijo', 'abuelo', 'persona', 'comunidad'),
    'Naturaleza y clima': ('rio', 'montana', 'agua', 'lluvia', 'viento', 'clima', 'tierra', 'cielo', 'sol'),
    'Plantas y agricultura': ('planta', 'arbol', 'flor', 'semilla', 'cultivo', 'agricultura', 'tuberculo', 'maiz'),
    'Tiempo y calendario': ('tiempo', 'dia', 'mes', 'ano', 'hora', 'semana', 'estacion', 'calendario'),
    'Acciones y verbos': ('verbo', 'accion', 'realizar', 'mover', 'caminar', 'hablar', 'hacer'),
    'Cualidades y descripciones': ('adjetivo', 'cualidad', 'describe', 'caracteristica', 'color', 'tamano'),
    'Gramática y expresiones': ('pronombre', 'expresion', 'particula', 'conector', 'adverbio', 'preposicion'),
    'Cultura y cosmovisión': ('ancestral', 'cosmovision', 'ceremonia', 'fiesta', 'tradicion', 'divinidad', 'comunitaria'),
    'Vida diaria y objetos': ('objeto', 'herramienta', 'casa', 'vestimenta', 'calzado', 'transporte', 'oficio'),
}


def normalizar(texto):
    texto = unicodedata.normalize('NFD', texto.casefold())
    texto = ''.join(caracter for caracter in texto if unicodedata.category(caracter) != 'Mn')
    return re.sub(r'\s+', ' ', texto)


class Command(BaseCommand):
    help = 'Propone categorías por palabras clave; nunca mueve la categoría principal.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        categorias = Categoria.objects.in_bulk(field_name='nombre')
        faltantes = sorted(set(REGLAS) - set(categorias))
        if faltantes:
            raise CommandError(f'Faltan categorías: {", ".join(faltantes)}')
        palabras = Palabra.objects.filter(categoria__nombre='General', categoria_propuesta__isnull=True, estado_revision='pendiente').only('pk', 'palabra_kichwa', 'traduccion_espanol', 'definicion')
        propuestas, conteo = [], Counter()
        for palabra in palabras.iterator(chunk_size=500):
            texto = normalizar(' '.join((palabra.palabra_kichwa, palabra.traduccion_espanol, palabra.definicion or '')))
            puntajes = {nombre: sum(termino in texto for termino in terminos) for nombre, terminos in REGLAS.items()}
            nombre, puntaje = max(puntajes.items(), key=lambda item: item[1])
            if puntaje:
                propuestas.append((palabra.pk, categorias[nombre].pk))
                conteo[nombre] += 1
        self.stdout.write(f'Propuestas para revisión: {len(propuestas)}')
        for nombre, total in conteo.most_common():
            self.stdout.write(f'  {nombre}: {total}')
        if not options['apply']:
            self.stdout.write(self.style.WARNING('Modo simulación: no se guardó ninguna propuesta.'))
            return
        with transaction.atomic():
            for palabra_id, categoria_id in propuestas:
                Palabra.objects.filter(pk=palabra_id, categoria_propuesta__isnull=True).update(categoria_propuesta_id=categoria_id)
        self.stdout.write(self.style.SUCCESS(f'{len(propuestas)} propuestas guardadas para revisión humana.'))
