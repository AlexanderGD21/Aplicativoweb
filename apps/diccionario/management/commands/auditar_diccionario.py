import json

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from apps.diccionario.models import Categoria, Palabra
from apps.diccionario.services.juegos import entrada_jugable


class Command(BaseCommand):
    help = 'Muestra indicadores de calidad del diccionario sin modificar datos.'

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true')

    def handle(self, *args, **options):
        palabras = Palabra.objects.all()
        jugables = [
            palabra for palabra in palabras.filter(activa=True).only(
                'palabra_kichwa', 'traduccion_espanol', 'dificultad', 'apta_para_juegos',
            ) if entrada_jugable(palabra)
        ]
        reporte = {
            'palabras': {
                'total': palabras.count(),
                'activas': palabras.filter(activa=True).count(),
                'sin_definicion': palabras.filter(Q(definicion__isnull=True) | Q(definicion='')).count(),
                'sin_pronunciacion': palabras.filter(Q(pronunciacion__isnull=True) | Q(pronunciacion='')).count(),
                'con_notas_gramaticales': palabras.exclude(notas_gramaticales__isnull=True).exclude(notas_gramaticales='').count(),
                'con_audio': palabras.exclude(audio__isnull=True).exclude(audio='').count(),
                'apta_para_juegos': palabras.filter(apta_para_juegos=True).count(),
                'jugables_actuales': len(jugables),
                'jugables_generales_sin_marca': sum(not palabra.apta_para_juegos for palabra in jugables),
                'con_categoria_propuesta': palabras.filter(categoria_propuesta__isnull=False).count(),
            },
            'clasificacion': {
                campo: list(palabras.values(campo).annotate(total=Count('id')).order_by(campo))
                for campo in (
                    'dificultad', 'nivel_dificultad', 'tipo', 'estado_revision',
                    'clasificacion_confianza',
                )
            },
            'dificultades_jugables': {
                dificultad: sum(palabra.dificultad == dificultad for palabra in jugables)
                for dificultad, _ in Palabra.DIFICULTAD_CHOICES
            },
            'categorias': list(
                Categoria.objects.annotate(total=Count('palabras'))
                .values('grupo', 'nombre', 'total')
                .order_by('grupo', 'orden', 'nombre')
            ),
        }
        if options['json']:
            self.stdout.write(json.dumps(reporte, ensure_ascii=False, indent=2))
            return
        self.stdout.write(self.style.MIGRATE_HEADING('Auditoría del diccionario'))
        for grupo, valores in reporte.items():
            self.stdout.write(f'\n{grupo.capitalize()}:')
            self.stdout.write(json.dumps(valores, ensure_ascii=False, indent=2))
