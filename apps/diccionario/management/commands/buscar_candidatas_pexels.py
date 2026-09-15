from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.diccionario.models import CandidataImagenPexels, PreparacionImagenVocabulario
from apps.diccionario.services.pexels import PexelsClient, PexelsError


class Command(BaseCommand):
    help = 'Busca fotografías candidatas en Pexels para un lote preparado; no las publica.'

    def add_arguments(self, parser):
        parser.add_argument('--lote', type=int, required=True)
        parser.add_argument('--cantidad', type=int, default=100)
        parser.add_argument('--resultados', type=int, default=3)
        parser.add_argument('--seleccionar-primera', action='store_true')
        parser.add_argument('--actualizar', action='store_true')

    def handle(self, *args, **options):
        if options['cantidad'] < 1:
            raise CommandError('--cantidad debe ser mayor que cero.')
        if not 1 <= options['resultados'] <= 20:
            raise CommandError('--resultados debe estar entre 1 y 20.')
        try:
            cliente = PexelsClient()
        except PexelsError as error:
            raise CommandError(str(error)) from error

        preparaciones = PreparacionImagenVocabulario.objects.filter(
            lote=options['lote'], estado='preparada',
        ).select_related('palabra').order_by('orden_lote')
        if not options['actualizar']:
            preparaciones = preparaciones.filter(candidatas_pexels__isnull=True)
        preparaciones = list(preparaciones[:options['cantidad']])
        if not preparaciones:
            raise CommandError('No hay acepciones pendientes de consulta en ese lote.')

        consultadas = candidatas = sin_resultados = 0
        restantes = None
        for preparacion in preparaciones:
            try:
                resultado = cliente.buscar_fotos(
                    preparacion.palabra.traduccion_espanol,
                    por_pagina=options['resultados'],
                )
            except PexelsError as error:
                raise CommandError(
                    f'La consulta se detuvo en {preparacion.palabra}: {error}'
                ) from error
            fotos = resultado['fotos']
            restantes = resultado['restantes'] or restantes
            consultadas += 1
            if not fotos:
                sin_resultados += 1
                continue
            with transaction.atomic():
                if options['actualizar']:
                    preparacion.candidatas_pexels.all().delete()
                for orden, foto in enumerate(fotos, start=1):
                    CandidataImagenPexels.objects.create(
                        preparacion=preparacion,
                        orden=orden,
                        seleccionada=options['seleccionar_primera'] and orden == 1,
                        **foto,
                    )
                    candidatas += 1

        mensaje_limite = f'; solicitudes restantes: {restantes}' if restantes is not None else ''
        self.stdout.write(self.style.SUCCESS(
            f'{consultadas} acepciones consultadas; {candidatas} candidatas guardadas; '
            f'{sin_resultados} sin resultados{mensaje_limite}.'
        ))
