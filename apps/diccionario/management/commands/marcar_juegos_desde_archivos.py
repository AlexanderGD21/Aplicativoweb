import ast
import re
import unicodedata
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.diccionario.models import Palabra


def normalizar(texto):
    texto = unicodedata.normalize('NFKC', texto)
    return re.sub(r'\s+', ' ', texto).strip().casefold().rstrip(' .,;:')


def leer_pares(ruta, invertir):
    ruta = Path(ruta)
    if not ruta.is_file():
        raise CommandError(f'No existe el archivo: {ruta}')
    pares = set()
    for numero, linea in enumerate(ruta.read_text(encoding='utf-8-sig').splitlines(), 1):
        linea = linea.strip()
        if not linea.startswith('('):
            continue
        try:
            valor = ast.literal_eval(linea.rstrip(','))
        except (ValueError, SyntaxError) as error:
            raise CommandError(f'Línea inválida {numero} en {ruta.name}') from error
        if not isinstance(valor, tuple) or len(valor) != 2 or not all(isinstance(item, str) and item.strip() for item in valor):
            raise CommandError(f'Línea inválida {numero} en {ruta.name}')
        espanol, kichwa = valor if invertir else (valor[1], valor[0])
        pares.add((normalizar(kichwa), normalizar(espanol)))
    return pares


class Command(BaseCommand):
    help = ('Actualiza la marca editorial heredada desde archivos; la selección de juegos '
            'también acepta entradas generales claras. Por defecto solo informa.')

    def add_arguments(self, parser):
        parser.add_argument('--espanol-kichwa', required=True)
        parser.add_argument('--kichwa-espanol', required=True)
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        pares = leer_pares(options['espanol_kichwa'], True) | leer_pares(options['kichwa_espanol'], False)
        existentes = {
            (normalizar(palabra_kichwa), normalizar(traduccion_espanol)): pk
            for pk, palabra_kichwa, traduccion_espanol in Palabra.objects.values_list('pk', 'palabra_kichwa', 'traduccion_espanol')
        }
        ids = [existentes[par] for par in pares if par in existentes]
        self.stdout.write(f'Pares fuente: {len(pares)}; encontrados: {len(ids)}; ausentes: {len(pares) - len(ids)}.')
        if not options['apply']:
            self.stdout.write(self.style.WARNING('Modo simulación: no se cambió ninguna marca.'))
            return
        with transaction.atomic():
            retiradas = Palabra.objects.filter(apta_para_juegos=True).exclude(pk__in=ids).update(apta_para_juegos=False)
            Palabra.objects.filter(pk__in=ids).update(apta_para_juegos=True)
        self.stdout.write(self.style.SUCCESS(f'{len(ids)} palabras aptas; {retiradas} marcas heredadas retiradas.'))
