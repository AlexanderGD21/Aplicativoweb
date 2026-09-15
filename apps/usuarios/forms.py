import unicodedata
import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import PerfilUsuario


def _limpiar_nombre_persona(valor, etiqueta):
    valor = ' '.join(unicodedata.normalize('NFC', valor).split())
    if not valor:
        raise forms.ValidationError(f'Ingresa tu {etiqueta.lower()}.')
    if not all(caracter.isalpha() or caracter == ' ' for caracter in valor):
        raise forms.ValidationError(
            f'El {etiqueta.lower()} solo puede contener letras y espacios.'
        )
    return valor


class LoginForm(AuthenticationForm):
    """Autenticación con nombre de usuario o correo sin revelar cuentas existentes."""

    username = forms.CharField(
        label=_('Usuario o correo electrónico'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'username',
            'autocapitalize': 'none',
            'spellcheck': 'false',
            'placeholder': _('Tu usuario o correo'),
            'data-tooltip': _('Puedes usar tu nombre de usuario o el correo asociado'),
        }),
    )
    password = forms.CharField(
        label=_('Contraseña'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password',
            'placeholder': _('Tu contraseña'),
            'data-tooltip': _('La contraseña distingue mayúsculas y minúsculas'),
        }),
    )
    error_messages = {
        'invalid_login': _('No pudimos iniciar sesión con esos datos. Revisa el usuario o correo y la contraseña.'),
        'inactive': _('Esta cuenta no está disponible.'),
    }

    def clean(self):
        identificador = self.cleaned_data.get('username', '').strip()
        if '@' in identificador:
            usuario = User.objects.filter(email__iexact=identificador).only('username').first()
            if usuario:
                self.cleaned_data['username'] = usuario.get_username()
        return super().clean()


class RegistroForm(UserCreationForm):
    acepto_terminos = forms.BooleanField(
        label=_('Acepto los términos y la política de privacidad'),
        required=True,
        error_messages={'required': _('Debes aceptar los términos y la política de privacidad.')},
    )
    recibir_novedades = forms.BooleanField(
        label=_('Quiero recibir novedades educativas por correo'),
        required=False,
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'nombre@correo.com',
            'autocomplete': 'email',
            'autocapitalize': 'none',
            'spellcheck': 'false',
            'data-tooltip': _('Usaremos este correo para recuperar el acceso a tu cuenta'),
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Tu nombre'),
            'autocomplete': 'given-name',
            'pattern': r'[\p{L} ]+',
            'title': _('Usa solo letras y espacios.'),
            'data-tooltip': _('Usa solo letras y espacios; puedes incluir tildes'),
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Tu apellido'),
            'autocomplete': 'family-name',
            'pattern': r'[\p{L} ]+',
            'title': _('Usa solo letras y espacios.'),
            'data-tooltip': _('Usa solo letras y espacios; puedes incluir tildes'),
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Elige un nombre de usuario'),
                'autocomplete': 'username',
                'autocapitalize': 'none',
                'spellcheck': 'false',
                'data-tooltip': _('Elige el nombre con el que iniciarás sesión'),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo, ayuda in (('first_name', 'first-name-help'), ('last_name', 'last-name-help')):
            self.fields[campo].widget.attrs['aria-describedby'] = ayuda
        self.fields['username'].widget.attrs['aria-describedby'] = 'username-help'
        self.fields['email'].widget.attrs['aria-describedby'] = 'email-help'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Crea una contraseña'),
            'autocomplete': 'new-password',
            'aria-describedby': 'password-strength-help',
            'data-tooltip': _('Combina al menos 8 caracteres y evita claves comunes'),
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Repite la contraseña'),
            'autocomplete': 'new-password',
            'aria-describedby': 'password-match-help',
            'data-tooltip': _('Repite exactamente la contraseña anterior'),
        })
        self.fields['acepto_terminos'].widget.attrs['aria-describedby'] = 'terms-consent-help'
        if self.is_bound:
            for nombre in self.errors:
                if nombre in self.fields:
                    self.fields[nombre].widget.attrs['aria-invalid'] = 'true'
                    if nombre in ('first_name', 'last_name'):
                        descritos = self.fields[nombre].widget.attrs['aria-describedby']
                        self.fields[nombre].widget.attrs['aria-describedby'] = f'{descritos} {nombre.replace("_", "-")}-error'

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(_('Ese nombre de usuario ya está en uso.'))
        return username

    def clean_first_name(self):
        return _limpiar_nombre_persona(self.cleaned_data['first_name'], 'Nombre')

    def clean_last_name(self):
        return _limpiar_nombre_persona(self.cleaned_data['last_name'], 'Apellido')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data['email']).strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('Ya existe una cuenta registrada con este correo.'))
        return email

class UserForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Correo electrónico'),
            'autocomplete': 'email',
            'autocapitalize': 'none',
            'spellcheck': 'false',
        }),
    )

    current_password = forms.CharField(
        label=_('Contraseña actual'),
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password',
            'placeholder': _('Necesaria para cambiar el correo'),
        }),
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nombre')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Apellido')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Correo electrónico')
            }),
        }

    def clean_first_name(self):
        return _limpiar_nombre_persona(self.cleaned_data['first_name'], 'Nombre')

    def clean_last_name(self):
        return _limpiar_nombre_persona(self.cleaned_data['last_name'], 'Apellido')

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data['email']).strip()
        existentes = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if existentes.exists():
            raise forms.ValidationError(_('Ya existe una cuenta registrada con este correo.'))
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        if self.instance.pk and email and email.casefold() != self.instance.email.casefold():
            password = cleaned_data.get('current_password', '')
            if not password or not self.instance.check_password(password):
                self.add_error(
                    'current_password',
                    _('Confirma tu contraseña actual para cambiar el correo.'),
                )
        return cleaned_data

class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = [
            'fecha_nacimiento', 'genero', 'ciudad', 'pais', 'telefono',
            'nivel_kichwa', 'biografia', 'avatar', 
            'notificaciones_email', 'perfil_publico', 'participa_ranking'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date',
                'aria-describedby': 'profile-age-preview',
            }),
            'genero': forms.Select(attrs={
                'class': 'form-control'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ciudad')
            }),
            'pais': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('País')
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('10 dígitos'),
                'autocomplete': 'tel',
                'inputmode': 'numeric',
                'pattern': '[0-9]{10}',
                'maxlength': '10',
                'aria-describedby': 'phone-help',
            }),
            'nivel_kichwa': forms.Select(attrs={
                'class': 'form-control'
            }),
            'biografia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Cuéntanos sobre ti...')
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'notificaciones_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'perfil_publico': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'participa_ranking': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

        labels = {
            'fecha_nacimiento': _('Fecha de nacimiento'),
            'genero': _('Género'),
            'ciudad': _('Ciudad'),
            'pais': _('País'),
            'telefono': _('Teléfono'),
            'nivel_kichwa': _('Nivel de Kichwa'),
            'biografia': _('Biografía'),
            'avatar': _('Avatar'),
            'notificaciones_email': _('Recibir novedades educativas por correo'),
            'perfil_publico': _('Mostrar mi perfil públicamente'),
            'participa_ranking': _('Mostrar mi usuario y puntos en el ranking público'),
        }

        help_texts = {
            'participa_ranking': _('Opcional. Puedes dejar de aparecer desmarcando esta opción cuando quieras.'),
            'telefono': _('Opcional y privado. Escribe exactamente 10 dígitos, sin espacios ni símbolos.'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].widget.attrs['max'] = timezone.localdate().isoformat()
        self.fields['telefono'].strip = False
        self.fields['genero'].choices = [('', '---------'), ('M', _('Masculino')), ('F', _('Femenino')), ('O', _('Otro'))]
        self.fields['nivel_kichwa'].choices = [
            ('principiante', _('Principiante')), ('intermedio', _('Intermedio')),
            ('avanzado', _('Avanzado')), ('nativo', _('Nativo')),
        ]

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '')
        if telefono and not re.fullmatch(r'[0-9]{10}', telefono):
            raise forms.ValidationError(_('El teléfono debe tener exactamente 10 dígitos numéricos.'))
        return telefono

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError(_('La fecha de nacimiento no puede ser futura.'))
        return fecha

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > 2 * 1024 * 1024:
            raise forms.ValidationError(_('La imagen debe pesar 2 MB o menos.'))
        if avatar and (avatar.image.width > 4096 or avatar.image.height > 4096):
            raise forms.ValidationError(_('La imagen no puede superar 4096 × 4096 píxeles.'))
        return avatar


class CambioContrasenaForm(PasswordChangeForm):
    """Conserva todas las validaciones de contraseña configuradas en Django."""

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        configuracion = {
            'old_password': (_('Contraseña actual'), 'current-password', _('Confirma tu contraseña actual')),
            'new_password1': (_('Contraseña nueva'), 'new-password', _('Crea una contraseña nueva')),
            'new_password2': (_('Confirmar contraseña nueva'), 'new-password', _('Repite la contraseña nueva')),
        }
        for nombre, (etiqueta, autocompletar, marcador) in configuracion.items():
            campo = self.fields[nombre]
            campo.label = etiqueta
            campo.widget.attrs.update({
                'class': 'form-control',
                'autocomplete': autocompletar,
                'placeholder': marcador,
            })
