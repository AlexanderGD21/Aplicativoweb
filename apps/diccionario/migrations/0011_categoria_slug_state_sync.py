from django.db import migrations, models


def add_slug_if_missing(apps, schema_editor):
    categoria = apps.get_model('diccionario', 'Categoria')
    columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(), categoria._meta.db_table
        )
    }
    if 'slug' not in columns:
        field = models.SlugField(blank=True, unique=True)
        field.set_attributes_from_name('slug')
        field.model = categoria
        schema_editor.add_field(categoria, field)


class Migration(migrations.Migration):
    dependencies = [('diccionario', '0010_palabra_estado_revision_alter_palabra_categoria')]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(add_slug_if_missing, migrations.RunPython.noop)],
            state_operations=[
                migrations.AddField(
                    model_name='categoria',
                    name='slug',
                    field=models.SlugField(blank=True, unique=True),
                ),
            ],
        ),
    ]
