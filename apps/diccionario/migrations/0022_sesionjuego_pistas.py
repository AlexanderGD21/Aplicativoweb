from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('diccionario', '0021_busquedapopulardiaria'),
    ]

    operations = [
        migrations.AddField(
            model_name='sesionjuego',
            name='pistas_usadas',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='sesionjuego',
            name='pistas_palabras_ids',
            field=models.JSONField(default=list),
        ),
    ]
