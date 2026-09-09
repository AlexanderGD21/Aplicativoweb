from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.diccionario.models import Categoria, Palabra, normalizar_texto_busqueda
from apps.diccionario.services.clasificacion import (
    TAXONOMIA,
    calcular_dificultad_pronunciacion,
    clasificar_textos,
)


class Command(BaseCommand):
    help = (
        'Reclasifica el corpus con la taxonomía temática auditable, recalcula la '
        'dificultad de pronunciación y prepara los índices de búsqueda bilingüe.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Guarda los cambios. Sin esta opción solo genera una vista previa.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Incluye entradas revisadas o validadas. Por defecto las conserva.',
        )

    def handle(self, *args, **options):
        aplicar = options['apply']
        forzar = options['force']
        palabras = Palabra.objects.all().order_by('pk')
        if not forzar:
            palabras = palabras.filter(estado_revision='pendiente')

        categorias = {definicion.nombre: definicion for definicion in TAXONOMIA}
        por_categoria = Counter()
        por_confianza = Counter()
        por_dificultad = Counter()
        resultados = []

        for palabra in palabras.iterator(chunk_size=500):
            resultado = clasificar_textos(
                palabra.palabra_kichwa,
                palabra.traduccion_espanol,
                palabra.definicion or '',
            )
            dificultad, nivel, puntaje_pronunciacion = calcular_dificultad_pronunciacion(
                palabra.palabra_kichwa
            )
            resultados.append((palabra, resultado, dificultad, nivel, puntaje_pronunciacion))
            por_categoria[resultado.categoria] += 1
            por_confianza[resultado.confianza] += 1
            por_dificultad[dificultad] += 1

        self.stdout.write(f'Entradas analizadas: {len(resultados)}')
        self._imprimir_conteo('Categorías', por_categoria)
        self._imprimir_conteo('Confianza', por_confianza)
        self._imprimir_conteo('Pronunciación', por_dificultad)

        if not aplicar:
            self.stdout.write(self.style.WARNING('Vista previa: no se modificó la base de datos.'))
            return

        with transaction.atomic():
            momento_actualizacion = timezone.now()
            categorias_db = {}
            for definicion in TAXONOMIA:
                categoria, _ = Categoria.objects.update_or_create(
                    nombre=definicion.nombre,
                    defaults={
                        'grupo': definicion.grupo,
                        'orden': definicion.orden,
                        'descripcion': definicion.descripcion,
                        'color': definicion.color,
                    },
                )
                categorias_db[definicion.nombre] = categoria

            pendientes = []
            for palabra, resultado, dificultad, nivel, puntaje_pronunciacion in resultados:
                palabra.categoria = categorias_db[resultado.categoria]
                palabra.categoria_propuesta = None
                palabra.clasificacion_confianza = resultado.confianza
                palabra.clasificacion_motivo = resultado.motivo
                palabra.dificultad = dificultad
                palabra.nivel_dificultad = nivel
                palabra.busqueda_kichwa = normalizar_texto_busqueda(palabra.palabra_kichwa)
                palabra.busqueda_espanol = normalizar_texto_busqueda(palabra.traduccion_espanol)
                palabra.busqueda_contenido = normalizar_texto_busqueda(' '.join(filter(None, (
                    palabra.definicion,
                    palabra.pronunciacion,
                    palabra.sinonimos,
                    palabra.notas_gramaticales,
                ))))
                palabra.clasificacion_motivo = (
                    f'{resultado.motivo} Pronunciación: {puntaje_pronunciacion} puntos.'
                )[:255]
                palabra.fecha_actualizacion = momento_actualizacion
                pendientes.append(palabra)

                if len(pendientes) == 500:
                    self._guardar_lote(pendientes)
                    pendientes = []

            if pendientes:
                self._guardar_lote(pendientes)

            nombres_vigentes = tuple(categorias)
            Categoria.objects.exclude(nombre__in=nombres_vigentes).filter(
                palabras__isnull=True
            ).delete()

        self.stdout.write(self.style.SUCCESS('Reestructuración aplicada correctamente.'))

    def _guardar_lote(self, palabras):
        Palabra.objects.bulk_update(
            palabras,
            [
                'categoria',
                'categoria_propuesta',
                'clasificacion_confianza',
                'clasificacion_motivo',
                'dificultad',
                'nivel_dificultad',
                'busqueda_kichwa',
                'busqueda_espanol',
                'busqueda_contenido',
                'fecha_actualizacion',
            ],
            batch_size=500,
        )

    def _imprimir_conteo(self, titulo, conteo):
        self.stdout.write(f'\n{titulo}:')
        for nombre, cantidad in conteo.most_common():
            self.stdout.write(f'  {nombre}: {cantidad}')
