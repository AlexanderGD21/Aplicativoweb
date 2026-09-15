import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.diccionario.models import Palabra, PreparacionImagenVocabulario
from apps.diccionario.services.imagenes_vocabulario import (
    CUOTAS_LOTE_INICIAL,
    crear_descripcion_candidata,
    crear_prompt,
    es_acepcion_apta_para_lote,
    tipo_visual_para_categoria,
)


class Command(BaseCommand):
    help = 'Clasifica las acepciones y prepara un lote revisable de prompts para imágenes.'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=100)
        parser.add_argument('--lote', type=int)
        parser.add_argument('--salida', type=Path)
        parser.add_argument('--solo-clasificar', action='store_true')

    def handle(self, *args, **options):
        cantidad = options['cantidad']
        if cantidad < 1:
            raise CommandError('--cantidad debe ser mayor que cero.')

        creadas, actualizadas = self._clasificar()
        self.stdout.write(f'Clasificación: {creadas} creadas; {actualizadas} actualizadas.')
        if options['solo_clasificar']:
            return

        lote = options['lote']
        if lote is None:
            lote = (PreparacionImagenVocabulario.objects.aggregate(maximo=Max('lote'))['maximo'] or 0) + 1
        if PreparacionImagenVocabulario.objects.filter(lote=lote).exists():
            raise CommandError(f'El lote {lote} ya existe; usa otro número.')

        seleccionadas = self._seleccionar(cantidad)
        if not seleccionadas:
            raise CommandError('No quedan acepciones concretas disponibles para preparar.')

        with transaction.atomic():
            marca_tiempo = timezone.now()
            for orden, preparacion in enumerate(seleccionadas, start=1):
                preparacion.estado = 'preparada'
                preparacion.lote = lote
                preparacion.orden_lote = orden
                preparacion.prompt = crear_prompt(preparacion.palabra, preparacion.tipo_visual)
                preparacion.descripcion_candidata = crear_descripcion_candidata(preparacion.palabra)
                preparacion.fecha_actualizacion = marca_tiempo
            PreparacionImagenVocabulario.objects.bulk_update(
                seleccionadas,
                ['estado', 'lote', 'orden_lote', 'prompt', 'descripcion_candidata', 'fecha_actualizacion'],
            )

        salida = options['salida']
        if salida:
            self._exportar(salida, seleccionadas)
            self.stdout.write(f'Manifiesto: {salida.resolve()}')
        self.stdout.write(self.style.SUCCESS(
            f'Lote {lote}: {len(seleccionadas)} acepciones preparadas para revisión y generación.'
        ))

    def _clasificar(self):
        existentes = set(PreparacionImagenVocabulario.objects.values_list('palabra_id', flat=True))
        nuevas = []
        for palabra in Palabra.objects.select_related('categoria').iterator(chunk_size=500):
            if palabra.pk not in existentes:
                nuevas.append(PreparacionImagenVocabulario(
                    palabra_id=palabra.pk,
                    tipo_visual=tipo_visual_para_categoria(palabra.categoria.slug),
                    estado='publicada' if palabra.imagen_vocabulario else 'clasificada',
                    ruta_candidata=palabra.imagen_vocabulario,
                    descripcion_candidata=palabra.descripcion_imagen,
                    credito_candidato=palabra.credito_imagen or 'Ilustración original creada para este proyecto.',
                ))
        PreparacionImagenVocabulario.objects.bulk_create(nuevas, batch_size=500)

        actualizadas = []
        queryset = PreparacionImagenVocabulario.objects.filter(
            estado='clasificada', lote__isnull=True,
        ).select_related('palabra__categoria')
        for preparacion in queryset.iterator(chunk_size=500):
            tipo = tipo_visual_para_categoria(preparacion.palabra.categoria.slug)
            if preparacion.tipo_visual != tipo:
                preparacion.tipo_visual = tipo
                actualizadas.append(preparacion)
        PreparacionImagenVocabulario.objects.bulk_update(actualizadas, ['tipo_visual'], batch_size=500)
        return len(nuevas), len(actualizadas)

    def _seleccionar(self, cantidad):
        base = PreparacionImagenVocabulario.objects.filter(
            estado='clasificada', palabra__activa=True, palabra__imagen_vocabulario='',
        ).select_related('palabra', 'palabra__categoria')
        seleccionadas = []
        usados = set()
        for slug, cuota in CUOTAS_LOTE_INICIAL.items():
            candidatos = base.filter(palabra__categoria__slug=slug).order_by(
                '-palabra__apta_para_juegos', 'palabra__traduccion_espanol', 'palabra__palabra_kichwa',
            )
            for preparacion in candidatos.iterator():
                if es_acepcion_apta_para_lote(preparacion.palabra):
                    seleccionadas.append(preparacion)
                    usados.add(preparacion.pk)
                if len([item for item in seleccionadas if item.palabra.categoria.slug == slug]) >= cuota:
                    break
                if len(seleccionadas) >= cantidad:
                    return seleccionadas

        if len(seleccionadas) < cantidad:
            restantes = base.exclude(pk__in=usados).exclude(tipo_visual__in=['diagrama', 'no_recomendada']).order_by(
                '-palabra__apta_para_juegos', 'palabra__traduccion_espanol', 'palabra__palabra_kichwa',
            )
            for preparacion in restantes.iterator():
                if es_acepcion_apta_para_lote(preparacion.palabra):
                    seleccionadas.append(preparacion)
                if len(seleccionadas) >= cantidad:
                    break
        return seleccionadas

    def _exportar(self, salida, preparaciones):
        salida.parent.mkdir(parents=True, exist_ok=True)
        with salida.open('w', encoding='utf-8-sig', newline='') as archivo:
            campos = [
                'lote', 'orden', 'palabra_id', 'kichwa', 'espanol', 'categoria',
                'tipo_visual', 'prompt', 'descripcion_candidata', 'estado',
            ]
            escritor = csv.DictWriter(archivo, fieldnames=campos)
            escritor.writeheader()
            for preparacion in preparaciones:
                escritor.writerow({
                    'lote': preparacion.lote,
                    'orden': preparacion.orden_lote,
                    'palabra_id': preparacion.palabra_id,
                    'kichwa': preparacion.palabra.palabra_kichwa,
                    'espanol': preparacion.palabra.traduccion_espanol,
                    'categoria': preparacion.palabra.categoria.nombre,
                    'tipo_visual': preparacion.tipo_visual,
                    'prompt': preparacion.prompt,
                    'descripcion_candidata': preparacion.descripcion_candidata,
                    'estado': preparacion.estado,
                })
