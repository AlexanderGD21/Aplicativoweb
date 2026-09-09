import re
import shutil
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from apps.diccionario.models import Palabra


def normalizar(texto):
    texto = unicodedata.normalize('NFKC', texto)
    return re.sub(r'\s+', ' ', texto).strip().casefold()


class Command(BaseCommand):
    help = 'Migra audios existentes de static/audios a media/audios sin modificar la fuente.'

    def add_arguments(self, parser):
        parser.add_argument('--origen', default=str(Path(settings.BASE_DIR) / 'static' / 'audios'))
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        origen = Path(options['origen']).resolve()
        if not origen.is_dir():
            raise CommandError(f'No existe el directorio de audio: {origen}')
        archivos = {normalizar(archivo.stem): archivo for archivo in origen.glob('*.mp3') if archivo.is_file()}
        candidatas = [palabra for palabra in Palabra.objects.filter(Q(audio='') | Q(audio__isnull=True)).only('pk', 'palabra_kichwa', 'audio') if normalizar(palabra.palabra_kichwa) in archivos]
        self.stdout.write(f'Audios fuente: {len(archivos)}; coincidencias sin migrar: {len(candidatas)}.')
        if not options['apply']:
            self.stdout.write(self.style.WARNING('Modo simulación: no se copió ni registró ningún audio.'))
            return
        destino = Path(settings.MEDIA_ROOT) / 'audios'
        destino.mkdir(parents=True, exist_ok=True)
        with transaction.atomic():
            for palabra in candidatas:
                origen_audio = archivos[normalizar(palabra.palabra_kichwa)]
                destino_audio = destino / origen_audio.name
                if not destino_audio.exists():
                    shutil.copy2(origen_audio, destino_audio)
                palabra.audio.name = f'audios/{destino_audio.name}'
                palabra.save(update_fields=['audio'])
        self.stdout.write(self.style.SUCCESS(f'{len(candidatas)} audios copiados y asociados.'))
