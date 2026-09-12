from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0004_perfilusuario_consentimiento_legal'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilusuario',
            name='participa_ranking',
            field=models.BooleanField(default=False),
        ),
    ]
