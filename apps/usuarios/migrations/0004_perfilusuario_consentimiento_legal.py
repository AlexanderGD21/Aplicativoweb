from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_unique_email_case_insensitive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perfilusuario',
            name='notificaciones_email',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='terminos_aceptados_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='version_privacidad',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='version_terminos',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
