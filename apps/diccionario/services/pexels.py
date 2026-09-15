import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from django.conf import settings
import truststore


API_URL = 'https://api.pexels.com/v1/search'
MAX_JSON_BYTES = 5 * 1024 * 1024
MAX_IMAGE_BYTES = 20 * 1024 * 1024
USER_AGENT = 'DiccionarioKichwa/1.0'


class PexelsError(RuntimeError):
    pass


def contexto_tls_sistema():
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


class PexelsClient:
    def __init__(self, api_key=None, timeout=None):
        self.api_key = (api_key if api_key is not None else settings.PEXELS_API_KEY).strip()
        self.timeout = timeout if timeout is not None else settings.PEXELS_API_TIMEOUT
        if not self.api_key:
            raise PexelsError('Falta PEXELS_API_KEY en el archivo .env.')

    def buscar_fotos(self, consulta, por_pagina=3):
        parametros = urlencode({
            'query': consulta,
            'orientation': 'square',
            'size': 'medium',
            'locale': 'es-ES',
            'per_page': max(1, min(int(por_pagina), 20)),
        })
        solicitud = Request(
            f'{API_URL}?{parametros}',
            headers={'Authorization': self.api_key, 'User-Agent': USER_AGENT},
        )
        try:
            with urlopen(
                solicitud, timeout=self.timeout, context=contexto_tls_sistema(),
            ) as respuesta:
                contenido = respuesta.read(MAX_JSON_BYTES + 1)
                if len(contenido) > MAX_JSON_BYTES:
                    raise PexelsError('La respuesta de Pexels superó el tamaño permitido.')
                datos = json.loads(contenido.decode('utf-8'))
                limite = respuesta.headers.get('X-Ratelimit-Limit')
                restantes = respuesta.headers.get('X-Ratelimit-Remaining')
                reinicio = respuesta.headers.get('X-Ratelimit-Reset')
        except HTTPError as error:
            if error.code == 401:
                raise PexelsError('Pexels rechazó la clave de API.') from error
            if error.code == 429:
                raise PexelsError('Se alcanzó el límite de solicitudes de Pexels.') from error
            raise PexelsError(f'Pexels respondió con HTTP {error.code}.') from error
        except (URLError, TimeoutError) as error:
            detalle = getattr(error, 'reason', str(error))
            raise PexelsError(f'No se pudo conectar con Pexels: {detalle}.') from error
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as error:
            raise PexelsError('Pexels devolvió una respuesta inválida.') from error

        fotos = []
        for foto in datos.get('photos', []):
            fuente = foto.get('src') or {}
            url_imagen = fuente.get('large2x') or fuente.get('large') or fuente.get('original')
            if not all((foto.get('id'), foto.get('url'), url_imagen, foto.get('photographer'))):
                continue
            fotos.append({
                'pexels_id': int(foto['id']),
                'url_foto': foto['url'],
                'url_imagen': url_imagen,
                'fotografo': foto['photographer'],
                'url_fotografo': foto.get('photographer_url') or 'https://www.pexels.com/',
                'descripcion_original': (foto.get('alt') or '')[:500],
                'ancho': int(foto.get('width') or 1),
                'alto': int(foto.get('height') or 1),
                'color_promedio': (foto.get('avg_color') or '')[:7],
            })
        return {
            'fotos': fotos,
            'limite': limite,
            'restantes': restantes,
            'reinicio': reinicio,
        }


def descargar_imagen_pexels(url, timeout=None):
    destino = urlparse(url)
    if destino.scheme != 'https' or destino.hostname != 'images.pexels.com':
        raise PexelsError('La candidata no usa el servidor oficial de imágenes de Pexels.')
    solicitud = Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urlopen(
            solicitud,
            timeout=timeout or settings.PEXELS_API_TIMEOUT,
            context=contexto_tls_sistema(),
        ) as respuesta:
            contenido = respuesta.read(MAX_IMAGE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as error:
        raise PexelsError('No se pudo descargar la candidata de Pexels.') from error
    if len(contenido) > MAX_IMAGE_BYTES:
        raise PexelsError('La imagen de Pexels superó 20 MB.')
    return contenido
