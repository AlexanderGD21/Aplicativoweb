from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario

class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = (
        ('avatar', 'biografia'),
        ('fecha_nacimiento', 'genero'),
        ('ciudad', 'pais', 'telefono'),
        ('nivel_kichwa', 'palabras_aprendidas', 'puntos_totales'),
        ('notificaciones_email', 'perfil_publico'),
        ('fecha_creacion', 'ultima_actividad')
    )
    readonly_fields = ('fecha_creacion', 'ultima_actividad')

class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'nivel_kichwa', 'palabras_aprendidas', 'puntos_totales', 'ciudad', 'pais', 'fecha_creacion']
    list_filter = ['nivel_kichwa', 'genero', 'pais', 'perfil_publico', 'fecha_creacion']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name', 'ciudad', 'pais']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'ultima_actividad']
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Información Personal', {
            'fields': ('avatar', 'biografia', 'fecha_nacimiento', 'genero')
        }),
        ('Ubicación', {
            'fields': ('ciudad', 'pais', 'telefono')
        }),
        ('Aprendizaje', {
            'fields': ('nivel_kichwa', 'palabras_aprendidas', 'puntos_totales', 'racha_dias')
        }),
        ('Configuración', {
            'fields': ('notificaciones_email', 'perfil_publico')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'ultima_actividad'),
            'classes': ('collapse',)
        })
    )
    ordering = ['-fecha_creacion']
