from django.core.management.base import BaseCommand
import csv
import json

class Command(BaseCommand):
    help = 'Exporta un archivo de ejemplo para cargar palabras masivamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--formato',
            type=str,
            choices=['csv', 'json', 'python'],
            default='python',
            help='Formato del archivo de salida',
        )

    def handle(self, *args, **options):
        formato = options['formato']
        
        if formato == 'csv':
            self.generar_csv()
        elif formato == 'json':
            self.generar_json()
        else:
            self.generar_python()

    def generar_csv(self):
        """Genera un archivo CSV de ejemplo"""
        with open('palabras_ejemplo.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['palabra_kichwa', 'traduccion_espanol', 'descripcion'])
            writer.writerow(['mama', 'madre', 'Mujer que ha dado a luz'])
            writer.writerow(['taita', 'padre', 'Hombre que ha engendrado hijos'])
            writer.writerow(['wawa', 'niño/bebé', 'Persona de corta edad'])
        
        self.stdout.write('Archivo palabras_ejemplo.csv generado')

    def generar_json(self):
        """Genera un archivo JSON de ejemplo"""
        datos = [
            {
                'palabra_kichwa': 'mama',
                'traduccion_espanol': 'madre',
                'descripcion': 'Mujer que ha dado a luz'
            },
            {
                'palabra_kichwa': 'taita',
                'traduccion_espanol': 'padre',
                'descripcion': 'Hombre que ha engendrado hijos'
            }
        ]
        
        with open('palabras_ejemplo.json', 'w', encoding='utf-8') as jsonfile:
            json.dump(datos, jsonfile, ensure_ascii=False, indent=2)
        
        self.stdout.write('Archivo palabras_ejemplo.json generado')

    def generar_python(self):
        """Genera un archivo Python de ejemplo"""
        contenido = '''# Archivo de ejemplo para cargar palabras
# Copia este formato y pega tus palabras

palabras_kichwa_espanol = [
    ('mama', 'madre', 'Mujer que ha dado a luz'),
    ('taita', 'padre', 'Hombre que ha engendrado hijos'),
    ('wawa', 'niño/bebé', 'Persona de corta edad'),
    # Agrega más palabras aquí...
]

palabras_espanol_kichwa = [
    ('madre', 'mama', 'Mujer que ha dado a luz'),
    ('padre', 'taita', 'Hombre que ha engendrado hijos'),
    ('niño', 'wawa', 'Persona de corta edad'),
    # Agrega más palabras aquí...
]
'''
        
        with open('palabras_ejemplo.py', 'w', encoding='utf-8') as pyfile:
            pyfile.write(contenido)
        
        self.stdout.write('Archivo palabras_ejemplo.py generado')
