from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.diccionario.models import CandidataImagenPexels
from apps.diccionario.services.pexels import PexelsError, descargar_imagen_pexels


class Command(BaseCommand):
    help = 'Descarga las candidatas Pexels seleccionadas como WebP; no las publica.'

    def add_arguments(self, parser):
        parser.add_argument('--lote', type=int, required=True)
        parser.add_argument('--cantidad', type=int, default=100)

    def handle(self, *args, **options):
        if options['cantidad'] < 1:
            raise CommandError('--cantidad debe ser mayor que cero.')
        candidatas = CandidataImagenPexels.objects.filter(
            preparacion__lote=options['lote'],
            preparacion__estado='preparada',
            seleccionada=True,
        ).select_related('preparacion__palabra').order_by('preparacion__orden_lote')[:options['cantidad']]
        candidatas = list(candidatas)
        if not candidatas:
            raise CommandError('No hay candidatas seleccionadas para descargar en ese lote.')

        raiz_estatica = Path(settings.STATICFILES_DIRS[0])
        directorio = raiz_estatica / 'img' / 'vocabulario' / 'pexels'
        directorio.mkdir(parents=True, exist_ok=True)
        descargadas = 0
        for candidata in candidatas:
            try:
                contenido = descargar_imagen_pexels(candidata.url_imagen)
                with Image.open(BytesIO(contenido)) as imagen:
                    imagen = imagen.convert('RGB')
                    lado = min(imagen.size)
                    izquierda = (imagen.width - lado) // 2
                    superior = (imagen.height - lado) // 2
                    imagen = imagen.crop((izquierda, superior, izquierda + lado, superior + lado))
                    imagen = imagen.resize((768, 768), Image.Resampling.LANCZOS)
                    nombre = slugify(
                        f'{candidata.preparacion.palabra.palabra_kichwa}-'
                        f'{candidata.preparacion.palabra.traduccion_espanol}'
                    )[:90]
                    ruta_relativa = f'img/vocabulario/pexels/{nombre}-{candidata.pexels_id}.webp'
                    imagen.save(raiz_estatica / ruta_relativa, 'WEBP', quality=84, method=6)
            except (PexelsError, UnidentifiedImageError, OSError) as error:
                raise CommandError(f'No se pudo preparar Pexels {candidata.pexels_id}: {error}') from error

            preparacion = candidata.preparacion
            preparacion.ruta_candidata = ruta_relativa
            preparacion.proveedor_candidato = 'pexels'
            preparacion.autor_candidato = candidata.fotografo
            preparacion.autor_candidato_url = candidata.url_fotografo
            preparacion.fuente_candidata_url = candidata.url_foto
            preparacion.credito_candidato = f'Fotografía de {candidata.fotografo} en Pexels.'[:240]
            preparacion.estado = 'generada'
            preparacion.save(update_fields=[
                'ruta_candidata', 'proveedor_candidato', 'autor_candidato',
                'autor_candidato_url', 'fuente_candidata_url', 'credito_candidato',
                'estado', 'fecha_actualizacion',
            ])
            descargadas += 1
        self.stdout.write(self.style.SUCCESS(
            f'{descargadas} fotografías convertidas a WebP y enviadas a revisión.'
        ))
