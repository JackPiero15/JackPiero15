---
name: plantillas-edicion-letras
description: Plantilla de los edits de letra traducida al español para TikTok 9:16 hechos entre el 29 y el 31 de octubre de 2026 (Confident v3, Too Much, Justin, Laroi, Down For Real, Dinero), lista para reutilizar con Python + ffmpeg, sin Blender - letra tecleada palabra a palabra con destellos blanco/negro y fotos de fondo en escala de grises, con tinte o a color. Úsala siempre que el usuario pida un edit "como el de Dinero / Down For Real / Too Much / Confident v3", un edit de canción con la letra en español apareciendo palabra por palabra, letra tecleada, destellos blanco y negro, fotos de Pinterest de fondo, o reutilizar las plantillas de edición de estos días, aunque no diga el nombre de la skill.
---

# Plantilla de edición: letra tecleada (TikTok 9:16)

Salida: MP4 1080x1920, 30 fps, H.264 CRF 16 (CRF 10 en la versión HQ), audio AAC 320k 48 kHz, ~60 s.

Renderizador: `scripts/render_letras.py`. Edits de referencia en `ejemplos/piezas/`.

Variantes (parámetros de imagen comprobados en los JSON):

| Edit | Fondo de las fotos | Parámetros |
|---|---|---|
| Confident v3 / Justin | B/N alto contraste (filtro `xerox`), algunas giran | `k: 7`, `dim: 0.5`, `spin`, `fy`; `font_size: 88` |
| Too Much / Laroi | B/N alto contraste con tinte azul/cian/violeta | `k: 5.0`, `dim: 0.46`, `tint: [40,110,210]`/`[60,170,200]`/`[120,70,200]` |
| Down For Real | Tinte violeta/rosa/azul, contraste suave | `k: 3.6`, `dim: 0.5`, `tint: [125,70,205]`/`[205,90,175]`/`[70,95,210]` |
| Dinero | Foto a color desaturada 15 %, cálida | `"rgb": true` en la pieza; `color: true`, `dim: 0.55` |

## Flujo

1. Crear proyecto: `bash scripts/nuevo_proyecto.sh <carpeta>` → `tools/` (scripts), `fonts/` (Roboto Condensed variable), `media/`, `pieces/`, `work/`, `out/`, `lineas.json`. Todos los comandos siguientes se ejecutan desde `<carpeta>`.
2. Audio: dejar la canción en `media/`. Transcribir con tiempos por palabra: `python tools/transcribe.py media/cancion.wav work/tr.json medium` (faster-whisper, idioma `en`). Formato: `{"segments":[{"words":[{"w","s","e","p"}]}]}`.
3. Imágenes: `python tools/pin_fetch.py media/pins <id_pin> ...` o `python tools/board_fetch.py media/rel <limite> <url_tablero> ...`; luego `python tools/make_sheet.py media/rel` → `work/sheet_index.txt` + `work/sheet_XX.jpg` numeradas. Revisar la hoja y excluir imágenes que no encajen (en Dinero se excluyeron fotos de ropa).
4. Tabla de líneas en `lineas.json` (plantilla en `assets/plantilla_lineas.json`). Una entrada por verso: `t0`/`t1` en segundos de la fuente, `en` (original), `es` (traducción fiel, español latino), `mode` (`flash` o `hold`), `img` (idx de la hoja, solo `hold`), `tint` opcional `[r,g,b]`. `in`/`out` = ventana del fragmento en la fuente.
5. Construir: `python tools/build_timeline.py lineas.json` → `pieces/<id>.json` y `pieces/<id>_table.json`.
6. Revisar fotogramas: `python tools/render_letras.py pieces/<id>.json out/qa.jpg 0.5 5.2 13.0 ...` (un JPG por tiempo).
7. Render: `python tools/render_letras.py pieces/<id>.json out/video.mp4` (`CRF=10` en el entorno para la versión HQ).
8. Audio: `bash tools/mux_audio.sh out/video.mp4 media/cancion.wav <ganancia_dB> out/final.mp4 [inicio_audio_s]`. Ganancias usadas: -5.1 dB (Justin, Laroi), -4.6 dB (Down For Real). `inicio_audio_s` = `in` cuando el audio es la canción completa.

## Reglas del constructor (`build_timeline.py`)

Lógica idéntica a los builders de Dinero y Down For Real; la salida se comprobó igual a la de ambos en 10 casos de prueba.

- Golpes de voz = inicios de palabra de Whisper dentro de `[t0-0.06, t1)`, fusionando los separados menos de 0.16 s (`min_word_gap`).
- Si hay más palabras en español que golpes: se agrupan las palabras contiguas más cortas. Si hay más golpes que palabras: se parte la palabra más larga al 55 % con `_` o `-` alternados (efecto tecleo); no se parten añadidos de menos de 5 caracteres.
- `reset_questions`: tras `"? "` el texto en pantalla se reinicia (preguntas repetidas).
- `flash`: el fondo alterna blanco/negro en cada golpe separado ≥0.28 s del cambio anterior (`min_flash_swap`) y siempre al empezar la línea; si no alterna, solo cambia el texto.
- `hold`: imagen fija con acercamiento lento (1.2 %/s) y deriva; transición con desenfoque horizontal solo en el primer golpe de la línea.
- El primer evento se fuerza a `t = 0`.

## Esquema de la pieza (`render_letras.py`)

- Raíz: `id`, `duration`, `font`, `font_size`, `font_weight`, `text_y` (centro vertical del texto, 960), `max_text_w` (860), `fade_out`, `rgb` (true = fotos a color), `images`, `events`.
- `images[i]`: `file`; `crop` `[x0,y0,x1,y1]` en fracciones; `fx`/`fy` (encuadre 0–1); `spin` (grados/s); `xerox` (default true); `k`/`mid` (contraste xerox); `color` (sin xerox, requiere `rgb`); `grade` `[r,g,b]` (solo color, default `[1.06,1.0,0.9]`); `invert`; `dim` (brillo); `tint` `[r,g,b]` (colorea los medios tonos).
- `events[j]`: `t`, `text` (texto visible), `line` (verso completo: fija la posición para que el texto parcial no salte), `mode`, `bg` (`w`/`b`, solo flash), `img`, `img_t0` (solo hold), `swap` (transición con desenfoque).
- Rutas relativas a la carpeta padre de `tools/` (raíz del proyecto).

## Controles de calidad

- Traducción fiel al sentido, español latino natural; marcar en `en` las líneas donde Whisper y la letra oficial difieren (en Too Much se anotó la confianza por línea).
- Revisar fotogramas en: primer evento, cada cambio flash→hold, el verso más largo (no debe pasar de 3 líneas a 84 px) y los últimos 0.5 s (fundido).
- Verificar duración y streams: `ffprobe -v error -show_entries stream=codec_name,width,height:format=duration -of compact out/final.mp4`.
- Videos e imágenes de terceros: no subirlos a git (en el repo, `export/*.mp4` y `export/*.png` están ignorados).

## Archivos

- `scripts/`: `render_letras.py` (versión de Dinero: incluye todas las funciones de Confident v3 y Too Much), `build_timeline.py`, `make_sheet.py`, `transcribe.py`, `pin_fetch.py`, `board_fetch.py`, `mux_audio.sh`, `nuevo_proyecto.sh`.
- `assets/`: `plantilla_lineas.json`, `fonts/` (ver `assets/fonts/FUENTES.md`).
- `ejemplos/piezas/`: piezas finales y tablas en/es de los 6 edits.
- `ejemplos/builders_originales/`: scripts originales de cada edit (rutas `/home/user/...` y fuente `RobotoCondensed[wght].ttf` de la sesión original; solo referencia).
