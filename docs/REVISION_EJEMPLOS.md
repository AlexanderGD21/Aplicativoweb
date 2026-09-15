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
registra al responsable y la fecha. Para una transcripción cotejada directamente
con una fuente autorizada, el comando puede registrar una **revisión documental**
sin atribuírsela a una cuenta humana. Solo entonces aparece el ejemplo bilingüe y
su fuente en el detalle público. La acción **Retirar publicación** lo oculta.
Editar la oración, traducción, fuente o entrada asociada lo devuelve a borrador y
exige una nueva revisión.

No se generaron oraciones artificiales ni se declararon revisados contenidos que
no hayan pasado por este flujo. Hay 29 ejemplos publicados tras cotejo documental.
El trabajo editorial futuro consiste en obtener una validación lingüística
independiente y seguir ampliando la cobertura con fuentes identificables.

## Módulo autorizado de IST Tena (2023)

El propietario del proyecto autorizó usar el módulo compilado por Lic. Miguel
Narváez, M.Sc. Se cotejaron visualmente las tablas bilingües de las páginas PDF
17, 18, 24, 25, 29 y 83. El comando
`python manage.py preparar_ejemplos_modulo_2023` prepara 29 oraciones de 11
lemas existentes como borradores. Registra página PDF y sección en `fuente`,
ajusta solo puntuación y ortografía española evidente, y puede ejecutarse otra vez
sin duplicar las oraciones que no hayan cambiado. La opción
`--publicar-cotejados` registra fecha, método y alcance de la comprobación sin
atribuirla a una cuenta humana.

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

Los nueve borradores iniciales fueron cotejados visualmente con las páginas
citadas. Sus formas y traducciones coinciden con el módulo. El uso colectivo de
`ayllukuna` traducido como «familia» se conserva tal como está en la fuente. El
cotejo documental confirma la transcripción; no pretende sustituir una futura
validación lingüística independiente de la variedad y sus matices.

La ampliación añade 20 formas conjugadas documentadas: cuatro de `rimana` en la
página PDF 24 y cuatro de cada uno de `tarpuna`, `mikuna`, `killkana` y `takina`
en la página PDF 25. Se combinaron el sujeto y el verbo que aparecen en cada fila
de las tablas, y se normalizó la redacción española sin cambiar el sentido.

El módulo combina materiales propios y fuentes citadas, y las páginas PDF
118–153 contienen un vocabulario en imágenes cuyo texto no se extrae de forma
fiable. Por ello no se importó automáticamente ese bloque ni se trataron listas
de equivalencias como oraciones.
