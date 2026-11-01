---
name: blender-video-editor
description: Edit videos for YouTube and TikTok/Shorts/Reels in Blender's Video Sequence Editor (VSE) through the Blender MCP, with FFmpeg for audio cleanup, silence cuts, captions and verification. Story-first cuts, no jump cuts, B-roll, Netflix-style captions, titles/lower thirds, music ducking, -14 LUFS, color correction with strip modifiers, 16:9 and 9:16 renders. Use whenever the user wants to edit, cut, assemble, caption, clean audio or export a video, or brings a DaVinci/Premiere workflow to do in Blender.
---
# Blender Video Editor (VSE) + FFmpeg

Adapted from the Premiere Pro skill and the DaVinci Resolve skills (social editor, folder autocutter, cut screen recording, audio cleanup, color grade, titles, multi-platform export, troubleshooting). Resolve tool names -> Blender equivalents: `references/davinci-to-blender.md`. Quality gates: `references/editing-qa.md`.

Run Blender code with the Blender MCP `execute_blender_code` (return dicts). Run FFmpeg/Python helpers with PowerShell (Windows). Scripts live in this skill's `scripts/` folder.

## Core rule
Do not cut from transcript text alone. Story first, then prove it: frame checks, audio checks, a render you can watch. A technically valid cut with sentence fragments, jump cuts, speaker out of frame, wrong captions or music over voice is a failure.

## Profiles
| Target | Resolution | Length | Speed | Loudness |
| :--- | :--- | :--- | :--- | :--- |
| TikTok / Shorts / Reels | 1080×1920, 30 fps | up to 3 min | 1.0-1.1× for talking | -14 LUFS, TP < -1 dBTP |
| YouTube | 1920×1080 (or 3840×2160), match source fps | 3-12 min | 1.0× | -14 LUFS, TP < -1 dBTP |
Match scene fps to the source clips (read after import) or audio drifts.

## Workflow
1. **Preflight**: Blender MCP connected; `ffmpeg -version` works (if not, ask before installing: `winget install Gyan.FFmpeg`); media paths exist.
2. **Ingest/audit**: `python scripts/probe_media.py <folder> --out <work>/media_manifest.json`, then `python scripts/audio_quality_audit.py <folder> --out <work>/audio_quality_audit.json`. Reject silent/black sources; fix one-dead-channel stereo.
3. **Story plan** (`story_plan.md`): hook (first 3 s must promise something), body beats, recap/CTA. Short note of what is cut and why.
4. **Edit decisions** (`edit_decisions.json`): per segment source, in/out seconds, channel, reason, transition, crop/scale, caption text. Optional silence-cut list from FFmpeg `silencedetect` (padding 0.1-0.15 s).
5. **Build in Blender** (sections below): set scene, place strips from the decisions, punch-ins or B-roll on every seam, markers for each beat.
6. **Audio**: clean dialogue with the FFmpeg chain (EQ -> de-hum -> denoise -> compress -> loudnorm), import the clean stem on channel 1, mute the original audio strips, duck music.
7. **Titles & captions**: TEXT strips for hook/lower thirds; captions as TEXT strips or burned with `scripts/caption_burnin_pipeline.py` (`--size 1920x1080` for YouTube).
8. **Color**: strip modifiers (normalize -> balance -> enhance), same stack on matched clips.
9. **Render** MP4, then loudness pass if needed, then **verify**: `python scripts/verify_social_export.py out.mp4 --out-dir <work>/review --profile tiktok|youtube`. Look at the stills.
10. **Report**: output path, duration/resolution/fps, loudness, what was checked, known gaps. Save the .blend versioned (never overwrite the user's file).

## Blender rules
- API 5.x: `sed.strips` (old: `sed.sequences`). Detect with `hasattr(sed, "strips")`.
- `frame = round(sec * fps) + scene.frame_start`.
- Read strips before editing; names change after splits. Before big rebuilds: `bpy.ops.scene.new(type='FULL_COPY')` or save a copy.
- Channels: 1 dialogue clean, 2 A-roll, 3 B-roll, 4 graphics/titles, 5 captions, 6 music, 7 SFX, 8 original audio (muted reference).
- `scene.render.use_sequencer = True`, else the 3D scene renders (black/cube).

## Setup + place segments
```python
import bpy, os
scene = bpy.context.scene
W, H, FPS = 1080, 1920, 30          # YouTube: 1920,1080
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.render.use_sequencer = True
sed = scene.sequence_editor or scene.sequence_editor_create()
strips = sed.strips if hasattr(sed, "strips") else sed.sequences
f = lambda s: round(s * FPS)

segments = [  # from edit_decisions.json
    {"src": r"C:\ruta\clip1.mp4", "in": 3.2, "out": 11.8, "scale": 1.0},
    {"src": r"C:\ruta\clip1.mp4", "in": 14.0, "out": 22.5, "scale": 1.15},  # punch-in hides the seam
]
rec = scene.frame_start
placed = []
for i, s in enumerate(segments):
    mv = strips.new_movie(f"seg{i}", s["src"], channel=2, frame_start=rec - f(s["in"]))
    mv.frame_offset_start = f(s["in"]); mv.frame_offset_end = mv.frame_duration - f(s["out"])
    au = strips.new_sound(f"seg{i}_aud", s["src"], channel=8, frame_start=rec - f(s["in"]))
    au.frame_offset_start = f(s["in"]); au.frame_offset_end = au.frame_duration - f(s["out"])
    mv.transform.scale_x = mv.transform.scale_y = s["scale"]
    scene.timeline_markers.new(f"{i+1}", frame=rec)
    placed.append((mv.name, mv.frame_final_start, mv.frame_final_end))
    rec = mv.frame_final_end
scene.frame_end = rec - 1
result = {"placed": placed, "end": scene.frame_end}
```
Fit horizontal footage in vertical: scale so height fills (`scale = H / src_h * src_w/W` as needed) and set `transform.offset_x` to keep the face centered; keyframe offsets per segment instead of Smart Reframe.

## Titles, lower thirds, fades, music
```python
t = strips.new_effect("Hook", 'TEXT', channel=4, frame_start=scene.frame_start, length=f(2.5))
t.text = "Lo que nadie te dice de..."; t.font_size = 96; t.location = (0.5, 0.78)
t.use_shadow = True; t.use_box = True; t.box_color = (0, 0, 0, 0.55); t.wrap_width = 0.9
t.blend_alpha = 0; t.keyframe_insert("blend_alpha", frame=t.frame_final_start)
t.blend_alpha = 1; t.keyframe_insert("blend_alpha", frame=t.frame_final_start + 6)
m = strips.new_sound("music", r"C:\ruta\musica.mp3", channel=6, frame_start=scene.frame_start)
m.volume = 0.18   # under voice; raise only in gaps with keyframes
```
Lower third: COLOR strip (bar) + TEXT strip(s), slide in by keyframing `transform.offset_x` over ~12 frames, group in a Meta strip.

## Color (strip modifiers)
```python
mod = mv.modifiers.new("Balance", 'COLOR_BALANCE')
mod.color_balance.lift = (1.0, 1.0, 1.02); mod.color_balance.gamma = (1.03, 1.02, 1.0); mod.color_balance.gain = (1.05, 1.04, 1.02)
mv.color_saturation = 1.1    # keep under ~1.25 for skin
```
Copy the same modifier values to matching clips. Check a still before and after.

## Render
```python
r = scene.render
r.image_settings.file_format = 'FFMPEG'
r.ffmpeg.format = 'MPEG4'; r.ffmpeg.codec = 'H264'
r.ffmpeg.constant_rate_factor = 'HIGH'; r.ffmpeg.ffmpeg_preset = 'GOOD'
r.ffmpeg.audio_codec = 'AAC'; r.ffmpeg.audio_bitrate = 192; r.ffmpeg.audio_mixrate = 48000
r.filepath = r"C:\ruta\salida\video_tiktok.mp4"
bpy.ops.render.render(animation=True)   # blocks Blender; warn the user for long renders
```
Two platforms: duplicate the scene (`FULL_COPY`), change resolution/reframe, render each. Loudness fix without re-encoding video:
`ffmpeg -i in.mp4 -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k out.mp4`

## YouTube chapters
Markers -> description lines `0:00 Intro` (first must be 0:00, at least 3 chapters, each ≥ 10 s).

## Troubleshooting
| Problem | Cause | Fix |
| :--- | :--- | :--- |
| Audio drifts | scene fps ≠ clip fps | set `scene.render.fps` (and `fps_base`) to clip fps before placing |
| Black or cube render | sequencer off | `scene.render.use_sequencer = True` |
| `AttributeError: sequences` | Blender 5.x | use `sed.strips` |
| Choppy preview | heavy 4K H.264 | build proxies (strip `use_proxy`, 25-50%) or preview at lower res; final render uses originals |
| Clip offline (red) | file moved | update `strip.filepath` / `sound.filepath` |
| Split op fails | no sequencer context | use `temp_override` with a Sequencer area, or offsets instead of split |
| Render fails / 0 bytes | bad path or chars | plain filename, existing folder, enough disk space |
