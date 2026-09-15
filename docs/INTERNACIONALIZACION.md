# Internacionalización y traducciones inglesas

La interfaz usa la internacionalización de Django con español como idioma
predeterminado e inglés como alternativa. `LocaleMiddleware` conserva la
elección hecha desde el selector de la navegación. El catálogo editable está
en `locale/en/LC_MESSAGES/django.po`; para regenerar su archivo binario sin
instalar GNU gettext en Windows se ejecuta:

```powershell
.\venv\Scripts\python.exe scripts\compilar_catalogo_ingles.py
```

## Límite editorial del corpus

Cada acepción tiene `traduccion_ingles`, `definicion_ingles` y
`estado_revision_ingles`. Los estados son `pendiente`, `revisada` y `validada`.
Solo una traducción no vacía y `validada` se utiliza en resultados, sugerencias
y juegos ingleses. Si una entrada todavía no está validada, su detalle lo
indica y conserva la equivalencia española como referencia.

Las 20 categorías tienen nombre y descripción ingleses. La migración 0030
incluye un conjunto inicial de vocabulario concreto y prioritario; esto inicia
el flujo y no representa una traducción automática del corpus completo.

## Revisión por CSV

Para preparar el archivo de trabajo con todas las entradas activas:

```powershell
.\venv\Scripts\python.exe manage.py gestionar_traducciones_ingles `
  --exportar tmp\traducciones_ingles.csv
```

También se puede exportar una cola concreta con `--estado pendiente`. Las
columnas Kichwa, español y categoría sirven de contexto. La persona revisora
completa `traduccion_ingles`, `definicion_ingles` y cambia el estado. Una fila
marcada `revisada` o `validada` no puede tener la traducción vacía.

Después de revisar el archivo:

```powershell
.\venv\Scripts\python.exe manage.py gestionar_traducciones_ingles `
  --importar tmp\traducciones_ingles.csv
```

La importación valida todas las filas antes de escribir. Si encuentra un ID
desconocido, duplicado, un estado inválido o una traducción publicable vacía,
no modifica ninguna entrada. El mismo trabajo puede hacerse desde Django Admin,
que incluye filtros y acciones separadas para marcar traducciones revisadas o
validadas.
