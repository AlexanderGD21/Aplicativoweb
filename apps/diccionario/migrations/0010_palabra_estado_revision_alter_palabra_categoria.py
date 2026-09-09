from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('diccionario', '0009_alter_palabra_tipo')]

    operations = [
        migrations.AddField(
            model_name='palabra',
            name='estado_revision',
            field=models.CharField(
                choices=[
                    ('pendiente', 'Pendiente de revisión'),
                    ('revisada', 'Revisada'),
                    ('validada', 'Validada'),
                ],
                db_index=True,
                default='pendiente',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='palabra',
            name='categoria',
            field=models.ForeignKey(
                help_text='No se puede eliminar una categoría mientras tenga palabras asociadas.',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='palabras',
                to='diccionario.categoria',
            ),
        ),
    ]
