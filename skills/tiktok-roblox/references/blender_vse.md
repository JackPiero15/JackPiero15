# Blender VSE: archivos del proyecto y uso de los helpers

## edit_decisions.json (fuente de verdad de los cortes)

```json
{
  "fps": 30,
  "sources": {"B": "C:\\...\\2026-10-25 19-33-37.mov", "C": "C:\\...\\2026-10-26 01-26-19.mov"},
  "transcripts": {"B": "<scratch>\\trans\\2026-10-25_19-33-37_t1.json", "C": "<scratch>\\trans\\2026-10-26_01-26-19_t1.json"},
  "wavs16k": {"B": "2026-10-25_19-33-37_t1.wav", "C": "2026-10-26_01-26-19_t1.wav"},
  "framing": {"crop_x": [705, 1215], "crop_y": {"C": 40}, "scales": [1.5, 1.65]},
  "scenes": {
    "M2_foca_916": [["B", 628.8, 634.4], ["B", 638.0, 667.3]],
    "M4_feminismo_916": [["B", 1124.9, 1130.4], ["B", 1136.25, 1142.85]]
  }
}
```
- Cada corte es `[fuente, inicio_s, fin_s]` en segundos de la grabación original. Pon los bordes ~0.1-0.15 s fuera de la primera y la última palabra (usa `words.py`).
- Una escena por TikTok o momento; nómbrala `M<n>_<tema>_916`.
- Si cambias los cortes de una escena, regenera **solo esa escena**: `bake_clips.py … <escena>`, `SCENES=<escena> level_audio.py …`, `captions.py` + `caption_chunks.py`. Luego reconstrúyela en Blender y vuelve a poner sus memes y efectos, desplazando sus tiempos lo que haya cambiado el inicio.
- Si Blender tiene abiertos los archivos que vas a regenerar, escribe en una carpeta o nombre nuevo (`clips_m4_v2/`, `…_voz_nivelada_v2.wav`) en lugar de sobrescribirlos.

## Cargar los helpers en Blender

```python
exec(open(r"<skill>\scripts\blender_vse_helpers.py", encoding="utf-8").read(), globals())
```
Ejecuta esto en cada llamada a `execute_blender_code` que use los helpers: cada llamada empieza con un espacio de nombres limpio. El tool exige que `result` sea un **dict**.

Ejemplos (devuelve siempre algo verificable):
```python
result = build_scene("M2_foca_916", ED + r"\clips\clips_manifest.json", ED + r"\audio\M2_foca_916_voz_nivelada.wav")
# -> {"video_frames": 1047, "stem_frames": 1047}   iguales = sin desfase

result = add_captions("M2_foca_916", ED + r"\captions.json")          # {"expected": 28, "placed": 28}
result = {"m": add_image("M2_foca_916", ED + r"\memes\m2_foca.jpg", 1.80, 3.45)}
result = {"z": add_zoom("M2_foca_916", 27.55, 27.70, 28.50, 1.2),
          "s": add_sfx("M2_foca_916", SFX + r"\bark-fart.mp3", 27.60, 0.84)}
result = add_image("M2_foca_916", IMG + r"\cara.jpg", 34.45, 36.40, "full")   # cierre a pantalla completa
bpy.data.scenes["M2_foca_916"].frame_end = F(36.40) - 1                 # alarga la escena hasta el cierre
result = build_final("TIKTOK_final", ["M2_foca_916", "M4_feminismo_916", "M5_senpai_916"],
                     intro={"dur": 3.5, "title1": "MOMENTOS INCÓMODOS", "title2": "DE PODCAST ROBLOX",
                            "song": SONG, "song_vol": 0.72,
                            "shots": [(ED + r"\clips\M2_foca_916_s02.mp4", 500), (..., 120), (..., 120)]})
result = set_export("TIKTOK_final", ED + r"\export\<nombre>.mp4"); save_version(ED + r"\tiktok_v10_export.blend")
```
Para revisar: `show_scene(nombre, frame, play=True)`. Para capturas grandes, usa `fullscreen_preview(True)`, luego `get_screenshot_of_area_as_image("SEQUENCE_EDITOR")`, y después `fullscreen_preview(False)`. Si la captura no cambia al mover el cursor, fuerza el redibujado (`bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)`; `show_scene` ya lo hace).

## Escenas útiles para el usuario
- `01_seleccion`: grabaciones completas con marcadores y franjas de color en los momentos candidatos.
- `01b_momentos`: candidatos seguidos con rótulo, para elegir.
- `REVISION_todos`: escenas finales seguidas con tarjetas de 1 s («M2 · La foca»), solo para revisar y anotar tiempos.
- `TIKTOK_final`: intro + escenas sin tarjetas. Es la que se exporta.
Si una escena cambia de duración, ejecuta `refresh_final()` o reconstruye las escenas de revisión y la final.

## Render y comprobación (fuera de Blender)
```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background "<v.blend>" --scene TIKTOK_final --render-anim *> "<scratch>\render_log.txt"
python -I limit_audio.py "<export>\<nombre>.mp4" "<export>\<nombre>_FINAL.mp4"
python -I verify_export.py "<export>\<nombre>_FINAL.mp4" "<scratch>\sheet.jpg" 1.6 15 48 60 117 --probe 117.2:118.2
```
Unos 2 min para 2 min de video en un i5 de 13.ª generación. Lánzalo en segundo plano y no lo hagas mientras el usuario reproduce en Blender. Antes de entregar el archivo, mira la hoja de fotogramas.
