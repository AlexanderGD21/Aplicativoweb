from django.db import migrations


INDEXES = (
    ('palabra_kichwa_trgm_idx', 'palabra_kichwa'),
    ('palabra_espanol_trgm_idx', 'traduccion_espanol'),
    ('palabra_definicion_trgm_idx', 'definicion'),
    ('palabra_pronuncia_trgm_idx', 'pronunciacion'),
)


def crear_indices_trigram(apps, schema_editor):
    """Acelera ILIKE/contains en PostgreSQL; SQLite continúa sin cambios."""
    if schema_editor.connection.vendor != 'postgresql':
        return
    # En proveedores administrados la extensión puede no estar autorizada. La
    # migración no debe bloquear el despliegue: usa índices trigram solo cuando
    # pg_trgm esté disponible y deja una migración limpia en caso contrario.
    schema_editor.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN
                BEGIN
                    CREATE EXTENSION pg_trgm;
                EXCEPTION WHEN insufficient_privilege THEN
                    RAISE NOTICE 'pg_trgm no está disponible para este usuario';
                END;
            END IF;
        END
        $$;
        """
    )
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')")
        extension_disponible = cursor.fetchone()[0]
    if not extension_disponible:
        return
    for nombre, campo in INDEXES:
        schema_editor.execute(
            f'CREATE INDEX IF NOT EXISTS {nombre} '
            f'ON diccionario_palabra USING GIN ({campo} gin_trgm_ops)'
        )


def eliminar_indices_trigram(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    for nombre, _ in INDEXES:
        schema_editor.execute(f'DROP INDEX IF EXISTS {nombre}')


class Migration(migrations.Migration):
    dependencies = [
        ('diccionario', '0014_palabra_palabra_busq_kichwa_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_indices_trigram, eliminar_indices_trigram),
    ]
