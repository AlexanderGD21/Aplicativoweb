import re
import unicodedata
import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


def normalizar_texto_busqueda(texto):
    """Crea una versión comparable sin tildes editoriales ni mayúsculas."""
    texto = unicodedata.normalize('NFKD', (texto or '').casefold())
    texto = ''.join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != 'Mn'
    )
    return re.sub(r'[^a-z0-9ñ]+', ' ', texto).strip()


def validar_tamano_audio(archivo):
    if archivo.size > 10 * 1024 * 1024:
        raise ValidationError('El audio no puede superar 10 MB.')

class Categoria(models.Model):
    GRUPO_CHOICES = [
        ('entorno', 'Entorno natural'),
        ('personas', 'Personas y comunidad'),
        ('cotidiano', 'Vida cotidiana'),
        ('lengua', 'Lengua, tiempo y pensamiento'),
        ('acciones', 'Acciones y cualidades'),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    slug = models.SlugField(blank=True, unique=True)
    color = models.CharField(max_length=7, default='#007bff', help_text='Color en formato hexadecimal')
    grupo = models.CharField(max_length=20, choices=GRUPO_CHOICES, default='lengua')
    orden = models.PositiveSmallIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['grupo', 'orden', 'nombre']
    
    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nombre)[:45] or 'categoria'
            candidato = base
            contador = 2
            while Categoria.objects.exclude(pk=self.pk).filter(slug=candidato).exists():
                sufijo = f'-{contador}'
                candidato = f'{base[:50 - len(sufijo)]}{sufijo}'
                contador += 1
            self.slug = candidato
        super().save(*args, **kwargs)

class Palabra(models.Model):
    DIFICULTAD_CHOICES = [
        ('facil', 'Fácil'),
        ('medio', 'Medio'),
        ('dificil', 'Difícil'),
    ]
    
    NIVEL_CHOICES = [
        ('basico', 'Básico'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]
    
    TIPO_CHOICES = [
        ('kichwa_espanol', 'Kichwa-Español'),
        ('espanol_kichwa', 'Español-Kichwa'),
    ]

    ESTADO_REVISION_CHOICES = [
        ('pendiente', 'Pendiente de revisión'),
        ('revisada', 'Revisada'),
        ('validada', 'Validada'),
    ]

    CONFIANZA_CLASIFICACION_CHOICES = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja; requiere revisión'),
        ('manual', 'Clasificación manual'),
    ]
    
    # Campos básicos
    palabra_kichwa = models.CharField(max_length=300, db_index=True)
    traduccion_espanol = models.CharField(max_length=200, db_index=True)
    definicion = models.TextField(blank=True, null=True)
    pronunciacion = models.CharField(max_length=400, blank=True, null=True)
    busqueda_kichwa = models.CharField(max_length=300, blank=True, editable=False, db_index=True)
    busqueda_espanol = models.CharField(max_length=200, blank=True, editable=False, db_index=True)
    busqueda_contenido = models.TextField(blank=True, editable=False)
    audio = models.FileField(
        upload_to='audios/',
        blank=True,
        null=True,
        help_text='Archivo de pronunciación (MP3, OGG o WAV; máximo 10 MB).',
        validators=[FileExtensionValidator(['mp3', 'ogg', 'wav']), validar_tamano_audio],
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='palabras',
        help_text='No se puede eliminar una categoría mientras tenga palabras asociadas.',
    )
    categoria_propuesta = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        related_name='propuestas',
        blank=True,
        null=True,
        help_text='Sugerencia automática pendiente de validación humana.',
    )
    
    # Campos de clasificación
    dificultad = models.CharField(max_length=10, choices=DIFICULTAD_CHOICES, default='medio')
    nivel_dificultad = models.CharField(max_length=15, choices=NIVEL_CHOICES, default='basico')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='kichwa_espanol')
    estado_revision = models.CharField(
        max_length=10,
        choices=ESTADO_REVISION_CHOICES,
        default='pendiente',
        db_index=True,
        help_text='Control interno de la curación lingüística de la entrada.',
    )
    clasificacion_confianza = models.CharField(
        max_length=10,
        choices=CONFIANZA_CLASIFICACION_CHOICES,
        default='baja',
        db_index=True,
    )
    clasificacion_motivo = models.CharField(max_length=255, blank=True)
    
    # Campos para juegos
    apta_para_juegos = models.BooleanField(default=False)
    dificultad_juego = models.CharField(max_length=10, choices=DIFICULTAD_CHOICES, default='medio')
    descripcion_juego_espanol = models.TextField(blank=True, null=True)
    descripcion_juego_kichwa = models.TextField(blank=True, null=True)
    frecuencia_uso = models.IntegerField(default=1)
    
    # Campos adicionales
    etimologia = models.TextField(blank=True, null=True)
    sinonimos = models.TextField(blank=True, null=True, help_text='Separar con comas')
    notas_gramaticales = models.TextField(blank=True, null=True)
    ejemplo_uso = models.TextField(blank=True, null=True)
    
    # Campos de control
    activa = models.BooleanField(default=True)
    veces_vista = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Palabra'
        verbose_name_plural = 'Palabras'
        ordering = ['palabra_kichwa']
        unique_together = ['palabra_kichwa', 'traduccion_espanol']
        indexes = [
            models.Index(fields=['activa', 'palabra_kichwa'], name='palabra_busq_kichwa_idx'),
            models.Index(fields=['activa', 'traduccion_espanol'], name='palabra_busq_espanol_idx'),
            models.Index(fields=['activa', 'categoria', 'dificultad'], name='palabra_filtros_idx'),
            models.Index(fields=['activa', 'apta_para_juegos', 'dificultad_juego'], name='palabra_juegos_idx'),
        ]
    
    def __str__(self):
        return f"{self.palabra_kichwa} - {self.traduccion_espanol}"

    def save(self, *args, **kwargs):
        self.busqueda_kichwa = normalizar_texto_busqueda(self.palabra_kichwa)
        self.busqueda_espanol = normalizar_texto_busqueda(self.traduccion_espanol)
        self.busqueda_contenido = normalizar_texto_busqueda(' '.join(filter(None, (
            self.definicion,
            self.pronunciacion,
            self.sinonimos,
            self.notas_gramaticales,
        ))))
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {
                'busqueda_kichwa', 'busqueda_espanol', 'busqueda_contenido',
            }
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('diccionario:detalle_palabra', kwargs={'pk': self.pk})

class PalabraFavorita(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    palabra = models.ForeignKey(Palabra, on_delete=models.CASCADE)
    fecha_agregada = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Palabra Favorita'
        verbose_name_plural = 'Palabras Favoritas'
        unique_together = ['usuario', 'palabra']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.palabra.palabra_kichwa}"


class RelacionPalabra(models.Model):
    """Vínculo léxico curado; no depende solo de compartir categoría."""
    TIPO_CHOICES = [
        ('familia', 'Misma familia semántica'),
        ('sinonimo', 'Sinónimo o equivalente'),
        ('contraste', 'Contraste o antónimo'),
        ('contexto', 'Relacionado por contexto'),
    ]
    origen = models.ForeignKey(Palabra, on_delete=models.CASCADE, related_name='relaciones_origen')
    destino = models.ForeignKey(Palabra, on_delete=models.CASCADE, related_name='relaciones_destino')
    tipo = models.CharField(max_length=12, choices=TIPO_CHOICES, default='contexto')
    nota = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name = 'Relación entre palabras'
        verbose_name_plural = 'Relaciones entre palabras'
        constraints = [
            models.UniqueConstraint(fields=['origen', 'destino', 'tipo'], name='relacion_palabra_unica'),
            models.CheckConstraint(check=~models.Q(origen=models.F('destino')), name='relacion_palabra_distinta'),
        ]

class HistorialBusqueda(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    termino_buscado = models.CharField(max_length=200)
    resultados_encontrados = models.IntegerField(default=0)
    fecha_busqueda = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Historial de Búsqueda'
        verbose_name_plural = 'Historial de Búsquedas'
        ordering = ['-fecha_busqueda']
    
    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else 'Anónimo'
        return f"{usuario_str} buscó: {self.termino_buscado}"


class BusquedaPopularDiaria(models.Model):
    """Conteo agregado de búsquedas exactas; no almacena la identidad de quien consulta."""

    palabra = models.ForeignKey(Palabra, on_delete=models.CASCADE, related_name='busquedas_populares')
    fecha = models.DateField(default=timezone.localdate, db_index=True)
    consultas = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Búsqueda popular diaria'
        verbose_name_plural = 'Búsquedas populares diarias'
        constraints = [
            models.UniqueConstraint(fields=['palabra', 'fecha'], name='busqueda_popular_palabra_fecha'),
        ]

class EstadisticaJuego(models.Model):
    TIPO_JUEGO_CHOICES = [
        ('traduccion', 'Traducción'),
        ('completar', 'Completar Palabras'),
        ('memoria', 'Juego de Memoria'),
        ('conectar', 'Conectar Traducciones'),
        ('sopa_letras', 'Sopa de Letras'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_juego = models.CharField(max_length=20, choices=TIPO_JUEGO_CHOICES)
    puntuacion = models.IntegerField(default=0)
    respuestas_correctas = models.IntegerField(default=0)
    respuestas_totales = models.IntegerField(default=0)
    dificultad = models.CharField(max_length=10, choices=Palabra.DIFICULTAD_CHOICES, default='medio')
    tiempo_jugado = models.IntegerField(default=0, help_text='Tiempo en segundos')
    fecha_juego = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Estadística de Juego'
        verbose_name_plural = 'Estadísticas de Juegos'
        ordering = ['-fecha_juego']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_juego_display()} - {self.puntuacion} pts"
    
    @property
    def porcentaje_aciertos(self):
        if self.respuestas_totales > 0:
            return round((self.respuestas_correctas / self.respuestas_totales) * 100, 2)
        return 0


class SesionJuego(models.Model):
    """Conjunto cerrado de palabras que el servidor autoriza para una partida."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sesiones_juego')
    clave_anonima = models.CharField(max_length=40, blank=True)
    tipo_juego = models.CharField(max_length=20, choices=EstadisticaJuego.TIPO_JUEGO_CHOICES)
    dificultad = models.CharField(max_length=10, choices=Palabra.DIFICULTAD_CHOICES)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    palabras_ids = models.JSONField(default=list)
    pistas_usadas = models.PositiveSmallIntegerField(default=0)
    pistas_palabras_ids = models.JSONField(default=list)
    iniciada_en = models.DateTimeField(auto_now_add=True)
    finalizada_en = models.DateTimeField(null=True, blank=True)
    estadistica = models.OneToOneField(
        EstadisticaJuego, on_delete=models.SET_NULL, null=True, blank=True, related_name='sesion_validada',
    )

    class Meta:
        verbose_name = 'Sesión de juego'
        verbose_name_plural = 'Sesiones de juego'
        ordering = ['-iniciada_en']


class IntentoPalabraJuego(models.Model):
    sesion = models.ForeignKey(SesionJuego, on_delete=models.CASCADE, related_name='intentos')
    palabra = models.ForeignKey(Palabra, on_delete=models.CASCADE, related_name='intentos_juego')
    correcta = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Intento de palabra'
        verbose_name_plural = 'Intentos de palabras'
        ordering = ['fecha']
        indexes = [
            models.Index(fields=['sesion', 'palabra', 'correcta'], name='intento_sesion_palabra_idx'),
        ]


class ProgresoPalabraJuego(models.Model):
    """Memoria de aprendizaje por usuario y palabra, compartida por los juegos."""

    DOMINIO_CHOICES = [
        ('nueva', 'Nueva'),
        ('aprendiendo', 'Aprendiendo'),
        ('practicando', 'En práctica'),
        ('dominada', 'Dominada'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progreso_juegos')
    palabra = models.ForeignKey(Palabra, on_delete=models.CASCADE, related_name='progreso_juegos')
    intentos = models.PositiveIntegerField(default=0)
    respuestas_correctas = models.PositiveIntegerField(default=0)
    racha_actual = models.PositiveIntegerField(default=0)
    mejor_racha = models.PositiveIntegerField(default=0)
    dominio = models.CharField(max_length=12, choices=DOMINIO_CHOICES, default='nueva', db_index=True)
    ultima_practica = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Progreso de palabra en juegos'
        verbose_name_plural = 'Progreso de palabras en juegos'
        ordering = ['dominio', 'ultima_practica']
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'palabra'], name='progreso_juego_usuario_palabra'),
        ]
        indexes = [
            models.Index(fields=['usuario', 'dominio', 'ultima_practica'], name='progreso_juego_prioridad_idx'),
        ]

    @property
    def porcentaje_aciertos(self):
        if not self.intentos:
            return 0
        return round((self.respuestas_correctas / self.intentos) * 100)

    def registrar_respuesta(self, correcta):
        self.intentos += 1
        if correcta:
            self.respuestas_correctas += 1
            self.racha_actual += 1
            self.mejor_racha = max(self.mejor_racha, self.racha_actual)
        else:
            self.racha_actual = 0

        precision = self.respuestas_correctas / self.intentos
        if self.intentos >= 6 and precision >= 0.85 and self.racha_actual >= 3:
            self.dominio = 'dominada'
        elif self.intentos >= 3 and precision >= 0.6:
            self.dominio = 'practicando'
        else:
            self.dominio = 'aprendiendo'

        self.save(update_fields=[
            'intentos', 'respuestas_correctas', 'racha_actual', 'mejor_racha',
            'dominio', 'ultima_practica',
        ])

    def __str__(self):
        return f'{self.usuario.username}: {self.palabra.palabra_kichwa} ({self.dominio})'
