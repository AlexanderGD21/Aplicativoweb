from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('diccionario', '0007_fix_migration_state')]

    operations = [
        migrations.AddField(
            model_name='palabra',
            name='audio',
            field=models.FileField(blank=True, null=True, upload_to='audios/'),
        ),
    ]
