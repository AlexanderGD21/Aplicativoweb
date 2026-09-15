import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.diccionario.models import Palabra, limpiar_termino, normalizar_texto_busqueda


CAMPOS = (
    'id', 'palabra_kichwa', 'traduccion_espanol', 'categoria',
    'traduccion_ingles', 'definicion_ingles', 'estado_revision_ingles',
)
ESTADOS = {valor for valor, _ in Palabra.ESTADO_REVISION_CHOICES}


class Command(BaseCommand):
    help = 'Exporta o importa el flujo editorial de traducciones inglesas mediante CSV.'

    def add_arguments(self, parser):
        grupo = parser.add_mutually_exclusive_group(required=True)
        grupo.add_argument('--exportar', metavar='ARCHIVO')
        grupo.add_argument('--importar', metavar='ARCHIVO')
        parser.add_argument('--estado', choices=sorted(ESTADOS), help='Filtra el estado al exportar.')
        parser.add_argument('--todas', action='store_true', help='Incluye entradas inactivas al exportar.')

    def handle(self, *args, **options):
        if options['exportar']:
            self._exportar(Path(options['exportar']), options['estado'], options['todas'])
        else:
            self._importar(Path(options['importar']))

    def _exportar(self, archivo, estado, incluir_inactivas):
        palabras = Palabra.objects.select_related('categoria').order_by('id')
        if not incluir_inactivas:
            palabras = palabras.filter(activa=True)
        if estado:
            palabras = palabras.filter(estado_revision_ingles=estado)
        archivo.parent.mkdir(parents=True, exist_ok=True)
        with archivo.open('w', encoding='utf-8-sig', newline='') as salida:
            escritor = csv.DictWriter(salida, fieldnames=CAMPOS)
            escritor.writeheader()
            for palabra in palabras.iterator(chunk_size=500):
                escritor.writerow({
                    'id': palabra.pk,
                    'palabra_kichwa': palabra.palabra_kichwa,
                    'traduccion_espanol': palabra.traduccion_espanol,
                    'categoria': palabra.categoria.nombre,
                    'traduccion_ingles': palabra.traduccion_ingles,
                    'definicion_ingles': palabra.definicion_ingles,
                    'estado_revision_ingles': palabra.estado_revision_ingles,
                })
        self.stdout.write(self.style.SUCCESS(f'Exportadas {palabras.count()} entradas a {archivo.resolve()}'))

    def _importar(self, archivo):
        if not archivo.is_file():
            raise CommandError(f'No se encontró el archivo: {archivo}')
        with archivo.open('r', encoding='utf-8-sig', newline='') as entrada:
            lector = csv.DictReader(entrada)
            faltantes = set(CAMPOS) - set(lector.fieldnames or ())
            if faltantes:
                raise CommandError(f'Faltan columnas requeridas: {", ".join(sorted(faltantes))}')
            filas = list(lector)

        ids_vistos = set()
        preparadas = []
        errores = []
        for numero, fila in enumerate(filas, start=2):
            try:
                palabra_id = int((fila['id'] or '').strip())
            except ValueError:
                errores.append(f'fila {numero}: id inválido')
                continue
            if palabra_id in ids_vistos:
                errores.append(f'fila {numero}: id {palabra_id} repetido')
                continue
            ids_vistos.add(palabra_id)
            estado = (fila['estado_revision_ingles'] or 'pendiente').strip().lower()
            traduccion = limpiar_termino(fila['traduccion_ingles'])
            if estado not in ESTADOS:
                errores.append(f'fila {numero}: estado {estado!r} inválido')
            elif estado in {'revisada', 'validada'} and not traduccion:
                errores.append(f'fila {numero}: una traducción {estado} no puede estar vacía')
            preparadas.append((numero, palabra_id, traduccion, (fila['definicion_ingles'] or '').strip(), estado))
        existentes = set(Palabra.objects.filter(pk__in=ids_vistos).values_list('pk', flat=True))
        for numero, palabra_id, *_ in preparadas:
            if palabra_id not in existentes:
                errores.append(f'fila {numero}: no existe la entrada {palabra_id}')
        if errores:
            raise CommandError('No se importó ninguna fila:\n- ' + '\n- '.join(errores[:30]))

        with transaction.atomic():
            for _, palabra_id, traduccion, definicion, estado in preparadas:
                Palabra.objects.filter(pk=palabra_id).update(
                    traduccion_ingles=traduccion,
                    definicion_ingles=definicion,
                    estado_revision_ingles=estado,
                    busqueda_ingles=normalizar_texto_busqueda(traduccion),
                )
        self.stdout.write(self.style.SUCCESS(f'Importadas {len(preparadas)} traducciones desde {archivo.resolve()}'))
