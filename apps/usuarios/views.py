from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import RegistroForm, PerfilUsuarioForm, UserForm
from .models import PerfilUsuario

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
            except IntegrityError:
                form.add_error('email', 'Ya existe una cuenta registrada con este correo.')
                return render(request, 'usuarios/registro.html', {'form': form})
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada para {username}! Ya puedes iniciar sesión.')
            return redirect('usuarios:login')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})


@login_required
@require_POST
def cerrar_sesion(request):
    """Cierra sesión únicamente mediante POST protegido por CSRF."""
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('diccionario:home')

@login_required
def perfil(request, username=None):
    if username:
        usuario = get_object_or_404(User, username=username)
        perfil_usuario = get_object_or_404(PerfilUsuario, usuario=usuario)
        es_propio = request.user == usuario
    else:
        usuario = request.user
        perfil_usuario = get_object_or_404(PerfilUsuario, usuario=usuario)
        es_propio = True
    
    # Verificar si el perfil es público o es el propio usuario
    if not es_propio and not perfil_usuario.perfil_publico:
        messages.error(request, 'Este perfil es privado.')
        return redirect('diccionario:home')
    
    context = {
        'usuario': usuario,
        'perfil': perfil_usuario,
        'es_propio': es_propio,
    }
    return render(request, 'usuarios/perfil.html', context)

@login_required
def editar_perfil(request):
    perfil_usuario = get_object_or_404(PerfilUsuario, usuario=request.user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        perfil_form = PerfilUsuarioForm(request.POST, request.FILES, instance=perfil_usuario)
        
        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, '¡Tu perfil ha sido actualizado exitosamente!')
            return redirect('usuarios:perfil')
    else:
        user_form = UserForm(instance=request.user)
        perfil_form = PerfilUsuarioForm(instance=perfil_usuario)
    
    context = {
        'user_form': user_form,
        'perfil_form': perfil_form,
    }
    return render(request, 'usuarios/editar_perfil.html', context)

@login_required
def eliminar_cuenta(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = authenticate(username=request.user.username, password=password)
        
        if user:
            user.delete()
            messages.success(request, 'Tu cuenta ha sido eliminada exitosamente.')
            return redirect('diccionario:home')
        else:
            messages.error(request, 'Contraseña incorrecta.')
    
    return render(request, 'usuarios/eliminar_cuenta.html')

def terminos(request):
    return render(request, 'usuarios/terminos.html')

def privacidad(request):
    return render(request, 'usuarios/privacidad.html')

@login_required
@require_POST
def actualizar_puntos(request):
    """Vista AJAX para actualizar puntos del usuario"""
    try:
        puntos = int(request.POST.get('puntos', 0))
        perfil = request.user.perfil
        perfil.incrementar_puntos(puntos)
        
        return JsonResponse({
            'success': True,
            'puntos_totales': perfil.puntos_totales
        })
    except (TypeError, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'Los puntos deben ser un entero entre 0 y 10000.'
        }, status=400)

@login_required
@require_POST
def incrementar_palabras_aprendidas(request):
    """Vista AJAX para incrementar palabras aprendidas"""
    try:
        perfil = request.user.perfil
        perfil.incrementar_palabras_aprendidas()
        
        return JsonResponse({
            'success': True,
            'palabras_aprendidas': perfil.palabras_aprendidas
        })
    except Exception:
        return JsonResponse({
            'success': False,
            'error': 'No se pudo actualizar el progreso.'
        }, status=500)
