from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    NIVEL_KICHWA_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
        ('nativo', 'Nativo'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    biografia = models.TextField(max_length=500, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    pais = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    nivel_kichwa = models.CharField(max_length=20, choices=NIVEL_KICHWA_CHOICES, default='principiante')
    palabras_aprendidas = models.PositiveIntegerField(default=0)
    puntos_totales = models.PositiveIntegerField(default=0)
    racha_dias = models.PositiveIntegerField(default=0)
    notificaciones_email = models.BooleanField(default=False)
    perfil_publico = models.BooleanField(default=False)
    terminos_aceptados_en = models.DateTimeField(null=True, blank=True)
    version_terminos = models.CharField(max_length=20, blank=True)
    version_privacidad = models.CharField(max_length=20, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    ultima_actividad = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    @property
    def nombre_completo(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}".strip()

    @property
    def edad(self):
        if self.fecha_nacimiento:
            from datetime import date
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None

    def incrementar_puntos(self, puntos):
        if isinstance(puntos, bool) or not isinstance(puntos, int) or not 0 <= puntos <= 10_000:
            raise ValueError('Los puntos deben ser un entero entre 0 y 10000.')
        self.puntos_totales += puntos
        self.save(update_fields=['puntos_totales', 'fecha_actualizacion', 'ultima_actividad'])

    def incrementar_palabras_aprendidas(self):
        self.palabras_aprendidas += 1
        self.save(update_fields=['palabras_aprendidas', 'fecha_actualizacion', 'ultima_actividad'])
