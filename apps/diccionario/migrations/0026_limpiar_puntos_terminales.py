from collections import defaultdict

from django.db import migrations


def limpiar(texto):
    return (texto or '').strip().rstrip('.').rstrip()


def pronunciacion_generada(texto):
    return texto if '-' in texto else '-'.join(texto[i:i + 2] for i in range(0, len(texto), 2))


def limpiar_puntos_terminales(apps, schema_editor):
    Palabra = apps.get_model('diccionario', 'Palabra')
    EjemploUso = apps.get_model('diccionario', 'EjemploUso')
    PalabraFavorita = apps.get_model('diccionario', 'PalabraFavorita')
    RelacionPalabra = apps.get_model('diccionario', 'RelacionPalabra')
    BusquedaPopularDiaria = apps.get_model('diccionario', 'BusquedaPopularDiaria')
    ActividadUsuario = apps.get_model('diccionario', 'ActividadUsuario')
    IntentoPalabraJuego = apps.get_model('diccionario', 'IntentoPalabraJuego')
    ProgresoPalabraJuego = apps.get_model('diccionario', 'ProgresoPalabraJuego')
    SesionJuego = apps.get_model('diccionario', 'SesionJuego')
    db = schema_editor.connection.alias

    grupos = defaultdict(list)
    for palabra in Palabra.objects.using(db).all():
        grupos[(limpiar(palabra.palabra_kichwa), limpiar(palabra.traduccion_espanol))].append(palabra)

    reemplazos = {}
    for (kichwa, espanol), grupo in grupos.items():
        if len(grupo) < 2:
            continue
        principal = next(
            (p for p in grupo if p.palabra_kichwa == kichwa and p.traduccion_espanol == espanol),
            min(grupo, key=lambda p: p.pk),
        )
        for duplicada in grupo:
            if duplicada.pk == principal.pk:
                continue
            reemplazos[duplicada.pk] = principal.pk
            principal.apta_para_juegos |= duplicada.apta_para_juegos
            if duplicada.apta_para_juegos:
                principal.dificultad_juego = duplicada.dificultad_juego
            principal.frecuencia_uso = max(principal.frecuencia_uso, duplicada.frecuencia_uso)
            principal.veces_vista += duplicada.veces_vista
            for campo in (
                'audio', 'definicion', 'notas_gramaticales', 'descripcion_juego_espanol',
                'descripcion_juego_kichwa', 'etimologia', 'sinonimos', 'ejemplo_uso',
            ):
                if not getattr(principal, campo) and getattr(duplicada, campo):
                    setattr(principal, campo, getattr(duplicada, campo))
        principal.save(using=db)

    for anterior, actual in reemplazos.items():
        EjemploUso.objects.using(db).filter(palabra_id=anterior).update(palabra_id=actual)
        ActividadUsuario.objects.using(db).filter(palabra_id=anterior).update(palabra_id=actual)
        IntentoPalabraJuego.objects.using(db).filter(palabra_id=anterior).update(palabra_id=actual)

        for favorita in PalabraFavorita.objects.using(db).filter(palabra_id=anterior):
            existente = PalabraFavorita.objects.using(db).filter(usuario_id=favorita.usuario_id, palabra_id=actual).first()
            if existente:
                if favorita.fecha_agregada < existente.fecha_agregada:
                    PalabraFavorita.objects.using(db).filter(pk=existente.pk).update(fecha_agregada=favorita.fecha_agregada)
                favorita.delete(using=db)
            else:
                favorita.palabra_id = actual
                favorita.save(using=db, update_fields=['palabra'])

        for busqueda in BusquedaPopularDiaria.objects.using(db).filter(palabra_id=anterior):
            existente = BusquedaPopularDiaria.objects.using(db).filter(palabra_id=actual, fecha=busqueda.fecha).first()
            if existente:
                existente.consultas += busqueda.consultas
                existente.save(using=db, update_fields=['consultas'])
                busqueda.delete(using=db)
            else:
                busqueda.palabra_id = actual
                busqueda.save(using=db, update_fields=['palabra'])

        for progreso in ProgresoPalabraJuego.objects.using(db).filter(palabra_id=anterior):
            existente = ProgresoPalabraJuego.objects.using(db).filter(usuario_id=progreso.usuario_id, palabra_id=actual).first()
            if existente:
                existente.intentos += progreso.intentos
                existente.respuestas_correctas += progreso.respuestas_correctas
                existente.mejor_racha = max(existente.mejor_racha, progreso.mejor_racha)
                if progreso.ultima_practica > existente.ultima_practica:
                    existente.racha_actual = progreso.racha_actual
                    existente.ultima_practica = progreso.ultima_practica
                precision = existente.respuestas_correctas / existente.intentos if existente.intentos else 0
                if existente.intentos >= 6 and precision >= 0.85 and existente.racha_actual >= 3:
                    existente.dominio = 'dominada'
                elif existente.intentos >= 3 and precision >= 0.6:
                    existente.dominio = 'practicando'
                elif existente.intentos:
                    existente.dominio = 'aprendiendo'
                ProgresoPalabraJuego.objects.using(db).filter(pk=existente.pk).update(
                    intentos=existente.intentos,
                    respuestas_correctas=existente.respuestas_correctas,
                    racha_actual=existente.racha_actual,
                    mejor_racha=existente.mejor_racha,
                    ultima_practica=existente.ultima_practica,
                    dominio=existente.dominio,
                )
                progreso.delete(using=db)
            else:
                ProgresoPalabraJuego.objects.using(db).filter(pk=progreso.pk).update(palabra_id=actual)

        for relacion in RelacionPalabra.objects.using(db).filter(origen_id=anterior) | RelacionPalabra.objects.using(db).filter(destino_id=anterior):
            origen = reemplazos.get(relacion.origen_id, relacion.origen_id)
            destino = reemplazos.get(relacion.destino_id, relacion.destino_id)
            if origen == destino or RelacionPalabra.objects.using(db).filter(
                origen_id=origen, destino_id=destino, tipo=relacion.tipo,
            ).exclude(pk=relacion.pk).exists():
                relacion.delete(using=db)
            else:
                relacion.origen_id = origen
                relacion.destino_id = destino
                relacion.save(using=db, update_fields=['origen', 'destino'])

    if reemplazos:
        for sesion in SesionJuego.objects.using(db).only('pk', 'palabras_ids', 'pistas_palabras_ids'):
            campos = []
            for campo in ('palabras_ids', 'pistas_palabras_ids'):
                original = getattr(sesion, campo)
                corregido = [reemplazos.get(pk, pk) for pk in original]
                if corregido != original:
                    setattr(sesion, campo, corregido)
                    campos.append(campo)
            if campos:
                sesion.save(using=db, update_fields=campos)
        Palabra.objects.using(db).filter(pk__in=reemplazos).delete()

    for palabra in Palabra.objects.using(db).all():
        kichwa = limpiar(palabra.palabra_kichwa)
        espanol = limpiar(palabra.traduccion_espanol)
        campos = {}
        if kichwa != palabra.palabra_kichwa:
            campos['palabra_kichwa'] = kichwa
            if palabra.pronunciacion == pronunciacion_generada(palabra.palabra_kichwa):
                campos['pronunciacion'] = pronunciacion_generada(kichwa)
        if espanol != palabra.traduccion_espanol:
            campos['traduccion_espanol'] = espanol
        if campos:
            Palabra.objects.using(db).filter(pk=palabra.pk).update(**campos)


class Migration(migrations.Migration):
    dependencies = [('diccionario', '0025_ejemplos_uso_revisados')]

    operations = [migrations.RunPython(limpiar_puntos_terminales)]
