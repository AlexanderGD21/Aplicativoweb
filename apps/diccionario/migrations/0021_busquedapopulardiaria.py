import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('diccionario', '0020_sesionjuego_intentopalabrajuego'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusquedaPopularDiaria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(db_index=True, default=django.utils.timezone.localdate)),
                ('consultas', models.PositiveIntegerField(default=0)),
                ('palabra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='busquedas_populares', to='diccionario.palabra')),
            ],
            options={
                'verbose_name': 'Búsqueda popular diaria',
                'verbose_name_plural': 'Búsquedas populares diarias',
            },
        ),
        migrations.AddConstraint(
            model_name='busquedapopulardiaria',
            constraint=models.UniqueConstraint(fields=('palabra', 'fecha'), name='busqueda_popular_palabra_fecha'),
        ),
    ]
