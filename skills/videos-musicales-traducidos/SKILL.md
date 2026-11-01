---
name: videos-musicales-traducidos
description: Convierte canciones (videoclips, lyric videos o una canción + metraje de otro video) en videos con subtítulos traducidos al español latino, sincronizados con la voz, en Blender VSE con ffmpeg y faster-whisper - fragmento vertical 9:16 de ~1 minuto para TikTok, YouTube Shorts y estados de WhatsApp, y canción completa 16:9 para YouTube - con transcripción verificada, traducción fiel, reencuadre, tapado de letras incrustadas, -14 LUFS, SRT, tablas de alineación, letras en Markdown e informe. Úsala siempre que el usuario quiera traducir, subtitular o "poner la letra en español" a una canción o videoclip, hacer TikToks/Shorts/estados con canciones traducidas, edits de canciones con letra, lyric videos en español, o subtitular un videoclip para YouTube, aunque no mencione Blender, whisper ni esta skill. Also for translated-lyrics music edits in any language pair.
---

# Videos musicales traducidos (vertical + YouTube) en Blender

Pipeline probado en 4 canciones reales (videoclip propio, lyric video 4K con letra incrustada, videoclip 720p lleno de negros, y canción + visualizer de otra canción). Todo sale de un JSON por canción, así que cualquier cambio del usuario (una frase, un encuadre) se rehace en minutos.

## Qué manda y qué no
La canción es el centro. Del resto de skills de edición (blender-video-editor, blender-motion-graphics) se toma lo técnico (VSE, render, -14 LUFS, curvas EXPO), **no** sus recetas de vlog: nada de limpieza de diálogo, ducking, cortes de silencio, aceleración, SFX, whooshes, intros, logos, CTA, Ken Burns, movimiento constante ni zooms en cada corte. Subtítulos quietos y legibles valen más que animados. Si el usuario trae su propio encargo (un "prompt maestro"), ese encargo manda sobre esta skill.

Claude no puede escuchar. Todo lo que el informe llame "verificado" debe venir de pasadas independientes que coinciden, de la letra oficial incrustada o de fotogramas inspeccionados; lo demás se marca y se deja para que el usuario lo escuche. Nunca se declara revisado lo que no se comprobó.

## Estructura del proyecto
```
<proyecto>/
  pieces/<cancion>.json      tabla maestra + config de cada formato (plantilla: assets/piece_template.json)
  media/                     copias de fuentes + intermedios (originales intactos)
  fonts/Inter.woff2          (opcional; si falta se usa la de la skill)
  subs/<id>/{vertical,horizontal}/   PNG de subtítulos, timing.json, SRT
  subs/<id>/<id>_alineacion_maestra.csv/.json
  render/  vertical/  youtube/  export/  review/  letras/  work/
  <prefijo>_vNN.blend        una escena <CANCIÓN>_VERTICAL y otra <CANCIÓN>_YOUTUBE_16x9 por canción
```
Los scripts viven en `scripts/` de esta skill y trabajan sobre la carpeta del proyecto: define `$env:MT_PROJECT = "<proyecto>"` (y `FFMPEG` / `BLENDER` si no están en el PATH). En Windows ejecuta Python con `-I` cuando el script lea archivos descargados.

## Flujo
Lleva un plan visible y avanza por fases. Si el usuario quiere aprobar cada fase, para tras cada una; si dice "hazlos todos y reviso al final", sigue de corrido (pero sigue revisando tú cada paso).

### 1. Comprobar herramientas y fuentes
Blender por MCP (versión, escena), ffmpeg completo, Python (av, numpy, pillow, faster-whisper + modelos), espacio. No instales nada sin permiso. Inspecciona cada fuente con `ffmpeg -i` (resolución, fps, códec, duración, audio) y compáralo con lo que diga el usuario. Copia a `media/`. Extrae WAV: `ffmpeg -i fuente -vn -c:a pcm_s16le work/<c>_full.wav`.

### 2. Transcribir la canción COMPLETA y verificarla
Primero la canción entera (para YouTube); el vertical se deriva después. Lee `references/transcripcion-y-traduccion.md` antes de traducir. Resumen:
- `transcribe.py`, luego `recheck_lines.py` (dos modelos, voz realzada), `nbest.py` en cada línea dudosa, comparación entre repeticiones de coro y, si el video trae letra incrustada, `locate_text_color.py` + `read_burned_lyrics.py`.
- `silencedetect` para los límites musicales reales (`horizontal.in/out`), `beats.py` para tempo y rejilla.
- Cada subtítulo lleva `conf` ("alta", "media: motivo", "BAJA: hipótesis…"). Lo ininteligible no se inventa: se traduce solo lo seguro o se deja sin subtítulo, y se lista como pendiente.

### 3. Traducir y llenar la tabla maestra (`subs` en el JSON)
Español latino natural, mismo registro y groserías que el original, sin añadir reproches ni certezas. Bloques por sentido, 2 líneas máx., 12–17 c/s (revisa >20). Un color de acento por pieza en una palabra clave (`*palabra*`). Los coros repetidos reusan la traducción con su desfase medido. Anota en `letras/cambios_traduccion.md` cada corrección respecto a las adaptaciones que traiga el usuario.

### 4. Elegir el fragmento vertical
Bloque musical completo de 55–65 s que empiece con voz significativa y cierre en frase resuelta; bordes comprobados con `nbest.py` (sin trozos de la frase vecina). Si el bloque coherente es más corto, explícalo en vez de cortar una sección. Detalle en `references/montaje-y-encuadre.md`.

### 5. Planos y encuadre
Lee `references/montaje-y-encuadre.md`.
- **sync** (el video es el de la canción): cortes con `select='gt(scene,0.3)'`, negros con `luma_runs.py`, lista con `gen_sync_shots.py` (tapa negros con planos ambientales sin canto), `cx` por plano revisado en `crop_sheet.py`.
- **montage** (metraje ajeno, p. ej. visualizer): inventario de tomas limpias (`shot_sheet.py`, `luma_runs.py`), audio del metraje silenciado, `gen_montage.py` con secciones ancladas al pulso y retornos visuales en los coros (configuración real de ejemplo en `assets/montage_example.json`); nada de labios que finjan cantar mientras hay voz.
- **Texto incrustado**: placa opaca localizada (`plate`) que lleva el español; ni dos idiomas a la vez ni desenfoques grandes.
- 16:9: composición original sin bandas; subtítulo abajo al centro (márgenes 120/130 px).

### 6. Subtítulos y Blender
```
python scripts/make_subs.py pieces/<c>.json          # PNG + SRT + tabla maestra (ambos formatos)
```
Revisa los avisos (c/s, ancho, zona segura x 100–900 / y 260–1450 en vertical) y corrige el texto. Después, en Blender por MCP (en tandas para no superar el tiempo de espera):
```python
g = {"__file__": r"<skill>/scripts/build_blend.py", "PROJECT": r"<proyecto>", "BLEND_PREFIX": "musica"}
exec(open(g["__file__"], encoding="utf-8").read(), g)
g["build"]("<c>", "vertical"); g["build"]("<c>", "horizontal"); g["save_version"]()
```
Cada guardado es una versión nueva (`_vNN`), con rutas relativas. Detalles y trampas de Blender 5 en `references/tecnica-y-trampas.md`.

### 7. Revisar ANTES de renderizar
`qa_stills.py <c> <fmt> <blend> [cada_n]` renderiza en un Blender en segundo plano (no toca el del usuario, que puede ser un PC flojo) un fotograma por subtítulo y por plano, y monta una hoja. Míralas de verdad: caras cortadas, subtítulo sobre boca/ojos (pásalo arriba con `"pos": "top"` o cambia el plano), texto fuera de zona, inglés asomando bajo la placa, negros, destellos, planos repetidos. Corrige en el JSON, reconstruye, repite.

### 8. Render, audio y control final
```
python scripts/render_all.py <blend> <c>:vertical <c>:horizontal ...   # en segundo plano
python scripts/final_qa.py <c> <fmt>
python scripts/gen_letras.py <c> ...
python scripts/gen_report.py
```
`render_all` = Blender en segundo plano (H.264 CRF 17, BT.709, solo video) + `mux.py` (audio del original una sola vez, solo ganancia hacia -14 LUFS sin pasar de -1 dBTP, AAC 256k 48 kHz, faststart, nueva medición). `final_qa` = propiedades, `blackdetect` y una hoja de fotogramas del MP4 entregable en cada cambio de subtítulo. Investiga cada negro detectado (negro del original → tapar; recorte sobre ropa oscura → mover `cx`; fundido final → conservar y documentar). Re-renderiza solo lo afectado.

### 9. Entregables e informe
- `vertical/<id>_VERTICAL.mp4` y `youtube/<id>_YOUTUBE_COMPLETO_16x9.mp4`, cada uno con su `.srt` al lado (tiempos relativos a ese MP4). Una versión por formato, sin copias por plataforma.
- `.blend` + `media/` + `scripts`; tablas maestras; letras completas en Markdown; `letras/cambios_traduccion.md`.
- `INFORME.md`: fragmento elegido y por qué, duraciones, resolución/fps, mediciones reales (`export/tabla_mediciones.md`), decisiones por pieza, limitaciones (p. ej. 720p ampliado, placa que tapa una franja) y **lista de versos pendientes de escuchar**. No afirmes que el material está libre de derechos. No publiques ni envíes los videos a nadie.

## Scripts (en `scripts/`)
| Script | Para qué |
|---|---|
| `transcribe.py` | whisper con tiempos por palabra |
| `recheck_lines.py` | segunda pasada, voz realzada, dos modelos |
| `nbest.py` | 6 hipótesis por ventana corta |
| `beats.py` | tempo y rejilla de pulsos |
| `locate_text_color.py`, `read_burned_lyrics.py` | dónde está la letra incrustada y leerla rótulo a rótulo |
| `shot_sheet.py`, `luma_runs.py` | tomas de una fuente; tramos negros |
| `gen_sync_shots.py`, `gen_montage.py` | lista de planos (sync / montaje por secciones) |
| `crop_sheet.py` | revisar el recorte 9:16 de cada plano |
| `make_subs.py` | PNG de subtítulos, degradado/placa, SRT, tabla maestra |
| `build_blend.py` | escena de Blender por formato + versiones |
| `qa_stills.py` | fotogramas de control en segundo plano |
| `render_all.py`, `mux.py` | render + audio final medido |
| `final_qa.py`, `gen_letras.py`, `gen_report.py` | control del entregable, letras, tabla de mediciones |
