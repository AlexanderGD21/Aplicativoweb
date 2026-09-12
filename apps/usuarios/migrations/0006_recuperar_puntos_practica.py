from django.db import migrations
from django.db.models import Count


def recuperar_puntos(apps, schema_editor):
    Progreso = apps.get_model('diccionario', 'ProgresoPalabraJuego')
    Perfil = apps.get_model('usuarios', 'PerfilUsuario')
    avances = Progreso.objects.using(schema_editor.connection.alias).filter(
        respuestas_correctas__gt=0,
    ).values('usuario_id').annotate(palabras=Count('id'))
    for avance in avances.iterator():
        puntos = avance['palabras'] * 10
        Perfil.objects.using(schema_editor.connection.alias).filter(
            usuario_id=avance['usuario_id'], puntos_totales__lt=puntos,
        ).update(puntos_totales=puntos)


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0005_perfilusuario_participa_ranking'),
        ('diccionario', '0020_sesionjuego_intentopalabrajuego'),
    ]

    operations = [
        migrations.RunPython(recuperar_puntos, migrations.RunPython.noop),
    ]
