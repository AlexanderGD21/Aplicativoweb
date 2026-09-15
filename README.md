# Diccionario Kichwa V1

Aplicación Django para el corpus Kichwa Unificado–español.

La secuencia de funciones de aprendizaje y su estado están en
[`docs/HOJA_DE_RUTA_APRENDIZAJE.md`](docs/HOJA_DE_RUTA_APRENDIZAJE.md).

Para iniciar:

```powershell
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver
```

Las credenciales se configuran en `.env`, ignorado por Git. Copia
`.env.example` y reemplaza sus valores de ejemplo. La aplicación utiliza
exclusivamente PostgreSQL: configura `DATABASE_ENGINE=postgresql` y las
variables `DATABASE_*`.

## Pruebas con PostgreSQL

Con PostgreSQL 18 instalado localmente, ejecuta la suite en una instancia
temporal separada de la base configurada en `.env`:

```powershell
.\scripts\probar_postgresql_aislado.ps1
```

El script crea un clúster con contraseña aleatoria en un puerto local libre,
ejecuta `manage.py test` y detiene y elimina el clúster al terminar. Si los
binarios están en otra carpeta, indica `-PostgresBin 'ruta\al\bin'`.

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

## Español e inglés

La interfaz ofrece ambos idiomas y conserva la elección en una cookie. El
procedimiento para ampliar y revisar las equivalencias inglesas está en
[`docs/INTERNACIONALIZACION.md`](docs/INTERNACIONALIZACION.md). Ninguna
traducción pendiente se incorpora automáticamente a la búsqueda ni a los
juegos en inglés.
