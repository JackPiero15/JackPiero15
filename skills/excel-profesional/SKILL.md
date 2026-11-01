---
name: excel-profesional
description: Crea y da formato a libros de Excel (.xlsx) con aspecto profesional, limpio y legible, de nivel entregable académico o empresarial. Usar siempre que se pida construir, rehacer, mejorar o dar formato a un libro de Excel, modelo financiero, presupuesto, proyección, plan de inversión, estructura de costos, planilla o cualquier tabla en hojas de cálculo, aunque el usuario no mencione el formato. Obliga a fijar anchos de columna, ajustar texto, eliminar filas vacías, aplicar jerarquía visual (título, subtítulo, encabezados, totales), colores por tipo de celda y verificación visual final. Evita el aspecto "gordo", cortado o desordenado.
---

# Excel profesional

Objetivo: que cada hoja se lea de un vistazo, sin texto cortado, sin columnas desproporcionadas y sin espacio muerto.

## Flujo obligatorio

1. Construir contenido y fórmulas con `openpyxl` (las fórmulas siempre como fórmulas, nunca resultados escritos a mano).
2. Dar formato SOLO mediante las funciones de `scripts/estilo_excel.py` (importarlo; no reinventar estilos).
3. Recalcular si hay fórmulas y comprobar cero errores.
4. Verificación visual: convertir a PDF con LibreOffice, rasterizar y mirar cada hoja. Corregir y repetir hasta que la lista de control esté completa.

## Reglas de diseño (no negociables)

**Estructura de cada hoja**
- Fila 1 en blanco angosta. Fila 2: título de la hoja. Fila 3: subtítulo en una línea. Fila 4 en blanco.
- Columna A como margen (ancho 2). El contenido empieza en la columna B.
- Cada bloque: encabezado de sección (A., B., …), tabla, fila de total, UNA fila en blanco antes del siguiente bloque.
- Prohibido dejar filas vacías entre el último dato y la fila de total. Si la tabla crece, el total se desplaza (usar fórmulas con rango que cubra solo las filas con datos).

**Anchos de columna fijos (en caracteres)**
- N° / índice: 5 (nunca más de 6).
- Concepto / Descripción: 55 a 65.
- Montos (Monto, Valor sin IGV, IGV, Total, Precio): 16.
- Indicadores cortos (¿Afecta IGV?, Moneda, Cantidad, Unidad): 12.
- Fuente / Nota / Enlace: 70 a 90, con ajuste de texto.
- Porcentajes y años: 12.
- Ninguna columna sin ancho asignado explícitamente.

**Texto y alturas**
- Ajuste de texto activado en Concepto, Descripción y Nota. Altura de fila mínima 20; aumentar según las líneas del texto (≈15 por línea). Ningún texto cortado ni con "…".
- Alineación vertical centrada en tablas.

**Tipografía** (una sola familia: Calibri)
- Título: 16 negrita, azul marino `1F3864`.
- Subtítulo: 10 cursiva, gris `595959`.
- Encabezado de sección: 12 negrita, azul marino, sin relleno.
- Encabezado de tabla: 11 negrita, blanco sobre `1F3864`, centrado, altura 30.
- Datos: 11. Notas y fuentes: 10 cursiva gris.

**Color por tipo de celda**
- Entrada del usuario (montos y datos que se editan): relleno durazno `FCE4D6`, texto azul `0000FF`.
- Fórmula: texto negro, sin relleno.
- Vínculo a otra hoja: texto verde `008000`.
- Supuesto clave: relleno amarillo suave `FFF2CC`.
- Fila de total: relleno `BDD7EE`, negrita, borde superior grueso.
- Bordes finos gris `BFBFBF` en toda la tabla.

**Formatos numéricos**
- Soles: `"S/" #,##0.00;("S/" #,##0.00);"-"` (ceros como guion, negativos entre paréntesis).
- Porcentajes: `0.0%`, guardados como fracción (0.15 = 15,0 %).
- Años como texto. Cantidades enteras `#,##0`.
- Unidad indicada en el encabezado cuando no sea soles.

**Alineación**
- N° y textos cortos: centrados. Concepto y Nota: izquierda. Montos y porcentajes: derecha.

**Vista**
- Paneles inmovilizados bajo el encabezado de la primera tabla.
- Líneas de cuadrícula ocultas.
- Ampliación 100 %.
- Color de pestaña por tipo de hoja: azul (mercado, demanda, precio), verde (inversión, financiamiento), naranja (planilla, personal), rojo (costos), morado (gastos), gris (carátula, resumen, supuestos), turquesa (ingresos, resultados).

**Contenido**
- Toda cifra supuesta o de fuente externa lleva su fuente en la columna Nota (organismo, documento, fecha). Sin fuente verificable: escribir "supuesto del autor".
- Idioma de todo el libro: el del usuario, sin términos extranjeros innecesarios.

## Uso del módulo

```python
import sys; sys.path.insert(0, "scripts")
from estilo_excel import *

wb = Workbook()
ws = wb.active; ws.title = "Inversión"
preparar_hoja(ws, "ESTRUCTURA DE LA INVERSIÓN", "Gastos preoperativos, activos y capital de trabajo", color_pestana=COLOR_VERDE)

fila = 5
fila = seccion(ws, fila, "A. Inversión fija intangible")
columnas = [("N°","indice"), ("Concepto","texto"), ("Monto pagado","monto"),
            ("¿Afecto a IGV?","corto"), ("Valor sin IGV","monto"), ("IGV","monto"), ("Fuente / nota","nota")]
datos = [[1,"Búsqueda de nombre SUNARP",26,"No","=D{r}","=0","Tasa SUNARP vigente"], ...]
inicio, fin, fila = tabla(ws, fila, columnas, datos, entradas=[3,4])   # entradas: posiciones (base 1) de columnas editables
fila = total(ws, fila, inicio, fin, "TOTAL INVERSIÓN FIJA INTANGIBLE", sumar=[3,5,6])
finalizar_hoja(ws, congelar="B7")
wb.save("salida.xlsx")
```

En `datos`, `{r}` se reemplaza por el número de la fila actual para escribir fórmulas por fila.

## Verificación visual (obligatoria)

```bash
soffice --headless --convert-to pdf salida.xlsx
pdftoppm -r 70 -png salida.pdf vista
```

Abrir cada imagen y comprobar la lista de control:

- [ ] Columna N° ≤ 6 de ancho.
- [ ] Ningún texto cortado o con "…".
- [ ] Cero filas vacías entre datos y total.
- [ ] Título, subtítulo, secciones, encabezados y totales con jerarquía distinta.
- [ ] Entradas en durazno, fórmulas en negro, totales en azul claro.
- [ ] Cuadrícula oculta, paneles inmovilizados, pestañas coloreadas.
- [ ] Cero errores de fórmula tras recalcular.

Si una casilla falla, corregir y volver a verificar. No entregar con casillas incompletas.
