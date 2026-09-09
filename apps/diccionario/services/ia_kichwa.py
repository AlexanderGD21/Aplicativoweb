from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


@dataclass(frozen=True)
class ConfiguracionIAKichwa:
    proveedor: str
    base_url: str
    modelo: str
    timeout: int


def obtener_configuracion_ia():
    """Valida el contrato de IA sin conectarse ni revelar secretos."""
    proveedor = settings.KICHWA_AI_PROVIDER
    if proveedor == 'none':
        return None
    if proveedor != 'vits_http':
        raise ImproperlyConfigured('KICHWA_AI_PROVIDER debe ser "none" o "vits_http".')
    if not settings.KICHWA_AI_BASE_URL.startswith(('https://', 'http://')):
        raise ImproperlyConfigured('KICHWA_AI_BASE_URL debe ser una URL HTTP(S).')
    if not settings.KICHWA_AI_API_KEY:
        raise ImproperlyConfigured('KICHWA_AI_API_KEY es obligatoria para vits_http.')
    if not 1 <= settings.KICHWA_AI_TIMEOUT <= 60:
        raise ImproperlyConfigured('KICHWA_AI_TIMEOUT debe estar entre 1 y 60 segundos.')
    return ConfiguracionIAKichwa(proveedor, settings.KICHWA_AI_BASE_URL.rstrip('/'), settings.KICHWA_AI_MODEL, settings.KICHWA_AI_TIMEOUT)
