import hashlib
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LoginForm, RegistroForm, PerfilUsuarioForm, UserForm
from .models import PerfilUsuario


def _origen_cliente(request):
    """Confía en X-Forwarded-For solo si el despliegue declaró sus proxies."""
    proxies = settings.AUTH_TRUSTED_PROXY_COUNT
    reenviadas = [
        valor.strip()
        for valor in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')
        if valor.strip()
    ]
    if proxies > 0 and len(reenviadas) >= proxies:
        return reenviadas[-proxies]
    return request.META.get('REMOTE_ADDR', 'desconocido')


def _destino_seguro(request):
    destino = request.POST.get('next') or request.GET.get('next') or ''
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destino
    return ''


def _clave_limite(prefijo, request, identificador=''):
    origen = _origen_cliente(request)
    material = f'{origen}|{identificador.strip().casefold()}'.encode('utf-8')
    return f'usuarios:{prefijo}:{hashlib.sha256(material).hexdigest()}'


def _incrementar_limite(clave, segundos):
    if not cache.add(clave, 1, timeout=segundos):
        try:
            cache.incr(clave)
        except ValueError:
            cache.set(clave, 1, timeout=segundos)


class LoginSeguroView(LoginView):
    template_name = 'usuarios/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        self._limite_claves = [
            _clave_limite('login-origen', request),
            _clave_limite('login-cuenta', request, request.POST.get('username', '')),
        ]
        self._limite_excedido = any(
            cache.get(clave, 0) >= settings.LOGIN_MAX_ATTEMPTS
            for clave in self._limite_claves
        )
        if self._limite_excedido:
            form = self.get_form()
            form.add_error(
                None,
                'Demasiados intentos. Espera unos minutos antes de volver a intentarlo.',
            )
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        if not getattr(self, '_limite_excedido', False):
            for clave in self._limite_claves:
                _incrementar_limite(clave, settings.LOGIN_LOCKOUT_SECONDS)
        response = super().form_invalid(form)
        if getattr(self, '_limite_excedido', False):
            response.status_code = 429
        return response

    def form_valid(self, form):
        cache.delete_many(self._limite_claves)
        return super().form_valid(form)


class RecuperacionContrasenaView(PasswordResetView):
    template_name = 'usuarios/password_reset.html'
    email_template_name = 'usuarios/password_reset_email.txt'
    subject_template_name = 'usuarios/password_reset_subject.txt'
    success_url = reverse_lazy('usuarios:password_reset_done')

    def dispatch(self, request, *args, **kwargs):
        destino = _destino_seguro(request)
        if destino:
            request.session['usuarios_auth_next'] = destino
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.session.get('usuarios_auth_next', '')
        return context

    def post(self, request, *args, **kwargs):
        claves = [
            _clave_limite('password-reset-origen', request),
            _clave_limite('password-reset-cuenta', request, request.POST.get('email', '')),
        ]
        if any(cache.get(clave, 0) >= settings.PASSWORD_RESET_MAX_REQUESTS for clave in claves):
            return redirect(self.success_url)
        for clave in claves:
            _incrementar_limite(clave, settings.PASSWORD_RESET_RATE_SECONDS)
        return super().post(request, *args, **kwargs)


class DestinoAutenticacionMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.session.get('usuarios_auth_next', '')
        return context


class RecuperacionEnviadaView(DestinoAutenticacionMixin, PasswordResetDoneView):
    template_name = 'usuarios/password_reset_done.html'


class ConfirmarRecuperacionView(DestinoAutenticacionMixin, PasswordResetConfirmView):
    template_name = 'usuarios/password_reset_confirm.html'
    success_url = reverse_lazy('usuarios:password_reset_complete')


class RecuperacionCompletaView(DestinoAutenticacionMixin, PasswordResetCompleteView):
    template_name = 'usuarios/password_reset_complete.html'


def registro(request):
    if request.user.is_authenticated:
        return redirect('diccionario:home')
    if request.method == 'POST':
        limite_clave = _clave_limite('registro', request)
        if cache.get(limite_clave, 0) >= settings.REGISTRATION_MAX_REQUESTS:
            form = RegistroForm(request.POST)
            form.add_error(None, 'Demasiados intentos de registro. Espera unos minutos antes de continuar.')
            return render(request, 'usuarios/registro.html', {
                'form': form,
                'next': _destino_seguro(request),
            }, status=429)
        _incrementar_limite(limite_clave, settings.REGISTRATION_RATE_SECONDS)
        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
                    perfil.terminos_aceptados_en = timezone.now()
                    perfil.version_terminos = settings.LEGAL_TERMS_VERSION
                    perfil.version_privacidad = settings.LEGAL_PRIVACY_VERSION
                    perfil.notificaciones_email = form.cleaned_data['recibir_novedades']
                    perfil.save(update_fields=[
                        'terminos_aceptados_en',
                        'version_terminos',
                        'version_privacidad',
                        'notificaciones_email',
                        'fecha_actualizacion',
                        'ultima_actividad',
                    ])
            except IntegrityError:
                form.add_error(None, 'No pudimos crear la cuenta con esos datos. Revisa el usuario y el correo.')
                return render(request, 'usuarios/registro.html', {
                    'form': form,
                    'next': _destino_seguro(request),
                })
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada para {username}! Ya puedes iniciar sesión.')
            destino = _destino_seguro(request)
            if destino:
                return redirect(f"{reverse('usuarios:login')}?{urlencode({'next': destino})}")
            return redirect('usuarios:login')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {
        'form': form,
        'next': _destino_seguro(request),
    })


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
            avatar_anterior = perfil_usuario.avatar.name if perfil_usuario.avatar else ''
            user_form.save()
            perfil_actualizado = perfil_form.save()
            avatar_nuevo = perfil_actualizado.avatar.name if perfil_actualizado.avatar else ''
            if avatar_anterior and avatar_anterior != avatar_nuevo:
                perfil_usuario.avatar.storage.delete(avatar_anterior)
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
            avatar_nombre = user.perfil.avatar.name if user.perfil.avatar else ''
            avatar_storage = user.perfil.avatar.storage if user.perfil.avatar else None
            user.delete()
            if avatar_nombre and avatar_storage:
                avatar_storage.delete(avatar_nombre)
            messages.success(request, 'Tu cuenta ha sido eliminada exitosamente.')
            return redirect('diccionario:home')
        else:
            messages.error(request, 'Contraseña incorrecta.')
    
    return render(request, 'usuarios/eliminar_cuenta.html')

def terminos(request):
    return render(request, 'usuarios/terminos.html', {'version_legal': settings.LEGAL_TERMS_VERSION})

def privacidad(request):
    return render(request, 'usuarios/privacidad.html', {'version_legal': settings.LEGAL_PRIVACY_VERSION})
