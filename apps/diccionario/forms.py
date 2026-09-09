from django import forms
from .models import Palabra, Categoria

class BusquedaForm(forms.Form):
    termino = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar palabra en kichwa o español...',
            'autocomplete': 'off'
        })
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all().order_by('grupo', 'orden', 'nombre'),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    dificultad = forms.ChoiceField(
        label='Dificultad de pronunciación',
        choices=[('', 'Cualquier dificultad')] + Palabra.DIFICULTAD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class ContactoForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre completo'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com'
        })
    )
    
    asunto = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Asunto del mensaje'
        })
    )
    
    mensaje = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Escribe tu mensaje aquí...'
        })
    )

class PalabraForm(forms.ModelForm):
    class Meta:
        model = Palabra
        fields = [
            'palabra_kichwa', 'traduccion_espanol', 'definicion', 
            'pronunciacion', 'audio', 'categoria', 'categoria_propuesta', 'dificultad', 'nivel_dificultad',
            'tipo', 'estado_revision', 'apta_para_juegos', 'dificultad_juego',
            'descripcion_juego_espanol', 'descripcion_juego_kichwa',
            'notas_gramaticales', 'ejemplo_uso', 'activa'
        ]
        widgets = {
            'palabra_kichwa': forms.TextInput(attrs={'class': 'form-control'}),
            'traduccion_espanol': forms.TextInput(attrs={'class': 'form-control'}),
            'definicion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'pronunciacion': forms.TextInput(attrs={'class': 'form-control'}),
            'audio': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'categoria_propuesta': forms.Select(attrs={'class': 'form-select'}),
            'dificultad': forms.Select(attrs={'class': 'form-select'}),
            'nivel_dificultad': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'estado_revision': forms.Select(attrs={'class': 'form-select'}),
            'dificultad_juego': forms.Select(attrs={'class': 'form-select'}),
            'descripcion_juego_espanol': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'descripcion_juego_kichwa': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notas_gramaticales': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'ejemplo_uso': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'apta_para_juegos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
