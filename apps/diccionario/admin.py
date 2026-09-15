from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib.staticfiles import finders
from django.db import transaction
from django.db.models import F
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    ActividadUsuario, CandidataImagenPexels, Categoria, EstadisticaJuego, HistorialBusqueda,
    EjemploUso, IntentoPalabraJuego, Palabra, PalabraFavorita, PreparacionImagenVocabulario,
    ProgresoPalabraJuego, SesionJuego,
)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nombre_ingles', 'grupo', 'orden', 'color', 'fecha_creacion']
    list_filter = ['grupo', 'fecha_creacion']
    search_fields = ['nombre', 'nombre_ingles', 'descripcion', 'descripcion_ingles']
    ordering = ['grupo', 'orden', 'nombre']

@admin.register(Palabra)
class PalabraAdmin(admin.ModelAdmin):
    list_display = [
        'palabra_kichwa', 'traduccion_espanol', 'traduccion_ingles', 'categoria', 'categoria_propuesta',
        'estado_revision', 'estado_revision_ingles', 'clasificacion_confianza', 'dificultad', 'apta_para_juegos', 'activa', 'veces_vista'
    ]
    list_filter = [
        'categoria', 'categoria_propuesta', 'estado_revision', 'estado_revision_ingles', 'clasificacion_confianza',
        'dificultad', 'nivel_dificultad', 'tipo',
        'apta_para_juegos', 'activa', 'fecha_creacion'
    ]
    search_fields = ['palabra_kichwa', 'traduccion_espanol', 'traduccion_ingles', 'definicion', 'definicion_ingles']
    ordering = ['palabra_kichwa']
    readonly_fields = ['veces_vista', 'fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'palabra_kichwa', 'traduccion_espanol', 'definicion', 'pronunciacion',
                'audio', 'imagen_vocabulario', 'descripcion_imagen', 'credito_imagen',
                'proveedor_imagen', 'autor_imagen', 'autor_imagen_url',
                'fuente_imagen_url', 'categoria',
            )
        }),
        ('Clasificación', {
            'fields': (
                'categoria_propuesta', 'estado_revision', 'clasificacion_confianza',
                'clasificacion_motivo', 'dificultad', 'nivel_dificultad', 'tipo',
            )
        }),
        ('Configuración de Juegos', {
            'fields': ('apta_para_juegos', 'dificultad_juego', 'descripcion_juego_espanol', 'descripcion_juego_kichwa', 'frecuencia_uso')
        }),
        ('Información Adicional', {
            'fields': ('etimologia', 'sinonimos', 'notas_gramaticales'),
            'classes': ('collapse',)
        }),
        ('Traducción al inglés', {
            'fields': ('traduccion_ingles', 'definicion_ingles', 'estado_revision_ingles'),
            'description': 'La traducción inglesa solo será pública cuando esté marcada como validada.',
        }),
        ('Control', {
            'fields': ('activa', 'veces_vista', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    actions = [
        'aceptar_categoria_propuesta', 'rechazar_categoria_propuesta', 'marcar_revisada',
        'marcar_validada', 'marcar_ingles_revisado', 'marcar_ingles_validado',
    ]

    @admin.action(description='Aceptar categoría propuesta y marcar como revisada')
    def aceptar_categoria_propuesta(self, request, queryset):
        actualizadas = queryset.filter(categoria_propuesta__isnull=False).update(
            categoria=F('categoria_propuesta'),
            categoria_propuesta=None,
            estado_revision='revisada',
        )
        self.message_user(request, f'{actualizadas} propuestas aceptadas.')

    @admin.action(description='Rechazar categoría propuesta')
    def rechazar_categoria_propuesta(self, request, queryset):
        actualizadas = queryset.filter(categoria_propuesta__isnull=False).update(categoria_propuesta=None)
        self.message_user(request, f'{actualizadas} propuestas rechazadas.')

    @admin.action(description='Marcar como revisada')
    def marcar_revisada(self, request, queryset):
        self.message_user(request, f'{queryset.update(estado_revision="revisada")} entradas revisadas.')

    @admin.action(description='Marcar como validada')
    def marcar_validada(self, request, queryset):
        self.message_user(request, f'{queryset.update(estado_revision="validada")} entradas validadas.')

    @admin.action(description='Marcar traducción inglesa como revisada')
    def marcar_ingles_revisado(self, request, queryset):
        validas = queryset.exclude(traduccion_ingles='')
        self.message_user(request, f'{validas.update(estado_revision_ingles="revisada")} traducciones inglesas revisadas.')

    @admin.action(description='Validar traducción inglesa para publicación')
    def marcar_ingles_validado(self, request, queryset):
        validas = queryset.exclude(traduccion_ingles='')
        self.message_user(request, f'{validas.update(estado_revision_ingles="validada")} traducciones inglesas publicadas.')


@admin.register(PreparacionImagenVocabulario)
class PreparacionImagenVocabularioAdmin(admin.ModelAdmin):
    list_display = [
        'palabra', 'tipo_visual', 'estado', 'lote', 'orden_lote',
        'tiene_archivo', 'revisada_por', 'fecha_revision',
    ]
    list_filter = ['estado', 'tipo_visual', 'lote', 'palabra__categoria']
    search_fields = [
        'palabra__palabra_kichwa', 'palabra__traduccion_espanol',
        'prompt', 'notas_revision',
    ]
    autocomplete_fields = ['palabra']
    list_select_related = ['palabra', 'palabra__categoria', 'revisada_por']
    readonly_fields = ['estado', 'revisada_por', 'fecha_revision', 'fecha_creacion', 'fecha_actualizacion']
    ordering = ['lote', 'orden_lote', 'palabra__palabra_kichwa']
    actions = ['marcar_generadas', 'aprobar_revisadas', 'publicar_aprobadas', 'descartar']

    @admin.display(boolean=True, description='Archivo localizado')
    def tiene_archivo(self, obj):
        return bool(obj.ruta_candidata and finders.find(obj.ruta_candidata))

    @admin.action(description='Marcar como generadas si el archivo existe')
    def marcar_generadas(self, request, queryset):
        correctas = []
        omitidas = 0
        for preparacion in queryset.filter(estado='preparada'):
            if preparacion.ruta_candidata and finders.find(preparacion.ruta_candidata):
                correctas.append(preparacion.pk)
            else:
                omitidas += 1
        actualizadas = PreparacionImagenVocabulario.objects.filter(pk__in=correctas).update(
            estado='generada', fecha_actualizacion=timezone.now(),
        )
        self.message_user(request, f'{actualizadas} marcadas como generadas; {omitidas} sin archivo local.')

    @admin.action(description='Aprobar imágenes generadas tras revisión')
    def aprobar_revisadas(self, request, queryset):
        correctas = []
        omitidas = 0
        for preparacion in queryset.filter(estado='generada'):
            if (
                preparacion.ruta_candidata
                and preparacion.descripcion_candidata.strip()
                and finders.find(preparacion.ruta_candidata)
            ):
                correctas.append(preparacion.pk)
            else:
                omitidas += 1
        actualizadas = PreparacionImagenVocabulario.objects.filter(pk__in=correctas).update(
            estado='revisada', revisada_por=request.user, fecha_revision=timezone.now(),
            fecha_actualizacion=timezone.now(),
        )
        self.message_user(request, f'{actualizadas} aprobadas; {omitidas} incompletas o sin archivo local.')

    @admin.action(description='Publicar imágenes revisadas')
    def publicar_aprobadas(self, request, queryset):
        publicadas = 0
        omitidas = 0
        with transaction.atomic():
            for preparacion in queryset.filter(estado='revisada').select_related('palabra'):
                if not (
                    preparacion.ruta_candidata
                    and preparacion.descripcion_candidata.strip()
                    and finders.find(preparacion.ruta_candidata)
                ):
                    omitidas += 1
                    continue
                Palabra.objects.filter(pk=preparacion.palabra_id).update(
                    imagen_vocabulario=preparacion.ruta_candidata,
                    descripcion_imagen=preparacion.descripcion_candidata,
                    credito_imagen=preparacion.credito_candidato,
                    proveedor_imagen=preparacion.proveedor_candidato,
                    autor_imagen=preparacion.autor_candidato,
                    autor_imagen_url=preparacion.autor_candidato_url,
                    fuente_imagen_url=preparacion.fuente_candidata_url,
                    fecha_actualizacion=timezone.now(),
                )
                preparacion.estado = 'publicada'
                preparacion.save(update_fields=['estado', 'fecha_actualizacion'])
                publicadas += 1
        self.message_user(request, f'{publicadas} publicadas; {omitidas} incompletas o sin archivo local.')

    @admin.action(description='Descartar propuestas seleccionadas')
    def descartar(self, request, queryset):
        descartadas = queryset.exclude(estado='publicada').update(
            estado='descartada', fecha_actualizacion=timezone.now(),
        )
        self.message_user(request, f'{descartadas} propuestas descartadas.')


@admin.register(CandidataImagenPexels)
class CandidataImagenPexelsAdmin(admin.ModelAdmin):
    list_display = [
        'preparacion', 'orden', 'pexels_id', 'fotografo', 'seleccionada', 'abrir_foto',
    ]
    list_filter = ['seleccionada', 'preparacion__lote', 'preparacion__palabra__categoria']
    search_fields = [
        'preparacion__palabra__palabra_kichwa',
        'preparacion__palabra__traduccion_espanol', 'fotografo', 'pexels_id',
    ]
    list_select_related = ['preparacion', 'preparacion__palabra']
    readonly_fields = [
        'preparacion', 'pexels_id', 'orden', 'url_foto', 'url_imagen', 'fotografo',
        'url_fotografo', 'descripcion_original', 'ancho', 'alto', 'color_promedio',
        'seleccionada', 'fecha_consulta',
    ]
    actions = ['seleccionar_para_descarga']

    @admin.display(description='Origen')
    def abrir_foto(self, obj):
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">Ver en Pexels</a>',
            obj.url_foto,
        )

    @admin.action(description='Seleccionar una candidata por acepción')
    def seleccionar_para_descarga(self, request, queryset):
        candidatas = list(queryset.select_related('preparacion'))
        repetidas = {
            candidata.preparacion_id
            for candidata in candidatas
            if sum(item.preparacion_id == candidata.preparacion_id for item in candidatas) > 1
        }
        seleccionadas = 0
        with transaction.atomic():
            for candidata in candidatas:
                if candidata.preparacion_id in repetidas:
                    continue
                CandidataImagenPexels.objects.filter(
                    preparacion_id=candidata.preparacion_id,
                ).update(seleccionada=False)
                CandidataImagenPexels.objects.filter(pk=candidata.pk).update(seleccionada=True)
                seleccionadas += 1
        self.message_user(
            request,
            f'{seleccionadas} candidatas seleccionadas; '
            f'{len(repetidas)} acepciones omitidas por selección múltiple.',
        )


@admin.register(EjemploUso)
class EjemploUsoAdmin(admin.ModelAdmin):
    list_display = ['palabra', 'oracion_corta', 'estado', 'tipo_revision', 'fuente', 'revisado_por', 'fecha_revision']
    list_filter = ['estado', 'tipo_revision', 'palabra__categoria', 'fecha_revision']
    search_fields = ['palabra__palabra_kichwa', 'palabra__traduccion_espanol', 'oracion_kichwa', 'fuente']
    autocomplete_fields = ['palabra']
    readonly_fields = [
        'estado', 'tipo_revision', 'nota_revision', 'revisado_por', 'fecha_revision',
        'fecha_creacion', 'fecha_actualizacion',
    ]
    fields = [
        'palabra', 'oracion_kichwa', 'traduccion_espanol', 'fuente',
        'estado', 'tipo_revision', 'nota_revision', 'revisado_por', 'fecha_revision',
        'fecha_creacion', 'fecha_actualizacion',
    ]
    actions = ['publicar_revisados', 'retirar_publicacion']

    @admin.display(description='Oración en Kichwa')
    def oracion_corta(self, obj):
        return obj.oracion_kichwa[:90]

    @admin.action(description='Publicar tras revisión editorial')
    def publicar_revisados(self, request, queryset):
        publicados = 0
        invalidos = 0
        for ejemplo in queryset.filter(estado='borrador').select_related('palabra'):
            ejemplo.estado = 'publicado'
            ejemplo.revisado_por = request.user
            ejemplo.fecha_revision = timezone.now()
            ejemplo.tipo_revision = 'humana'
            ejemplo.nota_revision = 'Aprobado desde Django Admin.'
            try:
                ejemplo.save(update_fields=[
                    'estado', 'tipo_revision', 'nota_revision', 'revisado_por',
                    'fecha_revision', 'fecha_actualizacion',
                ])
            except ValidationError:
                invalidos += 1
            else:
                publicados += 1
        self.message_user(request, f'{publicados} ejemplos publicados; {invalidos} incompletos o inválidos.')

    @admin.action(description='Retirar publicación y devolver a borrador')
    def retirar_publicacion(self, request, queryset):
        retirados = queryset.filter(estado='publicado').update(
            estado='borrador', tipo_revision='', nota_revision='', revisado_por=None, fecha_revision=None,
            fecha_actualizacion=timezone.now(),
        )
        self.message_user(request, f'{retirados} ejemplos retirados.')

@admin.register(PalabraFavorita)
class PalabraFavoritaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'palabra', 'fecha_agregada']
    list_filter = ['fecha_agregada']
    search_fields = ['usuario__username', 'palabra__palabra_kichwa', 'palabra__traduccion_espanol']
    ordering = ['-fecha_agregada']

@admin.register(HistorialBusqueda)
class HistorialBusquedaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'termino_buscado', 'resultados_encontrados', 'fecha_busqueda']
    list_filter = ['fecha_busqueda', 'resultados_encontrados']
    search_fields = ['termino_buscado', 'usuario__username']
    ordering = ['-fecha_busqueda']
    readonly_fields = ['fecha_busqueda']


@admin.register(ActividadUsuario)
class ActividadUsuarioAdmin(admin.ModelAdmin):
    """Consulta de actividad individual para personal con permiso de lectura."""

    list_display = ['usuario', 'tipo', 'detalle', 'fecha']
    list_filter = ['tipo', 'fecha']
    search_fields = ['usuario__username', 'busqueda__termino_buscado', 'palabra__palabra_kichwa']
    list_select_related = ['usuario', 'busqueda', 'palabra', 'estadistica']
    readonly_fields = ['usuario', 'tipo', 'palabra', 'busqueda', 'estadistica', 'fecha']
    ordering = ['-fecha', '-id']

    @admin.display(description='Detalle')
    def detalle(self, obj):
        if obj.tipo == 'busqueda' and obj.busqueda:
            return obj.busqueda.termino_buscado
        if obj.tipo == 'palabra' and obj.palabra:
            return obj.palabra.palabra_kichwa
        if obj.tipo == 'juego' and obj.estadistica:
            return obj.estadistica.get_tipo_juego_display()
        return 'Registro ya no disponible'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EstadisticaJuego)
class EstadisticaJuegoAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 'tipo_juego', 'puntuacion', 
        'respuestas_correctas', 'respuestas_totales', 'dificultad', 'fecha_juego'
    ]
    list_filter = ['tipo_juego', 'dificultad', 'fecha_juego']
    search_fields = ['usuario__username']
    ordering = ['-fecha_juego']
    readonly_fields = ['fecha_juego', 'porcentaje_aciertos']
    
    def porcentaje_aciertos(self, obj):
        return f"{obj.porcentaje_aciertos}%"
    porcentaje_aciertos.short_description = 'Porcentaje de Aciertos'


@admin.register(ProgresoPalabraJuego)
class ProgresoPalabraJuegoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'palabra', 'dominio', 'intentos', 'respuestas_correctas', 'mejor_racha', 'ultima_practica']
    list_filter = ['dominio', 'ultima_practica']
    search_fields = ['usuario__username', 'palabra__palabra_kichwa', 'palabra__traduccion_espanol']
    readonly_fields = ['ultima_practica']


@admin.register(SesionJuego)
class SesionJuegoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'tipo_juego', 'dificultad', 'categoria', 'iniciada_en', 'finalizada_en']
    list_filter = ['tipo_juego', 'dificultad', 'iniciada_en', 'finalizada_en']
    readonly_fields = ['id', 'palabras_ids', 'iniciada_en', 'finalizada_en', 'estadistica']


@admin.register(IntentoPalabraJuego)
class IntentoPalabraJuegoAdmin(admin.ModelAdmin):
    list_display = ['sesion', 'palabra', 'correcta', 'fecha']
    list_filter = ['correcta', 'fecha', 'sesion__tipo_juego']
    search_fields = ['palabra__palabra_kichwa', 'palabra__traduccion_espanol', 'sesion__usuario__username']
    readonly_fields = ['sesion', 'palabra', 'correcta', 'fecha']
