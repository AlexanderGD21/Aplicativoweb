from django.urls import path
from . import views

app_name = 'diccionario'

urlpatterns = [
    # Páginas principales
    path('', views.home, name='home'),
    path('buscar/', views.buscar, name='buscar'),
    path('palabra/<int:pk>/', views.detalle_palabra, name='detalle_palabra'),
    path('categorias/', views.categorias, name='categorias'),
    path('categoria/<int:categoria_id>/', views.palabras_por_categoria, name='palabras_por_categoria'),
    
    # Páginas informativas
    path('acerca-de/', views.acerca_de, name='acerca_de'),
    path('contacto/', views.contacto, name='contacto'),
    
    # Juegos
    path('juegos/', views.juegos, name='juegos'),
    path('juegos/traduccion/', views.juego_traduccion, name='juego_traduccion'),
    path('juegos/completar/', views.juego_completar, name='juego_completar'),
    path('juegos/memoria/', views.juego_memoria, name='juego_memoria'),
    path('juegos/conexion/', views.juego_conectar, name='juego_conexion'),
    path('juegos/sopa-letras/', views.juego_sopa_letras, name='juego_sopa_letras'),
    
    # APIs para juegos
    path('juegos/guardar-estadistica/', views.guardar_estadistica_juego, name='guardar_estadistica_juego'),
    path('juegos/guardar-resultado/', views.guardar_estadistica_juego, name='guardar_resultado_juego'),
    path('juegos/registrar-respuesta/', views.registrar_respuesta_juego, name='registrar_respuesta_juego'),
    path('juegos/obtener-palabras/', views.obtener_palabras_juego, name='obtener_palabras_juego'),
    
    # APIs para búsqueda
    path('api/buscar/', views.buscar_palabras_ajax, name='buscar_palabras_ajax'),
    path('api/sugerencias/', views.obtener_sugerencias_ajax, name='obtener_sugerencias_ajax'),
    path('api/v1/palabras/', views.api_palabras, name='api_palabras'),
    path('api/v1/palabras/<int:pk>/', views.api_detalle_palabra, name='api_detalle_palabra'),
    
    # Favoritas (requieren autenticación)
    path('favoritas/', views.mis_favoritas, name='mis_favoritas'),
    path('favoritas/agregar/<int:palabra_id>/', views.agregar_favorita, name='agregar_favorita'),
    path('favoritas/quitar/<int:palabra_id>/', views.quitar_favorita, name='quitar_favorita'),
    path('favoritas/toggle/<int:palabra_id>/', views.toggle_favorita_ajax, name='toggle_favorita_ajax'),
]
