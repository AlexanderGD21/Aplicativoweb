from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from apps.diccionario.services.ia_kichwa import obtener_configuracion_ia


class Command(BaseCommand):
    help = 'Verifica la configuración de IA sin conectarse ni mostrar secretos.'

    def handle(self, *args, **options):
        try:
            configuracion = obtener_configuracion_ia()
        except ImproperlyConfigured as error:
            raise CommandError(str(error)) from error
        if configuracion is None:
            self.stdout.write('IA de Kichwa: desactivada (KICHWA_AI_PROVIDER=none).')
            return
        self.stdout.write(self.style.SUCCESS(f'IA configurada: proveedor={configuracion.proveedor}, timeout={configuracion.timeout}s.'))
