from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0006_recuperar_puntos_practica'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilusuario',
            name='pistas_extra_disponibles',
            field=models.PositiveSmallIntegerField(default=2),
        ),
    ]
