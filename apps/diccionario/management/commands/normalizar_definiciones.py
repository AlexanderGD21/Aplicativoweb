from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Q

from apps.diccionario.models import Palabra


class Command(BaseCommand):
    help = 'Copia notas gramaticales a definición solo si esta está vacía.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--limit', type=int, default=10)

    def handle(self, *args, **options):
        candidatas = Palabra.objects.filter(Q(definicion__isnull=True) | Q(definicion='')).exclude(Q(notas_gramaticales__isnull=True) | Q(notas_gramaticales=''))
        if not options['apply']:
            self.stdout.write(self.style.WARNING(f'Modo simulación: {candidatas.count()} candidatas; no se modificó ningún dato.'))
            for palabra in candidatas.order_by('pk')[:max(options['limit'], 0)]:
                self.stdout.write(f'  #{palabra.pk} {palabra.palabra_kichwa}: {palabra.notas_gramaticales[:100]}')
            return
        with transaction.atomic():
            actualizadas = candidatas.update(definicion=F('notas_gramaticales'))
        self.stdout.write(self.style.SUCCESS(f'{actualizadas} definiciones actualizadas sin borrar las notas originales.'))
