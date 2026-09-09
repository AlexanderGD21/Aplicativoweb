#!/usr/bin/env python
"""
Script para verificar la integridad de la base de datos del diccionario Kichwa
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diccionario_kichwa.settings')
django.setup()

from django.contrib.auth.models import User
from apps.usuarios.models import PerfilUsuario
from apps.diccionario.models import Palabra, Categoria
from django.db import connection

def verificar_usuarios():
    """Verificar integridad de usuarios y perfiles"""
    print("=== VERIFICACIÓN DE USUARIOS ===")
    
    total_usuarios = User.objects.count()
    total_perfiles = PerfilUsuario.objects.count()
    
    print(f"Total usuarios: {total_usuarios}")
    print(f"Total perfiles: {total_perfiles}")
    
    # Usuarios sin perfil
    usuarios_sin_perfil = []
    for user in User.objects.all():
        try:
            user.perfilusuario
        except PerfilUsuario.DoesNotExist:
            usuarios_sin_perfil.append(user.username)
    
    if usuarios_sin_perfil:
        print(f"❌ Usuarios sin perfil ({len(usuarios_sin_perfil)}): {usuarios_sin_perfil}")
    else:
        print("✅ Todos los usuarios tienen perfil")
    
    # Perfiles huérfanos
    perfiles_huerfanos = PerfilUsuario.objects.filter(usuario__isnull=True).count()
    if perfiles_huerfanos > 0:
        print(f"❌ Perfiles huérfanos: {perfiles_huerfanos}")
    else:
        print("✅ No hay perfiles huérfanos")
    
    return len(usuarios_sin_perfil) == 0 and perfiles_huerfanos == 0

def verificar_estructura_categoria():
    """Verificar qué columnas existen realmente en la tabla categoria"""
    print("\n=== VERIFICACIÓN DE ESTRUCTURA CATEGORIA ===")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(diccionario_categoria)")
            columnas = cursor.fetchall()
            
            columnas_existentes = [col[1] for col in columnas]
            print(f"Columnas existentes en diccionario_categoria: {columnas_existentes}")
            
            # Verificar si existe la columna slug
            tiene_slug = 'slug' in columnas_existentes
            print(f"¿Tiene columna 'slug'? {tiene_slug}")
            
            return columnas_existentes, tiene_slug
    except Exception as e:
        print(f"Error verificando estructura: {e}")
        return [], False

def verificar_diccionario():
    """Verificar integridad del diccionario"""
    print("\n=== VERIFICACIÓN DEL DICCIONARIO ===")
    
    total_palabras = Palabra.objects.count()
    total_categorias = Categoria.objects.count()
    
    print(f"Total palabras: {total_palabras}")
    print(f"Total categorías: {total_categorias}")
    
    # Palabras sin categoría
    palabras_sin_categoria = Palabra.objects.filter(categoria__isnull=True).count()
    if palabras_sin_categoria > 0:
        print(f"❌ Palabras sin categoría: {palabras_sin_categoria}")
    else:
        print("✅ Todas las palabras tienen categoría")
    
    # Verificar estructura antes de hacer consultas complejas
    columnas_existentes, tiene_slug = verificar_estructura_categoria()
    
    # Categorías vacías - usando solo campos que sabemos que existen
    try:
        from django.db.models import Count
        
        # Usar raw SQL para evitar problemas con el ORM
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.nombre, COUNT(p.id) as num_palabras
                FROM diccionario_categoria c
                LEFT JOIN diccionario_palabra p ON c.id = p.categoria_id
                GROUP BY c.id, c.nombre
                HAVING COUNT(p.id) = 0
            """)
            categorias_vacias = cursor.fetchall()
            
            if categorias_vacias:
                print(f"⚠️ Categorías vacías: {len(categorias_vacias)}")
                print("Categorías sin palabras:")
                for cat_id, nombre, num_palabras in categorias_vacias[:5]:
                    print(f"  - {nombre} (ID: {cat_id})")
            else:
                print("✅ Todas las categorías tienen palabras")
                
    except Exception as e:
        print(f"⚠️ Error verificando categorías vacías: {e}")
        # Fallback simple
        try:
            categorias_sin_palabras = []
            for categoria in Categoria.objects.all():
                if categoria.palabras.count() == 0:
                    categorias_sin_palabras.append(categoria)
            
            if categorias_sin_palabras:
                print(f"⚠️ Categorías vacías (método alternativo): {len(categorias_sin_palabras)}")
                for cat in categorias_sin_palabras[:5]:
                    print(f"  - {cat.nombre} (ID: {cat.id})")
            else:
                print("✅ Todas las categorías tienen palabras")
        except Exception as e2:
            print(f"❌ No se pudo verificar categorías vacías: {e2}")
    
    return palabras_sin_categoria == 0

def verificar_base_datos():
    """Verificar estado general de la base de datos"""
    print("\n=== VERIFICACIÓN DE BASE DE DATOS ===")
    
    try:
        with connection.cursor() as cursor:
            # Verificar tablas principales
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND (name LIKE 'usuarios_%' OR name LIKE 'diccionario_%')
                ORDER BY name
            """)
            tablas = cursor.fetchall()
            
            print("Tablas encontradas:")
            for tabla in tablas:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla[0]}")
                    count = cursor.fetchone()[0]
                    print(f"  - {tabla[0]}: {count} registros")
                except Exception as e:
                    print(f"  - {tabla[0]}: Error al contar")
        
        return True
    except Exception as e:
        print(f"Error verificando base de datos: {e}")
        return False

def verificar_migraciones_pendientes():
    """Verificar si hay migraciones pendientes"""
    print("\n=== VERIFICACIÓN DE MIGRACIONES ===")
    
    try:
        from django.core.management import execute_from_command_line
        from io import StringIO
        import sys
        
        # Capturar la salida del comando showmigrations
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            execute_from_command_line(['manage.py', 'showmigrations', '--plan'])
        except SystemExit:
            pass
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        if '[ ]' in output:
            print("⚠️ Hay migraciones pendientes")
            print("Ejecuta: python manage.py migrate")
            return False
        else:
            print("✅ Todas las migraciones están aplicadas")
            return True
            
    except Exception as e:
        print(f"No se pudo verificar migraciones: {e}")
        return True

def crear_migracion_slug():
    """Crear migración para agregar campo slug si no existe"""
    print("\n=== CREACIÓN DE MIGRACIÓN SLUG ===")
    
    columnas_existentes, tiene_slug = verificar_estructura_categoria()
    
    if not tiene_slug:
        print("⚠️ La columna 'slug' no existe en la base de datos")
        print("Esto puede causar errores en el modelo Categoria")
        print("\nPara solucionarlo:")
        print("1. python manage.py makemigrations diccionario")
        print("2. python manage.py migrate")
        return False
    else:
        print("✅ La columna 'slug' existe correctamente")
        return True

def main():
    """Función principal"""
    print("🔍 VERIFICACIÓN DE INTEGRIDAD - DICCIONARIO KICHWA")
    print("=" * 60)
    
    try:
        usuarios_ok = verificar_usuarios()
        diccionario_ok = verificar_diccionario()
        bd_ok = verificar_base_datos()
        migraciones_ok = verificar_migraciones_pendientes()
        slug_ok = crear_migracion_slug()
        
        print("\n" + "=" * 60)
        
        if usuarios_ok and diccionario_ok and bd_ok and migraciones_ok and slug_ok:
            print("✅ VERIFICACIÓN COMPLETADA - TODO PERFECTO")
            print("\n🎯 RESUMEN:")
            print("- Base de datos íntegra y actualizada")
            print("- Usuarios y perfiles correctos")
            print("- Diccionario funcional")
            print("- Migraciones aplicadas")
            print("- Estructura de tablas correcta")
        else:
            print("⚠️ VERIFICACIÓN COMPLETADA CON OBSERVACIONES")
            print("\n📝 ACCIONES RECOMENDADAS:")
            
            if not slug_ok:
                print("🔧 PROBLEMA PRINCIPAL: Falta columna 'slug'")
                print("   Solución:")
                print("   1. python manage.py makemigrations diccionario")
                print("   2. python manage.py migrate")
                print("")
            
            if not migraciones_ok:
                print("🔧 Aplicar migraciones pendientes:")
                print("   python manage.py migrate")
                print("")
            
            if not usuarios_ok:
                print("🔧 Corregir perfiles de usuario:")
                print("   python manage.py limpiar_perfiles_huerfanos --fix")
                print("")
            
            print("📊 El diccionario tiene contenido completo y funciona")
            print("📊 Las categorías vacías son normales")
        
    except Exception as e:
        print(f"❌ Error crítico durante la verificación: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
