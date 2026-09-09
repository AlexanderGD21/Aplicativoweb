from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('diccionario', '0008_palabra_audio')]

    operations = [
        migrations.AlterField(
            model_name='palabra',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('kichwa_espanol', 'Kichwa-Español'),
                    ('espanol_kichwa', 'Español-Kichwa'),
                ],
                default='kichwa_espanol',
                max_length=20,
            ),
        ),
    ]
