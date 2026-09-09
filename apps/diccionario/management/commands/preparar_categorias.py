from django.core.management.base import BaseCommand

from apps.diccionario.models import Categoria


CATEGORIAS_BASE = [
    ('Alimentación', 'Comidas, bebidas, cultivos y preparación de alimentos.', '#E67E22'),
    ('Animales', 'Fauna doméstica, silvestre y sus partes.', '#16A085'),
    ('Cuerpo y salud', 'Partes del cuerpo, bienestar y cuidado.', '#E74C3C'),
    ('Cultura y cosmovisión', 'Fiestas, prácticas comunitarias y saberes ancestrales.', '#8E44AD'),
    ('Familia y sociedad', 'Parentesco, personas, comunidad y relaciones sociales.', '#2980B9'),
    ('Gramática y expresiones', 'Partículas, conectores, pronombres y frases frecuentes.', '#34495E'),
    ('Naturaleza y clima', 'Agua, relieve, clima y fenómenos naturales.', '#27AE60'),
    ('Plantas y agricultura', 'Flora, siembra, cosecha y herramientas agrícolas.', '#2ECC71'),
    ('Tiempo y calendario', 'Días, meses, estaciones, cantidades y tiempo.', '#F1C40F'),
    ('Vida diaria y objetos', 'Hogar, vestimenta, transporte y objetos cotidianos.', '#D35400'),
    ('Acciones y verbos', 'Acciones, movimientos y procesos.', '#C0392B'),
    ('Cualidades y descripciones', 'Adjetivos, estados y características.', '#7F8C8D'),
]


class Command(BaseCommand):
    help = 'Crea una taxonomía base sin reclasificar palabras existentes.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        existentes = set(Categoria.objects.values_list('nombre', flat=True))
        pendientes = [categoria for categoria in CATEGORIAS_BASE if categoria[0] not in existentes]
        if not options['apply']:
            self.stdout.write(self.style.WARNING('Modo simulación: no se modificó ninguna categoría.'))
            for nombre, _, _ in pendientes:
                self.stdout.write(f'  Se crearía: {nombre}')
            return
        for nombre, descripcion, color in pendientes:
            Categoria.objects.create(nombre=nombre, descripcion=descripcion, color=color)
        self.stdout.write(self.style.SUCCESS(f'{len(pendientes)} categorías creadas; ninguna palabra fue reclasificada.'))
