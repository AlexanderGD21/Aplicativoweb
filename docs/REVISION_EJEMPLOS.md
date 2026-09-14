# Revisión editorial de ejemplos de uso

Al iniciar esta fase, las 4.509 entradas tenían en `ejemplo_uso` la equivalencia
automática «palabra - traducción». No eran oraciones. La migración 0025 elimina
únicamente esos marcadores; cualquier texto heredado distinto queda conservado
para revisión, pero no se publica directamente.

Los ejemplos nuevos se gestionan en **Django Admin → Ejemplos de uso**. Cada
borrador requiere una oración en Kichwa, su traducción completa al español y una
fuente identificable (obra, informante autorizado o autoría propia). El personal
editorial debe comprobar con una persona competente la variedad lingüística,
ortografía, sentido en contexto y permiso de publicación de la fuente. El estado
de revisión de la entrada del diccionario es independiente del ejemplo.

Después de esa comprobación, la acción **Publicar tras revisión editorial**
registra al responsable y la fecha. Solo entonces aparece el ejemplo bilingüe y
su fuente en el detalle público. La acción **Retirar publicación** lo oculta.
Editar la oración, traducción, fuente o entrada asociada lo devuelve a borrador y
exige una nueva revisión.

No se generaron oraciones artificiales ni se declararon revisados contenidos que
no hayan pasado por este flujo. El siguiente trabajo editorial consiste en
aprobar borradores documentados y ampliar la cobertura del vocabulario prioritario.

## Módulo autorizado de IST Tena (2023)

El propietario del proyecto autorizó usar el módulo compilado por Lic. Miguel
Narváez, M.Sc. Se cotejaron visualmente las tablas bilingües de las páginas PDF
17, 18, 25, 29 y 83. El comando
`python manage.py preparar_ejemplos_modulo_2023` prepara nueve oraciones de siete
lemas existentes como **borradores**. Registra página PDF y sección en `fuente`,
ajusta solo puntuación y ortografía española evidente, y no atribuye la revisión a una
cuenta humana ni publica los ejemplos por sí mismo. Puede ejecutarse otra vez
sin duplicar las oraciones que no hayan cambiado.

| Lema | Oración Kichwa | Español | Página PDF | Comprobación editorial pendiente |
| --- | --- | --- | --- | --- |
| `shamuna` | Kayman shamuy. | Ven para acá. | 18 | Imperativo del lema. |
| `shamuna` | Kayman shamupay. | Ven para acá por favor. | 18 | Matiz de cortesía. |
| `mikuna` | Ama mikuychu. | No comas. | 18 | Imperativo negativo. |
| `mikuna` | Ñuka mikuni. | Yo como. | 83 | Conjugación del presente. |
| `ayllu` | Shamuk watakaman llakishka ayllukuna. | Hasta el próximo año querida familia. | 17 | Uso del plural `-kuna` frente a «familia». |
| `rina` | Mayman rinki? | ¿Adónde vas? | 29 | Flexión verbal `rinki`. |
| `apana` | Imata apanki? | ¿Qué llevas? | 29 | Flexión verbal `apanki`. |
| `mashi` | Pitak kanpak mashika kan? | ¿Quién es tu amigo? | 29 | Uso de `mashika`. |
| `kiwa` | Imapak kiwataka apanki? | ¿Para qué llevas la hierba? | 29 | Uso de `kiwataka`. |

Antes de aprobar, comprobar en la página citada la forma Kichwa, la traducción,
la flexión del lema y el contexto. La autorización del módulo no sustituye esa
revisión de cada oración. El PDF se conserva fuera del repositorio; no se copia
íntegro ni se publica desde la aplicación.

El módulo combina materiales propios y fuentes citadas, y las páginas PDF
118–153 contienen un vocabulario en imágenes cuyo texto no se extrae de forma
fiable. Por ello no se importó automáticamente ese bloque ni se trataron listas
de equivalencias como oraciones.
