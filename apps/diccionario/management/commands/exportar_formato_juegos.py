from django.core.management.base import BaseCommand
from apps.diccionario.models import Palabra
import csv
import os

class Command(BaseCommand):
    help = 'Exporta ejemplos de formato para cargar palabras de juegos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--formato',
            type=str,
            choices=['python', 'csv', 'txt'],
            default='python',
            help='Formato de exportación (python, csv, txt)',
        )
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['kichwa-espanol', 'espanol-kichwa', 'ambos'],
            default='ambos',
            help='Tipo de palabras a exportar',
        )

    def handle(self, *args, **options):
        formato = options['formato']
        tipo = options['tipo']
        
        if formato == 'python':
            self.exportar_formato_python(tipo)
        elif formato == 'csv':
            self.exportar_formato_csv(tipo)
        elif formato == 'txt':
            self.exportar_formato_txt(tipo)

    def exportar_formato_python(self, tipo):
        """Exporta formato Python para copiar y pegar"""
        if tipo in ['kichwa-espanol', 'ambos']:
            self.stdout.write('\n# FORMATO PARA PALABRAS KICHWA-ESPAÑOL (751 palabras):')
            self.stdout.write('palabras_juegos_kichwa_espanol = [')
            self.stdout.write('    # Formato: (\'término_kichwa\', \'descripción_en_español\'),')
            self.stdout.write('    (\'inti\', \'Astro rey que nos da luz y calor durante el día\'),')
            self.stdout.write('    (\'killa\', \'Satélite natural de la Tierra que vemos en la noche\'),')
            self.stdout.write('    (\'yaku\', \'Líquido transparente e incoloro, esencial para la vida\'),')
            self.stdout.write('    # ... COPIA AQUÍ TUS 751 PALABRAS ...')
            self.stdout.write(']')
        
        if tipo in ['espanol-kichwa', 'ambos']:
            self.stdout.write('\n# FORMATO PARA PALABRAS ESPAÑOL-KICHWA (1550 palabras):')
            self.stdout.write('palabras_juegos_espanol_kichwa = [')
            self.stdout.write('    # Formato: (\'término_español\', \'descripción_en_kichwa\'),')
            self.stdout.write('    (\'sol\', \'Inti, kay pachapi achka ruphayta apamuk\'),')
            self.stdout.write('    (\'luna\', \'Killa, tutapi rikurik phuyu\'),')
            self.stdout.write('    (\'agua\', \'Yaku, kawsaypak ancha chaniyuk\'),')
            self.stdout.write('    # ... COPIA AQUÍ TUS 1550 PALABRAS ...')
            self.stdout.write(']')

    def exportar_formato_csv(self, tipo):
        """Exporta formato CSV"""
        if tipo in ['kichwa-espanol', 'ambos']:
            with open('formato_juegos_kichwa_espanol.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['termino_kichwa', 'descripcion_espanol'])
                writer.writerow(['inti', 'Astro rey que nos da luz y calor durante el día'])
                writer.writerow(['killa', 'Satélite natural de la Tierra que vemos en la noche'])
                writer.writerow(['yaku', 'Líquido transparente e incoloro, esencial para la vida'])
            self.stdout.write('Archivo creado: formato_juegos_kichwa_espanol.csv')
        
        if tipo in ['espanol-kichwa', 'ambos']:
            with open('formato_juegos_espanol_kichwa.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['termino_espanol', 'descripcion_kichwa'])
                writer.writerow(['sol', 'Inti, kay pachapi achka ruphayta apamuk'])
                writer.writerow(['luna', 'Killa, tutapi rikurik phuyu'])
                writer.writerow(['agua', 'Yaku, kawsaypak ancha chaniyuk'])
            self.stdout.write('Archivo creado: formato_juegos_espanol_kichwa.csv')

    def exportar_formato_txt(self, tipo):
        """Exporta formato de texto plano"""
        if tipo in ['kichwa-espanol', 'ambos']:
            with open('formato_juegos_kichwa_espanol.txt', 'w', encoding='utf-8') as file:
                file.write('FORMATO PARA PALABRAS KICHWA-ESPAÑOL (751 palabras)\n')
                file.write('Formato: (\'término_kichwa\', \'descripción_en_español\'),\n\n')
                file.write('(\'inti\', \'Astro rey que nos da luz y calor durante el día\'),\n')
                file.write('(\'killa\', \'Satélite natural de la Tierra que vemos en la noche\'),\n')
                file.write('(\'yaku\', \'Líquido transparente e incoloro, esencial para la vida\'),\n')
                file.write('# ... COPIA AQUÍ TUS 751 PALABRAS ...\n')
            self.stdout.write('Archivo creado: formato_juegos_kichwa_espanol.txt')
        
        if tipo in ['espanol-kichwa', 'ambos']:
            with open('formato_juegos_espanol_kichwa.txt', 'w', encoding='utf-8') as file:
                file.write('FORMATO PARA PALABRAS ESPAÑOL-KICHWA (1550 palabras)\n')
                file.write('Formato: (\'término_español\', \'descripción_en_kichwa\'),\n\n')
                file.write('(\'sol\', \'Inti, kay pachapi achka ruphayta apamuk\'),\n')
                file.write('(\'luna\', \'Killa, tutapi rikurik phuyu\'),\n')
                file.write('(\'agua\', \'Yaku, kawsaypak ancha chaniyuk\'),\n')
                file.write('# ... COPIA AQUÍ TUS 1550 PALABRAS ...\n')
            self.stdout.write('Archivo creado: formato_juegos_espanol_kichwa.txt')
