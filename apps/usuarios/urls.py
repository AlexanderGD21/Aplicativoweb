from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Autenticación
    path('registro/', views.registro, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    
    # Perfil
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/<str:username>/', views.perfil, name='perfil_usuario'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('eliminar-cuenta/', views.eliminar_cuenta, name='eliminar_cuenta'),
    
    # AJAX
    path('actualizar-puntos/', views.actualizar_puntos, name='actualizar_puntos'),
    path('incrementar-palabras/', views.incrementar_palabras_aprendidas, name='incrementar_palabras'),
    
    # Páginas legales
    path('terminos/', views.terminos, name='terminos'),
    path('privacidad/', views.privacidad, name='privacidad'),
    
    # Recuperación de contraseña
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='usuarios/password_reset.html',
             email_template_name='usuarios/password_reset_email.txt',
             subject_template_name='usuarios/password_reset_subject.txt',
             success_url=reverse_lazy('usuarios:password_reset_done'),
         ),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='usuarios/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='usuarios/password_reset_confirm.html',
             success_url=reverse_lazy('usuarios:password_reset_complete'),
         ),
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='usuarios/password_reset_complete.html'),
         name='password_reset_complete'),
]
