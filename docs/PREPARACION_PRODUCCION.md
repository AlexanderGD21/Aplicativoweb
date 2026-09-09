# Preparación para producción

El proyecto continúa en etapa de pulido local. No activar el despliegue todavía.

## Antes de publicar

1. Finalizar las mejoras funcionales, visuales, accesibilidad, juegos y búsqueda.
2. Ejecutar pruebas automatizadas y una revisión manual completa.
3. Elegir proveedor de alojamiento y dominio.
4. Configurar PostgreSQL administrado y restaurar una copia verificada de los datos.
5. Definir variables de producción sin subir `.env` al repositorio:

   ```env
   DEBUG=False
   ALLOWED_HOSTS=tudominio.com,www.tudominio.com
   CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://www.tudominio.com
   USE_X_FORWARDED_PROTO=True
   ```

6. Generar una `SECRET_KEY` nueva, larga y única para producción.
7. Configurar correo SMTP para recuperación de contraseñas, archivos estáticos, medios y copias de seguridad.
8. Asociar el dominio y confirmar que el proveedor emita el certificado HTTPS.
9. Verificar HTTPS, redirección HTTP, inicio de sesión, registro, recuperación de contraseña, búsqueda, juegos y panel de administración.

El código activa redirección HTTPS, cookies seguras y HSTS cuando `DEBUG=False`.
