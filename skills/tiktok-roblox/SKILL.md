---
name: tiktok-roblox
description: Convierte grabaciones de OBS de Roblox con chat de voz (podcasts, "match", karaoke, roleplay en escenario) en TikToks verticales 9:16 de humor, editados en Blender (VSE) por MCP y paso a paso con aprobación del usuario. Elige momentos incómodos o graciosos con Whisper, monta cortes, nivela voces a -14 LUFS, pone subtítulos blancos sincronizados, memes y efectos de sonido, intro con título y canción, exporta un MP4 de máxima calidad y lo sube a TikTok Studio. Úsala siempre que el usuario quiera editar clips o grabaciones de Roblox, hacer TikToks, Shorts o Reels de momentos graciosos o "momentos incómodos", un "podcast de Roblox", añadir memes o sonidos a un video, unir varios clips con intro, o subir un video a TikTok, aunque no mencione Blender ni esta skill.
---

# TikTok Roblox: momentos incómodos en Blender

Flujo probado de principio a fin: 3 grabaciones de OBS (1080p60, 25 min) → un TikTok de 1:59 con intro, 3 momentos, subtítulos, memes y sonidos, publicado en TikTok. Todo lo de abajo sale de esa sesión, incluidos los errores que costaron tiempo.

## Cómo trabajar con el usuario

El usuario quiere **ver y aprobar** cada decisión. Trabaja por etapas y detente al final de cada una con «Etapa lista para revisión». El silencio no es aprobación; si pide cambios, aplícalos y vuelve a mostrar esa misma etapa.

- Antes de cada etapa, explica en 2-3 líneas qué vas a hacer.
- Muestra el resultado **en Blender**: coloca el cursor, reproduce el fragmento (`screen.animation_play`) y compruébalo con capturas de la previsualización. No sustituyas la revisión del usuario por texto.
- Guarda una versión nueva del `.blend` en cada paso (`tiktok_v01_…`, `v02`…). Nunca sobrescribas la anterior.
- **No renderices hasta la exportación final** (ni fotogramas sueltos). En PCs con HDD, Blender se cuelga o se cierra al renderizar mientras edita; revisa con capturas de ventana.
- No puedes oír el audio: dilo cuando importe y pide al usuario que confirme volúmenes y palabras dudosas de la transcripción.
- Publicar en TikTok es una acción pública: confirma descripción, hashtags y portada antes de pulsar «Publicar».

## Requisitos (preflight)

- Blender 5.x con la extensión MCP (puerto 9876). Si no conecta: Preferencias → Sistema → Red → «Permitir acceso en línea», y en Complementos → MCP → «Start MCP Bridge Server» con «Auto Start». Si Blender se cerró y se reabrió desde un autosave, el servidor no arranca solo.
- Python con `faster-whisper`, `av` (PyAV, trae libavfilter: no hace falta `ffmpeg.exe`), `numpy`, `Pillow`.
- Los scripts están en `scripts/` de esta skill. Ejecútalos con `python -I <script>`; cada uno explica sus argumentos en su docstring.

Estructura del proyecto (crea `edicion/` junto a los videos):
```
edicion/
  edit_decisions.json   # cortes por escena (fuente)
  captions_raw.json / captions.json / caption_fixes.json
  audio/   <escena>_voz_nivelada.wav
  clips/   <escena>_sNN.mp4  + clips_manifest.json
  memes/   imágenes que pase el usuario (cópialas aquí)
  export/  MP4 final
  tiktok_vNN_*.blend
```

## Etapa 1 — Selección de momentos

1. Extrae audio de cada pista: `extract_audio.py <carpeta_videos> <scratch>/audio` (mide qué pista trae la mezcla; en OBS suelen ser idénticas).
2. Transcribe en español con marcas por palabra: `transcribe.py <scratch>/trans <wav>...` (modelo `small`, CPU int8; ~6 min por 20 min de audio, en segundo plano).
3. Localiza picos de energía (risas, gritos) y lee la transcripción completa buscando: humor negro, rechazos absurdos, egos inflados, frases que se contradicen, silencios incómodos, remates.
4. Comprueba visualmente cada candidato con `contact_sheet.py` (quién está en escena). Whisper confunde palabras («miedo no noventa» era «mido uno noventa»): verifica las frases clave.
5. Marca hasta 5 momentos en una escena `01_seleccion` (marcadores + franjas COLOR silenciadas con el nombre). Si el usuario quiere verlos, haz una escena `01b_momentos` con los intervalos seguidos y un rótulo. Avisa del contenido sexual explícito (TikTok puede restringirlo).

## Etapa 2 — Montaje (cortes, 9:16, audio)

1. Escribe `edit_decisions.json` (ver `references/blender_vse.md`). 20-35 s por momento sin forzarlo; conserva los silencios que dan risa; corta en límites de palabra con `words.py`.
2. **Clips ligeros** (lo que hace que el PC aguante): `bake_clips.py edit_decisions.json edicion/clips [escena…]` compone cada corte ya en 9:16 (fondo desenfocado + recorte centrado sin chat + zoom alterno 1.50/1.65 que disimula el salto) a 30 fps, CRF 14, con 0.5 s de margen a cada lado.
3. **Voz nivelada**: `level_audio.py edit_decisions.json edicion/audio` (iguala frase a frase ±10 dB, dynaudnorm suave, loudnorm -14 LUFS, limitador -1.5 dB). Opciones por entorno: `SCENES=a,b` para regenerar solo algunas, `DYN=` para el filtro.
4. En Blender, ejecuta `scripts/blender_vse_helpers.py` (ver referencia) y llama a `build_scene()` por escena: clips en canal 2, voz en canal 1. Comprueba que fotogramas de video == fotogramas de voz.
5. Revisa el encuadre con la previsualización a pantalla completa (`screen.screen_full_area`) y ajústalo si el personaje no queda centrado (lee la posición real en una captura; el escenario suele estar en x≈960-990 de la fuente y el chat empieza en x≈1210).

## Etapa 3 — Subtítulos

1. `captions.py edit_decisions.json <scratch>/audio edicion/captions_raw.json` (frases en tiempo de escena + tono para separar hablantes).
2. Corrige palabras mal transcritas y censura groserías fuertes en `caption_fixes.json`, luego `caption_chunks.py captions_raw.json captions.json --fixes caption_fixes.json` (bloques de 1-4 palabras, sin palabras sueltas).
3. `add_captions()` en Blender: Segoe UI Black 82 px, **blanco** (el usuario prefirió blanco a colores por hablante), contorno negro 0.12, sombra, en y=0.30. Lista al usuario las palabras dudosas.

## Etapa 4 — Memes y sonidos

Lee `references/memes_y_sonidos.md` antes de colocar nada. En resumen: 4-6 intervenciones por cada 35 s, cada imagen en el diálogo exacto que la motiva, sonidos en los silencios a ~-16 LUFS, música bajo la voz a ~-32 LUFS, cierre a pantalla completa. El usuario suele mandar imágenes nuevas pensadas para frases concretas: cópialas a `edicion/memes/` y ponlas exactamente donde dice. Acepta cambios y quita lo que no le gusta sin discutir (le sobraron las risas de rana, «muehehe» y «mwah»).

## Etapa 5 — Video final, exportación y publicación

1. Escena `TIKTOK_final` con `build_final()`: intro de ~3.5 s (montaje oscurecido de los clips + título en dos textos que no se solapen + canción a ~-15 LUFS con fundido) y las escenas como SceneStrip seguidas, **sin tarjetas negras** entre ellas.
2. `set_export()` y render en un proceso aparte (no congela la UI):
   `blender --background <v.blend> --scene TIKTOK_final --render-anim *> log.txt`. Si se cae con EXCEPTION_ACCESS_VIOLATION al escribir el MP4, relánzalo: fue aleatorio.
3. `limit_audio.py in.mp4 FINAL.mp4` (copia el video, limita picos del audio a -1.5 dB) y `verify_export.py FINAL.mp4 sheet.jpg <segundos…>`: comprueba 1080×1920, 30 fps, -14 LUFS ±1, pico ≤ -1 dB, inicio de audio y video en 0, y mira la hoja de fotogramas (intro, memes, cierres).
4. Publicación: sigue `references/tiktok_upload.md` (el usuario elige el archivo; tú escribes la descripción, eliges portada de la intro y publicas tras su confirmación).

## Recursos de la skill

- `references/blender_vse.md`: formato de `edit_decisions.json`, uso de cada helper de Blender, comandos de render y verificación. Léelo antes de la Etapa 2.
- `references/memes_y_sonidos.md`: dónde y cómo poner imágenes, zooms, sonidos y subtítulos, con volúmenes. Léelo antes de la Etapa 4.
- `references/tiktok_upload.md`: subida paso a paso a TikTok Studio con el navegador integrado. Léelo antes de publicar.
- `scripts/`: `extract_audio`, `transcribe`, `contact_sheet`, `words`, `level_audio`, `bake_clips`, `captions`, `caption_chunks`, `sfx_measure`, `limit_audio`, `verify_export`, `loudness` (módulo común) y `blender_vse_helpers` (se carga dentro de Blender).

## Errores ya resueltos (no los repitas)

| Problema | Causa | Solución |
| :--- | :--- | :--- |
| El secuenciador no muestra nada | Blender 5 usa `workspace.sequencer_scene` | Asigna la escena ahí y a `window.scene` |
| Video a media velocidad en escena de 30 fps | Tira de 60 fps creada por código | Usa clips a la misma fps o el operador con `adjust_playback_rate=True` |
| Blender se cierra al previsualizar o renderizar | Precarga + recorte/desenfoque en vivo + HDD | Clips ligeros, `sequence_editor.use_prefetch=False`, sin efectos en vivo |
| `enum "FFMPEG" not found` | Blender 5 separa imagen y video | `image_settings.media_type='VIDEO'` antes de `file_format='FFMPEG'` |
| `Action has no attribute fcurves` | Acciones por capas en Blender 5 | `strip.keyframe_delete(prop, frame=…)` |
| faster-whisper falla en `av.open(metadata_errors)` | PyAV 19 | Pásale el audio como array numpy |
| Un subtítulo desaparece | Choque al crear tiras | Cuenta tiras de texto vs `captions.json` y repón las que falten |
| El arrastre o clic no funciona en TikTok | Viewport emulado reescalado | Arrastra en tamaño normal; para «Guardar» amplía a 1440×900 y pulsa por `ref` |
| La descripción pierde la primera frase | Autocompletado de hashtags | Escribe hashtags, luego `ctrl+Home` y la frase; verifica el texto del editor |
