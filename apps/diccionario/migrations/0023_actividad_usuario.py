from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def recuperar_actividad_anterior(apps, schema_editor):
    Busqueda = apps.get_model('diccionario', 'HistorialBusqueda')
    Estadistica = apps.get_model('diccionario', 'EstadisticaJuego')
    Actividad = apps.get_model('diccionario', 'ActividadUsuario')
    alias = schema_editor.connection.alias

    def guardar_por_lotes(registros):
        lote = []
        for registro in registros:
            lote.append(registro)
            if len(lote) == 500:
                Actividad.objects.using(alias).bulk_create(lote, batch_size=500)
                lote.clear()
        if lote:
            Actividad.objects.using(alias).bulk_create(lote, batch_size=500)

    guardar_por_lotes(
        Actividad(usuario_id=busqueda.usuario_id, tipo='busqueda',
                  busqueda_id=busqueda.pk, fecha=busqueda.fecha_busqueda)
        for busqueda in Busqueda.objects.using(alias).exclude(usuario_id=None).iterator(chunk_size=500)
    )
    guardar_por_lotes(
        Actividad(usuario_id=partida.usuario_id, tipo='juego',
                  estadistica_id=partida.pk, fecha=partida.fecha_juego)
        for partida in Estadistica.objects.using(alias).iterator(chunk_size=500)
    )


class Migration(migrations.Migration):
    dependencies = [
        ('diccionario', '0022_sesionjuego_pistas'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActividadUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('busqueda', 'Búsqueda'), ('palabra', 'Palabra consultada'), ('juego', 'Partida terminada')], db_index=True, max_length=10)),
                ('fecha', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('busqueda', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='diccionario.historialbusqueda')),
                ('estadistica', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='diccionario.estadisticajuego')),
                ('palabra', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='diccionario.palabra')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actividades', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Actividad de usuario',
                'verbose_name_plural': 'Actividades de usuarios',
                'ordering': ['-fecha', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='actividadusuario',
            index=models.Index(fields=['usuario', '-fecha'], name='actividad_usuario_fecha_idx'),
        ),
        migrations.RunPython(recuperar_actividad_anterior, migrations.RunPython.noop),
    ]
