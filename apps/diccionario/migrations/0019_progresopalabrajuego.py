from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('diccionario', '0018_taxonomia_busqueda_clasificacion'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgresoPalabraJuego',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intentos', models.PositiveIntegerField(default=0)),
                ('respuestas_correctas', models.PositiveIntegerField(default=0)),
                ('racha_actual', models.PositiveIntegerField(default=0)),
                ('mejor_racha', models.PositiveIntegerField(default=0)),
                ('dominio', models.CharField(choices=[('nueva', 'Nueva'), ('aprendiendo', 'Aprendiendo'), ('practicando', 'En práctica'), ('dominada', 'Dominada')], db_index=True, default='nueva', max_length=12)),
                ('ultima_practica', models.DateTimeField(auto_now=True)),
                ('palabra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progreso_juegos', to='diccionario.palabra')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progreso_juegos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Progreso de palabra en juegos',
                'verbose_name_plural': 'Progreso de palabras en juegos',
                'ordering': ['dominio', 'ultima_practica'],
            },
        ),
        migrations.AddConstraint(
            model_name='progresopalabrajuego',
            constraint=models.UniqueConstraint(fields=('usuario', 'palabra'), name='progreso_juego_usuario_palabra'),
        ),
        migrations.AddIndex(
            model_name='progresopalabrajuego',
            index=models.Index(fields=['usuario', 'dominio', 'ultima_practica'], name='progreso_juego_prioridad_idx'),
        ),
    ]
