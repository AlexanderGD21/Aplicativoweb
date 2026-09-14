"""Prepara ejemplos documentados; nunca los publica sin revisión editorial."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.diccionario.models import EjemploUso, Palabra


MODULO = 'IST Tena, Módulo Kichwa (2023)'

# Página PDF (1 basada), no la numeración interna que reinicia en cada eje.
EJEMPLOS = (
    ('shamuna', 'venir', 'Kayman shamuy.', 'Ven para acá.', 18, '5.6'),
    ('shamuna', 'venir', 'Kayman shamupay.', 'Ven para acá por favor.', 18, '5.6'),
    ('mikuna', 'alimentarse', 'Ama mikuychu.', 'No comas.', 18, '5.6'),
    ('mikuna', 'alimentarse', 'Ñuka mikuni.', 'Yo como.', 83, '14.13'),
    ('ayllu', 'familia', 'Shamuk watakaman llakishka ayllukuna.',
     'Hasta el próximo año querida familia.', 17, '5.5'),
    ('rina', 'ir, viajar', 'Mayman rinki?', '¿Adónde vas?', 29, '6.10'),
    ('apana', 'llevar', 'Imata apanki?', '¿Qué llevas?', 29, '6.10'),
    ('mashi', 'compañero, amigo', 'Pitak kanpak mashika kan?',
     '¿Quién es tu amigo?', 29, '6.10'),
    ('kiwa', 'hierba en general', 'Imapak kiwataka apanki?',
     '¿Para qué llevas la hierba?', 29, '6.10'),
)


class Command(BaseCommand):
    help = 'Carga como borradores nueve ejemplos cotejados con el módulo autorizado de IST Tena.'

    @transaction.atomic
    def handle(self, *args, **options):
        preparados = []
        problemas = []
        for kichwa, significado, oracion, traduccion, pagina, seccion in EJEMPLOS:
            try:
                palabra = Palabra.objects.get(
                    palabra_kichwa=kichwa, traduccion_espanol=significado, activa=True,
                )
            except Palabra.DoesNotExist:
                problemas.append(f'No existe la entrada {kichwa} / {significado}.')
                continue
            fuente = f'{MODULO}, página PDF {pagina}, sección {seccion}'
            previo = EjemploUso.objects.filter(palabra=palabra, oracion_kichwa=oracion).first()
            if previo and (previo.traduccion_espanol != traduccion or previo.fuente != fuente):
                problemas.append(f'El ejemplo de {kichwa} ya existe con otro contenido: {oracion}')
            preparados.append((palabra, oracion, traduccion, fuente))
        if problemas:
            raise CommandError('No se importó nada:\n' + '\n'.join(problemas))

        creados = 0
        for palabra, oracion, traduccion, fuente in preparados:
            _, creado = EjemploUso.objects.get_or_create(
                palabra=palabra, oracion_kichwa=oracion,
                defaults={'traduccion_espanol': traduccion, 'fuente': fuente},
            )
            creados += int(creado)
        self.stdout.write(self.style.SUCCESS(
            f'{creados} borradores nuevos; {len(preparados) - creados} ya existían. '
            'La publicación requiere revisión en Django Admin.'
        ))
