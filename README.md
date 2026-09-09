# Diccionario Kichwa V1

Aplicación Django para el corpus Kichwa Unificado–español. Para iniciar:

```powershell
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver
```

Las credenciales se configuran en `.env`, ignorado por Git. Copia
`.env.example` y reemplaza sus valores de ejemplo. SQLite es local por defecto;
PostgreSQL se habilita con `DATABASE_ENGINE=postgresql` y `DATABASE_*`.

Para trasladar una copia validada de SQLite a PostgreSQL, completa primero las
variables `DATABASE_*` en `.env` y ejecuta:

```powershell
.\scripts\migrar_sqlite_a_postgres.ps1 -Confirmar
```

El script conserva un respaldo y un volcado JSON en `backups/`; no borra la
base SQLite original.

## Curación

```powershell
python manage.py auditar_diccionario --json
python manage.py preparar_categorias --apply
python manage.py proponer_categorias --apply
python manage.py importar_audios_estaticos --apply
```

Las propuestas nunca reclasifican automáticamente: se aceptan o rechazan en
`/admin/`. La IA está apagada por defecto; valida su configuración con
`python manage.py verificar_ia_kichwa`.
