# PostgreSQL y producción

Usa `docker-compose.postgres.yml` solo para desarrollo local. Para producción,
configura un servidor PostgreSQL administrado, `DEBUG=False`, una `SECRET_KEY`
aleatoria, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y HTTPS antes de ejecutar.
Las únicas variables de base admitidas por Django son `DATABASE_ENGINE`,
`DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST` y
`DATABASE_PORT`; no uses los nombres antiguos `DB_*`.

Antes de migrar, prueba las credenciales con el cliente de PostgreSQL. La cuenta
de aplicación debe tener acceso únicamente a la base del diccionario, no ser un
superusuario de PostgreSQL. Después ejecuta:

```powershell
python manage.py check --deploy
python manage.py collectstatic --noinput
```

No elimines SQLite hasta validar una migración lógica en una copia y conservar
un respaldo recuperable.
