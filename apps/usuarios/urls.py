from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Autenticación
    path('registro/', views.registro, name='registro'),
    path('login/', views.LoginSeguroView.as_view(), name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    
    # Perfil
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/<str:username>/', views.perfil, name='perfil_usuario'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('eliminar-cuenta/', views.eliminar_cuenta, name='eliminar_cuenta'),
    
    # Páginas legales
    path('terminos/', views.terminos, name='terminos'),
    path('privacidad/', views.privacidad, name='privacidad'),
    
    # Recuperación de contraseña
    path('password-reset/',
         views.RecuperacionContrasenaView.as_view(),
         name='password_reset'),
    path('password-reset/done/',
         views.RecuperacionEnviadaView.as_view(),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         views.ConfirmarRecuperacionView.as_view(),
         name='password_reset_confirm'),
    path('reset/done/',
         views.RecuperacionCompletaView.as_view(),
         name='password_reset_complete'),
]
