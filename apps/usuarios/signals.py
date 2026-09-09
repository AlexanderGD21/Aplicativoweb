from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Signal para crear automáticamente un perfil cuando se crea un usuario
    """
    # loaddata carga perfiles explícitos; crear uno aquí duplicaría usuario_id.
    if kwargs.get('raw'):
        return

    if created:
        try:
            # Usar get_or_create para evitar duplicados
            perfil, perfil_created = PerfilUsuario.objects.get_or_create(
                usuario=instance,
                defaults={
                    'nivel_kichwa': 'principiante',
                    'puntos_totales': 0,
                    'biografia': '',
                    'ciudad': '',
                    'pais': ''
                }
            )
            
            if perfil_created:
                logger.info(f'Perfil creado para usuario: {instance.username}')
            else:
                logger.warning(f'Perfil ya existía para usuario: {instance.username}')
                
        except Exception as e:
            logger.error(f'Error creando perfil para {instance.username}: {e}')

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """
    Signal para guardar el perfil cuando se actualiza el usuario
    """
    # Las fixtures se restauran tal como fueron serializadas.
    if kwargs.get('raw'):
        return

    try:
        # El related_name declarado por PerfilUsuario es "perfil".
        if hasattr(instance, 'perfil'):
            instance.perfil.save()
        else:
            # Si no existe, crearlo
            PerfilUsuario.objects.get_or_create(
                usuario=instance,
                defaults={
                    'nivel_kichwa': 'principiante',
                    'puntos_totales': 0,
                    'biografia': '',
                    'ciudad': '',
                    'pais': ''
                }
            )
    except Exception as e:
        logger.error(f'Error guardando perfil para {instance.username}: {e}')
