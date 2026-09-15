"""Prepara ejemplos documentados; nunca los publica sin revisión editorial."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.diccionario.models import EjemploUso, Palabra


MODULO = 'IST Tena, Módulo Kichwa (2023)'
NOTA_COTEJO = (
    'Cotejado visualmente con la tabla bilingüe de la página y sección citadas; '
    'no equivale a una validación lingüística independiente.'
)

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
    ('rimana', 'hablar, conversar', 'Ñuka rimani.', 'Yo hablo.', 24, '6.3'),
    ('rimana', 'hablar, conversar', 'Kan rimanki.', 'Tú hablas.', 24, '6.3'),
    ('rimana', 'hablar, conversar', 'Pay riman.', 'Él o ella habla.', 24, '6.3'),
    ('rimana', 'hablar, conversar', 'Ñukanchik rimanchik.', 'Nosotros hablamos.', 24, '6.3'),
    ('tarpuna', 'sembrar', 'Ñuka tarpuni.', 'Yo siembro.', 25, '6.3'),
    ('tarpuna', 'sembrar', 'Kan tarpunki.', 'Tú siembras.', 25, '6.3'),
    ('tarpuna', 'sembrar', 'Pay tarpun.', 'Él o ella siembra.', 25, '6.3'),
    ('tarpuna', 'sembrar', 'Ñukanchik tarpunchik.', 'Nosotros sembramos.', 25, '6.3'),
    ('mikuna', 'alimentarse', 'Kan mikunki.', 'Tú comes.', 25, '6.4'),
    ('mikuna', 'alimentarse', 'Pay mikun.', 'Él o ella come.', 25, '6.4'),
    ('mikuna', 'alimentarse', 'Ñukanchik mikunchik.', 'Nosotros comemos.', 25, '6.4'),
    ('mikuna', 'alimentarse', 'Paykuna mikunkuna.', 'Ellos o ellas comen.', 25, '6.4'),
    ('killkana', 'escribir', 'Ñuka killkani.', 'Yo escribo.', 25, '6.5'),
    ('killkana', 'escribir', 'Kan killkanki.', 'Tú escribes.', 25, '6.5'),
    ('killkana', 'escribir', 'Pay killkan.', 'Él o ella escribe.', 25, '6.5'),
    ('killkana', 'escribir', 'Ñukanchik killkanchik.', 'Nosotros escribimos.', 25, '6.5'),
    ('takina', 'cantar', 'Ñuka takini.', 'Yo canto.', 25, '6.5'),
    ('takina', 'cantar', 'Kan takinki.', 'Tú cantas.', 25, '6.5'),
    ('takina', 'cantar', 'Pay takin.', 'Él o ella canta.', 25, '6.5'),
    ('takina', 'cantar', 'Ñukanchik takinchik.', 'Nosotros cantamos.', 25, '6.5'),
)


class Command(BaseCommand):
    help = 'Prepara ejemplos del módulo de IST Tena y puede publicarlos con cotejo documental.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--publicar-cotejados', action='store_true',
            help='Publica los ejemplos tras registrar que fueron cotejados visualmente con las páginas citadas.',
        )

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
        ejemplos = []
        for palabra, oracion, traduccion, fuente in preparados:
            ejemplo, creado = EjemploUso.objects.get_or_create(
                palabra=palabra, oracion_kichwa=oracion,
                defaults={'traduccion_espanol': traduccion, 'fuente': fuente},
            )
            creados += int(creado)
            ejemplos.append(ejemplo)
        publicados = 0
        if options['publicar_cotejados']:
            fecha = timezone.now()
            for ejemplo in ejemplos:
                if (
                    ejemplo.estado == 'publicado'
                    and ejemplo.tipo_revision == 'documental'
                    and ejemplo.nota_revision == NOTA_COTEJO
                    and ejemplo.fecha_revision
                    and ejemplo.revisado_por_id is None
                ):
                    continue
                ejemplo.estado = 'publicado'
                ejemplo.tipo_revision = 'documental'
                ejemplo.nota_revision = NOTA_COTEJO
                ejemplo.revisado_por = None
                ejemplo.fecha_revision = fecha
                ejemplo.save(update_fields=[
                    'estado', 'tipo_revision', 'nota_revision', 'revisado_por',
                    'fecha_revision', 'fecha_actualizacion',
                ])
                publicados += 1
        self.stdout.write(self.style.SUCCESS(
            f'{creados} ejemplos nuevos; {len(preparados) - creados} ya existían; '
            f'{publicados} publicados con cotejo documental.'
        ))
