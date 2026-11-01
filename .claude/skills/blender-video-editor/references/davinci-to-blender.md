# DaVinci Resolve -> Blender VSE / FFmpeg map

Use this when a DaVinci tutorial, skill or user habit names a Resolve tool.

| DaVinci Resolve | Blender 5.x VSE / FFmpeg equivalent |
| :--- | :--- |
| Project / Media Pool / bins | .blend file; group strips with Meta strips; keep sources in a `Footage/` folder |
| Timeline (01:00:00:00 start) | Scene; starts at `scene.frame_start` (usually 1) — always offset placements from it |
| Video track V1/V2 / Audio A1/A2 | Channels; higher channel draws on top. Suggested: 1 dialogue, 2 A-roll, 3 B-roll, 4 graphics, 5 captions, 6 music, 7 SFX |
| Disable track / clip | `strip.mute = True` (also `sed.channels[n].mute` in 4.x+) |
| Markers | `scene.timeline_markers` |
| Razor / Blade | `bpy.ops.sequencer.split(...)` or two strips with `frame_offset_start/end` |
| Ripple delete | delete strip + `bpy.ops.sequencer.gap_remove(all=True)` |
| Text+ / Fusion titles | TEXT effect strip (font, size, shadow, box, outline); animate `location`, `blend_alpha` with keyframes |
| Lower third template | TEXT strip + COLOR strip in a Meta strip; reuse by appending from a template .blend |
| Smart Reframe (Studio) | Manual: strip `transform.offset_x/offset_y` + `scale_x/y` keyframes per segment |
| Color page primaries | Strip modifiers: `COLOR_BALANCE` (lift/gamma/gain), `CURVES`, `BRIGHT_CONTRAST`, `HUE_CORRECT`; or set `color_saturation` / `color_multiply` |
| Shot matching | Same modifier stack on matched strips; compare stills with `bpy.ops.render.opengl` or FFmpeg frame grabs |
| Clip EQ low-cut / De-Hummer | FFmpeg: `highpass=f=80`, `bandreject=f=60` (50 in Europe) or `anlmdn`/`afftdn` |
| Noise Reduction | FFmpeg `afftdn=nf=-25` (gentle) |
| Dialogue Leveler | FFmpeg `dynaudnorm` or `acompressor`, then `loudnorm` |
| Ducker | FFmpeg `sidechaincompress`, or Blender `volume` keyframes on the music strip |
| Deliver presets | Render settings: FFMPEG / MPEG4 / H264 / AAC; one scene per platform (full-copy scene for 9:16) |
| Loudness normalize on render | Render from Blender, then FFmpeg `loudnorm=I=-14:TP=-1.5:LRA=11` pass (copy video) |
| Create Subtitles from Audio (AI) | Whisper (if installed) -> SRT -> `scripts/caption_burnin_pipeline.py`, or import as TEXT strips |
| Remove Silent Portions | FFmpeg `silencedetect` -> cut list -> rebuild strips in Blender |

## FFmpeg audio cleanup chain (order matters: frequency first, dynamics last)
```
ffmpeg -i dialog.wav -af "highpass=f=80,bandreject=f=60:width_type=h:w=4,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=10:release=150,loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 dialog_clean.wav
```
Music ducked by voice:
```
ffmpeg -i dialog_clean.wav -i music.mp3 -filter_complex "[1:a]volume=0.35[m];[m][0:a]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[d];[0:a][d]amix=inputs=2:duration=first:normalize=0" mix.wav
```

## Silence-cut list
```
ffmpeg -i clip.mp4 -af silencedetect=noise=-35dB:d=0.5 -f null -
```
Parse `silence_start`/`silence_end`, keep 0.1-0.15 s padding on each side so words are not clipped, then rebuild the kept ranges as strips back-to-back.
