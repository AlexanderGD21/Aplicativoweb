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
python manage.py reestructurar_diccionario
python manage.py reestructurar_diccionario --apply
python manage.py importar_audios_estaticos --apply
```

`reestructurar_diccionario` muestra primero una vista previa. Con `--apply`
crea la taxonomía temática, clasifica las entradas pendientes, recalcula la
dificultad de pronunciación y actualiza los campos de búsqueda bilingüe sin
tildes. Cada decisión guarda una confianza y una explicación auditable; las
entradas de confianza baja permanecen señaladas para revisión humana en
`/admin/`. Usa `--force` solo si también deseas reemplazar categorías revisadas
o validadas manualmente.

## Vocabulario de juegos

Los juegos también usan entradas generales del diccionario. La selección exige
un par Kichwa–español breve y descarta listas de variantes o glosas extensas;
mantiene el tema y la `dificultad` de pronunciación de cada entrada. La marca
histórica `apta_para_juegos` ya no es una condición obligatoria y
`dificultad_juego` no reemplaza la dificultad del diccionario en los filtros.
Las entradas de confianza baja aún requieren revisión lingüística humana.

La IA está apagada por defecto; valida su configuración con
`python manage.py verificar_ia_kichwa`.
