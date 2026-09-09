from django.db import migrations


def crear_indice_correo_unico(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    correos = {}
    for correo in User.objects.exclude(email='').values_list('email', flat=True):
        clave = correo.strip().lower()
        correos[clave] = correos.get(clave, 0) + 1
    duplicados = [correo for correo, total in correos.items() if total > 1]
    if duplicados:
        raise RuntimeError(
            'No se puede crear el índice único de correo: hay direcciones duplicadas. '
            'Corrige los correos repetidos antes de migrar.'
        )
    schema_editor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS auth_user_email_ci_unique "
        "ON auth_user (LOWER(email)) WHERE email <> ''"
    )


def eliminar_indice_correo_unico(apps, schema_editor):
    schema_editor.execute('DROP INDEX IF EXISTS auth_user_email_ci_unique')


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0002_perfilusuario_telefono_alter_perfilusuario_avatar_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_indice_correo_unico, eliminar_indice_correo_unico),
    ]
