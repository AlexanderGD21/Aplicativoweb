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

## Fotografías candidatas de Pexels

Pexels funciona como buscador de fotografías de terceros; no genera
ilustraciones originales. Por ese motivo sus resultados se guardan como
candidatas y no sustituyen automáticamente las once ilustraciones infantiles
originales. La revisión debe comprobar que la foto representa la acepción y que
es adecuada para público infantil.

Guarda la clave únicamente en el `.env` local:

```dotenv
PEXELS_API_KEY=tu_clave_privada
PEXELS_API_TIMEOUT=20
```

Para buscar tres opciones cuadradas por cada acepción del lote:

```powershell
.\venv\Scripts\python.exe manage.py buscar_candidatas_pexels `
  --lote 1 --cantidad 100 --resultados 3
```

Cada resultado conserva el ID de Pexels, la página de la foto, la URL del autor,
la descripción original y el tamaño. En Django Admin, abre **Candidatas de
Pexels**, revisa las opciones y ejecuta **Seleccionar una candidata por
acepción**. Luego descarga y convierte las seleccionadas a WebP de 768 × 768:

```powershell
.\venv\Scripts\python.exe manage.py descargar_candidatas_pexels `
  --lote 1 --cantidad 100
```

La descarga deja cada preparación en estado `generada`. Todavía se requieren
las acciones **Aprobar imágenes generadas tras revisión** y **Publicar imágenes
revisadas**. Al publicar, la entrada muestra el fotógrafo y enlaces a su perfil
y a la foto en Pexels.

La [documentación oficial de Pexels](https://www.pexels.com/api/documentation/)
indica autenticación con el encabezado `Authorization`, búsquedas localizadas y
un límite inicial de 200 solicitudes por hora y 20.000 por mes. Sus directrices
para la API solicitan un enlace visible a Pexels y acreditar al fotógrafo cuando
sea posible. La [licencia de Pexels](https://www.pexels.com/license/) permite usar
y modificar las fotos, con las restricciones descritas en esa página.
Las conexiones HTTPS usan `truststore` para validar certificados con el almacén
nativo del sistema operativo; no se desactiva la verificación TLS.

Las claves de API nunca deben copiarse al repositorio, a un CSV ni a los prompts.
