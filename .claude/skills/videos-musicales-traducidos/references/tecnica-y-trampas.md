# Técnica, audio, render y trampas conocidas

## Entorno típico (Windows) y comprobaciones previas
- Blender 5.x con el add-on MCP: `execute_blender_code` debe devolver un dict en `result` (no un int).
- ffmpeg completo (con loudnorm/ebur128). `ffprobe` puede no existir: usa `ffmpeg -i` y parsea stderr. Define `FFMPEG` si no está en el PATH.
- Python con numpy, av (PyAV), pillow, faster-whisper (modelos medium/small en la caché de HF). Sin scipy/torch está bien.
- Remotion solo si ya está instalado: instalar paquetes npm necesita autorización del usuario. Sin él, los subtítulos PNG en Blender cubren lo mismo.
- No instales ni actualices nada sin permiso. Si falta algo esencial, di exactamente qué.

## Fuentes e intermedios
- Copia las fuentes a `media/` del proyecto (rutas relativas en el .blend). Originales intactos.
- Intermedios solo cuando aportan (una generación, CRF 12, `-preset slow`, etiquetas bt709): AV1 4K → recorte 9:16 desde 4K y 1080p para 16:9; 59,94 fps → `fps=30000/1001` (descarta fotogramas, no interpola). Los VSE de Blender reproducen los strips a los fps de la escena: si no coinciden, la velocidad cambia → iguala fps con un intermedio, no con la escena.
- Blender: vista **Standard**, look None, todo en sRGB (strip, secuenciador, display) → transformación identidad (comprobado: ~1/255 de diferencia con la fuente).

## Subtítulos
- `make_subs.py` renderiza PNG transparentes a tamaño de lienzo con PIL: Inter variable (`Inter.woff2` que trae Blender en `datafiles/fonts`, licencia OFL; cópiala a `fonts/`) en SemiBold, blanco cálido, contorno oscuro 3 px al 85 %, sombra difusa. Elegido sobre TEXT strips porque estos no permiten peso SemiBold de la fuente variable ni colorear una palabra.
- Ajuste automático de tamaño (de `size` a `min_size`) para que la línea más ancha quepa en `max_w`; avisa si se sale de la zona segura o pasa de 20 c/s.
- Degradado localizado (banda inferior) constante; los subtítulos `top` llevan su propio degradado.
- En Blender: entrada de 3 fotogramas (alpha 0→1 + subida de 10 px, EXPO ease-out), salida de 2 (EXPO ease-in). Nada de rebotes. Es la parte de la skill blender-motion-graphics que encaja con un videoclip; el resto de sus reglas (Ken Burns, SFX, movimiento constante) no se aplica a subtítulos de canciones.

## Construcción en Blender (MCP)
```python
g = {"__file__": r"<skill>\scripts\build_blend.py", "PROJECT": r"<proyecto>", "BLEND_PREFIX": "musica"}
exec(open(g["__file__"], encoding="utf-8").read(), g)
g["build"]("cancion", "vertical"); g["build"]("cancion", "horizontal")
g["save_version"]()          # <prefix>_vNN.blend con rutas relativas
```
- Una llamada MCP con 8 escenas largas puede superar el tiempo de espera: construye en tandas de 2–4. Si una llamada expira, consulta el estado antes de repetir (Blender suele haber terminado).
- Blender 5: `sed.strips`; `image_settings.media_type = "VIDEO"` **antes** de `file_format = "FFMPEG"`; las acciones tienen capas (`action.layers[].strips[].channelbags[].fcurves`); `s.get("t0", s["k"][0]…)` evalúa el valor por defecto aunque exista la clave (usa un `if`).
- Canales: 1 canción (único audio), 2 metraje, 4 degradado/placa, 5 subtítulos. Marcadores por plano y por sección.

## Render y audio
- `render_all.py <blend> cancion:vertical cancion:horizontal …` → Blender en segundo plano (`-b -S escena -a`), solo video H.264 CRF 17 (`PERC_LOSSLESS`), y luego `mux.py`.
- Render de comprobación sin tocar el Blender del usuario: `qa_stills.py` lanza otro Blender en segundo plano que guarda PNG sueltos y monta una hoja (muy rápido; útil en PCs flojos que se colgaban renderizando desde la interfaz).
- `mux.py`: mide I/TP/LRA del tramo exacto con sus fundidos (`loudnorm print_format=json`), aplica **solo ganancia** `min(-14 - I, -1.3 - TP)`, codifica AAC LC estéreo 48 kHz 256 kb/s una vez, copia el video, `+faststart`, y vuelve a medir el MP4. Los masters comerciales suelen llegar a −6/−10 LUFS con TP > 0: bajar a −14 deja margen sin limitador.
- Tiempos cuantizados al fotograma (`round(t*fps)/fps`) iguales en Blender y en ffmpeg para que audio y video coincidan.

## Control final (`final_qa.py`)
- Propiedades (resolución, fps, yuv420p bt709, AAC 48k), `blackdetect`, y una hoja con un fotograma 0,25 s después de cada cambio de subtítulo extraído **del MP4 entregable**.
- Cada aviso de negro se mira: negro del original (tapar), recorte sobre ropa oscura (mover cx), fundido final (conservar). Repite hasta que solo queden los intencionados.

## Trampas que costaron tiempo
- `python -I` ignora `PYTHONIOENCODING`: whisper devuelve emojis en instrumentales y rompe `print` en cp1252 → `sys.stdout.reconfigure(encoding="utf-8")` dentro del script (ya incluido).
- `-I` tampoco añade la carpeta del script a `sys.path`: los scripts de la skill no importan módulos hermanos a propósito.
- PowerShell `Get-Content/Set-Content` sin `-Encoding` destroza tildes en UTF-8; usa `[IO.File]::ReadAllText/WriteAllText` o Python.
- La pantalla de bienvenida de Blender tapa el preview en capturas; las capturas de área por MCP no siempre refrescan tras `frame_set`. Para revisar fotogramas, `qa_stills.py`.
- Hojas de contacto mostradas reducidas: corrige la escala antes de medir posiciones.
