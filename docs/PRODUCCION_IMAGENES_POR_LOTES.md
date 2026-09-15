# Producción de imágenes por lotes

La aplicación administra la producción de ilustraciones desde PostgreSQL. Cada
registro pertenece a una acepción exacta de `Palabra`; dos traducciones de una
misma forma Kichwa mantienen procesos e imágenes independientes.

## Estados de trabajo

1. `clasificada`: la acepción tiene un tipo visual propuesto por su categoría.
2. `preparada`: pertenece a un lote y tiene prompt y texto alternativo candidato.
3. `generada`: el archivo existe en los estáticos del proyecto.
4. `revisada`: un administrador comprobó imagen, acepción y texto alternativo.
5. `publicada`: la ruta revisada se copió a la acepción y se muestra en el sitio.
6. `descartada`: la propuesta no debe continuar.

La clasificación es una ayuda operativa. No sustituye la revisión del sentido ni
garantiza que todas las acepciones abstractas necesiten una imagen.

## Primer lote

La migración `0028_preparacionimagenvocabulario` clasificó las 4.454 acepciones
que existen actualmente. Conservó las 11 ilustraciones iniciales como publicadas.
El lote 1 contiene 100 propuestas concretas y balanceadas por categoría. Su
manifiesto revisable está en `docs/lotes_imagenes/lote-001.csv`.

Para preparar un lote posterior:

```powershell
.\venv\Scripts\python.exe manage.py preparar_lote_imagenes `
  --cantidad 100 `
  --lote 2 `
  --salida docs\lotes_imagenes\lote-002.csv
```

El comando es deliberadamente independiente del proveedor de imágenes. Una
integración externa deberá leer la credencial desde `.env`, guardar la autoría,
licencia y página de origen, y colocar primero el archivo como candidato. La
publicación se realiza con las acciones de revisión de Django Admin.

Las claves de API nunca deben copiarse al repositorio, a un CSV ni a los prompts.
Antes de conectar un servicio se debe confirmar si la clave pertenece a Pexels,
Pixabay, Unsplash u otro proveedor, porque sus endpoints y requisitos de
atribución son diferentes.
