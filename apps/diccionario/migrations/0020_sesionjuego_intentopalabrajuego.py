import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('diccionario', '0019_progresopalabrajuego'),
    ]

    operations = [
        migrations.CreateModel(
            name='SesionJuego',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('clave_anonima', models.CharField(blank=True, max_length=40)),
                ('tipo_juego', models.CharField(choices=[('traduccion', 'Traducción'), ('completar', 'Completar Palabras'), ('memoria', 'Juego de Memoria'), ('conectar', 'Conectar Traducciones'), ('sopa_letras', 'Sopa de Letras')], max_length=20)),
                ('dificultad', models.CharField(choices=[('facil', 'Fácil'), ('medio', 'Medio'), ('dificil', 'Difícil')], max_length=10)),
                ('palabras_ids', models.JSONField(default=list)),
                ('iniciada_en', models.DateTimeField(auto_now_add=True)),
                ('finalizada_en', models.DateTimeField(blank=True, null=True)),
                ('categoria', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='diccionario.categoria')),
                ('estadistica', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sesion_validada', to='diccionario.estadisticajuego')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sesiones_juego', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Sesión de juego', 'verbose_name_plural': 'Sesiones de juego', 'ordering': ['-iniciada_en']},
        ),
        migrations.CreateModel(
            name='IntentoPalabraJuego',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('correcta', models.BooleanField(default=False)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('palabra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='intentos_juego', to='diccionario.palabra')),
                ('sesion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='intentos', to='diccionario.sesionjuego')),
            ],
            options={'verbose_name': 'Intento de palabra', 'verbose_name_plural': 'Intentos de palabras', 'ordering': ['fecha']},
        ),
        migrations.AddIndex(
            model_name='intentopalabrajuego',
            index=models.Index(fields=['sesion', 'palabra', 'correcta'], name='intento_sesion_palabra_idx'),
        ),
    ]
