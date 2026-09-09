import apps.diccionario.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('diccionario', '0011_categoria_slug_state_sync')]

    operations = [
        migrations.AddField(
            model_name='palabra',
            name='categoria_propuesta',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='propuestas',
                to='diccionario.categoria',
            ),
        ),
        migrations.AlterField(
            model_name='palabra',
            name='audio',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='audios/',
                validators=[
                    django.core.validators.FileExtensionValidator(['mp3', 'ogg', 'wav']),
                    apps.diccionario.models.validar_tamano_audio,
                ],
            ),
        ),
    ]
