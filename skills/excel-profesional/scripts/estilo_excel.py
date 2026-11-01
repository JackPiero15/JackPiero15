"""Estilos reutilizables para libros de Excel profesionales (openpyxl)."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties

AZUL_MARINO = "1F3864"
AZUL_CLARO = "BDD7EE"
DURAZNO = "FCE4D6"
AMARILLO = "FFF2CC"
GRIS_TEXTO = "595959"
GRIS_BORDE = "BFBFBF"

COLOR_AZUL = "2E75B6"
COLOR_VERDE = "548235"
COLOR_NARANJA = "ED7D31"
COLOR_ROJO = "C00000"
COLOR_MORADO = "7030A0"
COLOR_GRIS = "7F7F7F"
COLOR_TURQUESA = "00B0A0"

FUENTE = "Calibri"
FORMATO_SOLES = '"S/" #,##0.00;("S/" #,##0.00);"-"'
FORMATO_PORCENTAJE = "0.0%"
FORMATO_ENTERO = "#,##0"

# tipo de columna -> (ancho, alineación horizontal, formato numérico, ajustar texto)
TIPOS = {
    "indice": (5, "center", None, False),
    "texto": (60, "left", None, True),
    "monto": (16, "right", FORMATO_SOLES, False),
    "corto": (12, "center", None, False),
    "porcentaje": (12, "right", FORMATO_PORCENTAJE, False),
    "entero": (12, "right", FORMATO_ENTERO, False),
    "nota": (80, "left", None, True),
}

_borde = Side(style="thin", color=GRIS_BORDE)
BORDES = Border(left=_borde, right=_borde, top=_borde, bottom=_borde)
_ancho_ref = {}


def preparar_hoja(ws, titulo, subtitulo, color_pestana=None):
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 100
    ws.column_dimensions["A"].width = 2
    ws.row_dimensions[1].height = 8
    ws["B2"] = titulo
    ws["B2"].font = Font(name=FUENTE, size=16, bold=True, color=AZUL_MARINO)
    ws.row_dimensions[2].height = 26
    ws["B3"] = subtitulo
    ws["B3"].font = Font(name=FUENTE, size=10, italic=True, color=GRIS_TEXTO)
    if color_pestana:
        ws.sheet_properties.tabColor = color_pestana
    _ancho_ref[ws.title] = {}


def seccion(ws, fila, texto):
    c = ws.cell(row=fila, column=2, value=texto)
    c.font = Font(name=FUENTE, size=12, bold=True, color=AZUL_MARINO)
    ws.row_dimensions[fila].height = 22
    return fila + 1


def _lineas(texto, ancho):
    if not isinstance(texto, str) or texto.startswith("="):
        return 1
    return max(1, -(-len(texto) // max(int(ancho * 1.05), 1)))


def tabla(ws, fila, columnas, datos, entradas=()):
    """columnas: [(encabezado, tipo)]; datos: lista de filas; entradas: posiciones base 1 editables.
    Devuelve (fila_inicio_datos, fila_fin_datos, fila_siguiente)."""
    anchos = _ancho_ref.setdefault(ws.title, {})
    for j, (enc, tipo) in enumerate(columnas, start=2):
        ancho = TIPOS[tipo][0]
        letra = get_column_letter(j)
        anchos[letra] = max(anchos.get(letra, 0), ancho)
        c = ws.cell(row=fila, column=j, value=enc)
        c.font = Font(name=FUENTE, size=11, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=AZUL_MARINO)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDES
    ws.row_dimensions[fila].height = 30
    inicio = fila + 1
    for i, reg in enumerate(datos):
        r = inicio + i
        lineas = 1
        for k, (enc, tipo) in enumerate(columnas):
            ancho, horiz, formato, ajustar = TIPOS[tipo]
            valor = reg[k]
            if isinstance(valor, str) and "{r}" in valor:
                valor = valor.replace("{r}", str(r))
            c = ws.cell(row=r, column=k + 2, value=valor)
            es_entrada = (k + 1) in entradas
            es_nota = tipo == "nota"
            c.font = Font(name=FUENTE, size=10 if es_nota else 11, italic=es_nota,
                          color=GRIS_TEXTO if es_nota else ("0000FF" if es_entrada else "000000"))
            if es_entrada:
                c.fill = PatternFill("solid", fgColor=DURAZNO)
            c.alignment = Alignment(horizontal=horiz, vertical="center", wrap_text=ajustar, indent=1 if horiz in ("right", "left") else 0)
            c.border = BORDES
            if formato:
                c.number_format = formato
            if ajustar:
                lineas = max(lineas, _lineas(valor, anchos[get_column_letter(k + 2)]))
        ws.row_dimensions[r].height = max(20, 15 * lineas + 3)
    fin = inicio + len(datos) - 1
    return inicio, fin, fin + 2  # una fila en blanco; el total va inmediatamente tras los datos


def total(ws, fila, inicio, fin, etiqueta, sumar, col_etiqueta=3):
    """Fila de total pegada a los datos (se ubica en fin + 1; `fila` se conserva por compatibilidad).
    sumar: posiciones base 1 de las columnas a sumar. Devuelve la fila de inicio del siguiente bloque."""
    fila = fin + 1
    ultima_col = max(pos + 1 for pos in sumar) if sumar else col_etiqueta
    for j in range(2, ultima_col + 1):
        c = ws.cell(row=fila, column=j)
        c.fill = PatternFill("solid", fgColor=AZUL_CLARO)
        c.font = Font(name=FUENTE, size=11, bold=True, color="000000")
        c.border = Border(left=_borde, right=_borde, bottom=_borde,
                          top=Side(style="medium", color=AZUL_MARINO))
    et = ws.cell(row=fila, column=col_etiqueta, value=etiqueta)
    et.alignment = Alignment(horizontal="left", vertical="center")
    for pos in sumar:
        col = pos + 1
        letra = get_column_letter(col)
        c = ws.cell(row=fila, column=col, value=f"=SUM({letra}{inicio}:{letra}{fin})")
        c.number_format = FORMATO_SOLES
        c.alignment = Alignment(horizontal="right", vertical="center")
    ws.row_dimensions[fila].height = 24
    return fila + 2


def finalizar_hoja(ws, congelar=None):
    for letra, ancho in _ancho_ref.get(ws.title, {}).items():
        ws.column_dimensions[letra].width = ancho
    if congelar:
        ws.freeze_panes = congelar
    ws.sheet_view.zoomScale = 100
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
