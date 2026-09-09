import apps.diccionario.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('diccionario', '0012_palabra_categoria_propuesta_alter_palabra_audio')]

    operations = [
        migrations.AlterField(
            model_name='palabra',
            name='audio',
            field=models.FileField(blank=True, help_text='Archivo de pronunciación (MP3, OGG o WAV; máximo 10 MB).', null=True, upload_to='audios/', validators=[django.core.validators.FileExtensionValidator(['mp3', 'ogg', 'wav']), apps.diccionario.models.validar_tamano_audio]),
        ),
        migrations.AlterField(
            model_name='palabra',
            name='categoria_propuesta',
            field=models.ForeignKey(blank=True, help_text='Sugerencia automática pendiente de validación humana.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='propuestas', to='diccionario.categoria'),
        ),
        migrations.AlterField(
            model_name='palabra',
            name='estado_revision',
            field=models.CharField(choices=[('pendiente', 'Pendiente de revisión'), ('revisada', 'Revisada'), ('validada', 'Validada')], db_index=True, default='pendiente', help_text='Control interno de la curación lingüística de la entrada.', max_length=10),
        ),
    ]
