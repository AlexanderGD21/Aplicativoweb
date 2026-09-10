from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import PerfilUsuario


def _limpiar_nombre_persona(valor, etiqueta):
    valor = ' '.join(valor.split())
    if not valor:
        raise forms.ValidationError(f'Ingresa tu {etiqueta.lower()}.')
    if not all(caracter.isalpha() or caracter in " '-" for caracter in valor):
        raise forms.ValidationError(
            f'El {etiqueta.lower()} solo puede contener letras, espacios, apóstrofes o guiones.'
        )
    return valor


class LoginForm(AuthenticationForm):
    """Autenticación con nombre de usuario o correo sin revelar cuentas existentes."""

    username = forms.CharField(
        label='Usuario o correo electrónico',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'username',
            'autocapitalize': 'none',
            'spellcheck': 'false',
            'placeholder': 'Tu usuario o correo',
        }),
    )
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password',
            'placeholder': 'Tu contraseña',
        }),
    )
    error_messages = {
        'invalid_login': 'No pudimos iniciar sesión con esos datos. Revisa el usuario o correo y la contraseña.',
        'inactive': 'Esta cuenta no está disponible.',
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
        label='Acepto los términos y la política de privacidad',
        required=True,
        error_messages={'required': 'Debes aceptar los términos y la política de privacidad.'},
    )
    recibir_novedades = forms.BooleanField(
        label='Quiero recibir novedades educativas por correo',
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
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre',
            'autocomplete': 'given-name',
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu apellido',
            'autocomplete': 'family-name',
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Elige un nombre de usuario',
                'autocomplete': 'username',
                'autocapitalize': 'none',
                'spellcheck': 'false',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['aria-describedby'] = 'username-help'
        self.fields['email'].widget.attrs['aria-describedby'] = 'email-help'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Crea una contraseña',
            'autocomplete': 'new-password',
            'aria-describedby': 'password-strength-help',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Repite la contraseña',
            'autocomplete': 'new-password',
            'aria-describedby': 'password-match-help',
        })
        self.fields['acepto_terminos'].widget.attrs['aria-describedby'] = 'terms-consent-help'
        if self.is_bound:
            for nombre in self.errors:
                if nombre in self.fields:
                    self.fields[nombre].widget.attrs['aria-invalid'] = 'true'

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Ese nombre de usuario ya está en uso.')
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
            raise forms.ValidationError('Ya existe una cuenta registrada con este correo.')
        return email

class UserForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico',
            'autocomplete': 'email',
            'autocapitalize': 'none',
            'spellcheck': 'false',
        }),
    )

    current_password = forms.CharField(
        label='Contraseña actual',
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password',
            'placeholder': 'Necesaria para cambiar el correo',
        }),
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico'
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
            raise forms.ValidationError('Ya existe una cuenta registrada con este correo.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        if self.instance.pk and email and email.casefold() != self.instance.email.casefold():
            password = cleaned_data.get('current_password', '')
            if not password or not self.instance.check_password(password):
                self.add_error(
                    'current_password',
                    'Confirma tu contraseña actual para cambiar el correo.',
                )
        return cleaned_data

class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = [
            'fecha_nacimiento', 'genero', 'ciudad', 'pais', 'telefono',
            'nivel_kichwa', 'biografia', 'avatar', 
            'notificaciones_email', 'perfil_publico'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-control'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad'
            }),
            'pais': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'País'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono (privado)',
                'autocomplete': 'tel',
            }),
            'nivel_kichwa': forms.Select(attrs={
                'class': 'form-control'
            }),
            'biografia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Cuéntanos sobre ti...'
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
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > 2 * 1024 * 1024:
            raise forms.ValidationError('La imagen debe pesar 2 MB o menos.')
        if avatar and (avatar.image.width > 4096 or avatar.image.height > 4096):
            raise forms.ValidationError('La imagen no puede superar 4096 × 4096 píxeles.')
        return avatar
