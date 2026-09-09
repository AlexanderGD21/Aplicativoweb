#!/usr/bin/env python
"""
Script para crear usuarios masivamente desde un archivo CSV
Uso: python scripts/crear_usuarios_masivo.py archivo.csv
"""

import os
import sys
import django
import csv
from django.db import transaction

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.contrib.auth.models import User
from apps.usuarios.models import PerfilUsuario

def crear_usuarios_desde_csv(archivo_csv):
    """
    Crear usuarios desde un archivo CSV
    Formato esperado: username,email,first_name,last_name,password,ciudad,nivel_kichwa
    """
    usuarios_creados = 0
    errores = []
    
    try:
        with open(archivo_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):  # Start=2 porque la fila 1 son headers
                try:
                    with transaction.atomic():
                        # Validar campos requeridos
                        required_fields = ['username', 'email', 'password']
                        for field in required_fields:
                            if not row.get(field, '').strip():
                                raise ValueError(f'Campo requerido vacío: {field}')
                        
                        # Verificar si el usuario ya existe
                        username = row['username'].strip()
                        email = row['email'].strip()
                        
                        if User.objects.filter(username=username).exists():
                            raise ValueError(f'El usuario {username} ya existe')
                        
                        if User.objects.filter(email=email).exists():
                            raise ValueError(f'El email {email} ya está registrado')
                        
                        # Crear usuario
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=row['password'].strip(),
                            first_name=row.get('first_name', '').strip(),
                            last_name=row.get('last_name', '').strip()
                        )
                        
                        # Actualizar perfil si hay datos adicionales
                        perfil = user.perfilusuario
                        
                        if row.get('ciudad'):
                            perfil.ciudad = row['ciudad'].strip()
                        
                        if row.get('nivel_kichwa') in ['principiante', 'intermedio', 'avanzado', 'experto']:
                            perfil.nivel_kichwa = row['nivel_kichwa'].strip()
                        
                        if row.get('pais'):
                            perfil.pais = row['pais'].strip()
                        
                        if row.get('biografia'):
                            perfil.biografia = row['biografia'].strip()
                        
                        perfil.save()
                        
                        usuarios_creados += 1
                        print(f'✓ Usuario creado: {username}')
                        
                except Exception as e:
                    error_msg = f'Fila {row_num}: {str(e)}'
                    errores.append(error_msg)
                    print(f'✗ Error en fila {row_num}: {e}')
    
    except FileNotFoundError:
        print(f'Error: No se encontró el archivo {archivo_csv}')
        return
    except Exception as e:
        print(f'Error leyendo el archivo: {e}')
        return
    
    # Resumen
    print(f'\n--- RESUMEN ---')
    print(f'Usuarios creados exitosamente: {usuarios_creados}')
    print(f'Errores encontrados: {len(errores)}')
    
    if errores:
        print('\nErrores detallados:')
        for error in errores:
            print(f'  - {error}')

def crear_archivo_ejemplo():
    """Crear un archivo CSV de ejemplo"""
    ejemplo_csv = 'ejemplo_usuarios.csv'
    
    with open(ejemplo_csv, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Headers
        writer.writerow([
            'username', 'email', 'first_name', 'last_name', 'password',
            'ciudad', 'pais', 'nivel_kichwa', 'biografia'
        ])
        
        # Datos de ejemplo
        ejemplos = [
            ['maria_lopez', 'maria@ejemplo.com', 'María', 'López', 'password123',
             'Quito', 'Ecuador', 'principiante', 'Estudiante interesada en Kichwa'],
            ['carlos_garcia', 'carlos@ejemplo.com', 'Carlos', 'García', 'password123',
             'Cuenca', 'Ecuador', 'intermedio', 'Profesor de idiomas'],
            ['ana_rodriguez', 'ana@ejemplo.com', 'Ana', 'Rodríguez', 'password123',
             'Riobamba', 'Ecuador', 'avanzado', 'Investigadora cultural']
        ]
        
        for ejemplo in ejemplos:
            writer.writerow(ejemplo)
    
    print(f'Archivo de ejemplo creado: {ejemplo_csv}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python scripts/crear_usuarios_masivo.py <archivo.csv>')
        print('Para crear un archivo de ejemplo: python scripts/crear_usuarios_masivo.py --ejemplo')
        sys.exit(1)
    
    if sys.argv[1] == '--ejemplo':
        crear_archivo_ejemplo()
    else:
        archivo_csv = sys.argv[1]
        crear_usuarios_desde_csv(archivo_csv)
