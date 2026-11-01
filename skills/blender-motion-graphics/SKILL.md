---
name: blender-motion-graphics
description: Create and edit professional motion graphics in Blender (3D scene + VSE + compositor) driven through the Blender MCP with bpy. Use this skill EVERY time the user wants to create or edit a video in Blender, animate text/logos, build an intro/outro/logo sting, make a Reel/Short/TikTok/promo, add animated titles or captions over footage, composite images and B-roll, or complains their Blender video looks basic, generic or amateur. Always read this skill BEFORE writing any bpy animation code.
---

# Blender Motion Graphics

Blender keyframes everything with Bezier F-curves, so code is not the bottleneck —
**motion design craft is**. Untrained generation produces LINEAR/default easing,
opacity-only fades, simultaneous entrances, flat world colors and no texture: the
"generic AI video" look. This skill prevents it.

Port of the Remotion motion-graphics skill: same design rules, Blender implementation.

## Non-negotiable rules (every scene)

1. **Never LINEAR interpolation.** Every keyframe gets `interpolation='EXPO'`/`'BACK'`/
   `'ELASTIC'` with an explicit `easing`, or BEZIER with tuned handles. Use the helpers
   in `assets/mograph.py` (`key_ease`, `entrance`, `exit_fast`) — never raw
   `keyframe_insert` without setting interpolation afterwards.
2. **Entrances animate 2–3 properties together** (alpha + location Z/Y + scale).
   A lone fade is forbidden.
3. **Stagger everything**: words, letters, cards, rays → 3–6 frame offsets.
4. **Exits exist and are faster than entrances** (~10 frames vs ~20), `EASE_IN`.
5. **Five-layer stack**, bottom→top: background (animated gradient/emission planes
   or World shader, never a flat solid) → assets (image planes / footage strips) →
   graphics/type → color grade (compositor) → grain + vignette (compositor).
6. **Every still gets Ken Burns** (scale 1→1.08 + slow pan) — 3D image plane or VSE
   strip transform. Alternate zoom-in / zoom-out between consecutive shots.
7. **Idle elements breathe**: anything on screen >2 s gets a Noise or sine driver
   micro-motion (`breathe()` helper).
8. **All timing derives from `scene.render.fps`** (`sec(s)` helper). No magic frames.
9. **One theme**: `assets/theme.py` (colors, easings, fonts, timings). Never inline a
   hex or easing in scene code.
10. **Verify by LOOKING**: screenshots / viewport stills at key frames, fix, repeat.
    Never deliver unverified. (On weak PCs: viewport screenshots only, full render
    only at the final export — ask the user.)

## Workflow

### Step 1 — Scope
Duration, fps (30 default), size (1080×1920 vertical, 1920×1080 landscape), assets
(images, footage, audio, logos, fonts), new scene vs edit. If editing: inspect the
scene first (`get_objects_summary`, sequences, compositor) — never assume, never
destroy without confirmation.

### Step 2 — Setup
Run `assets/mograph.py` once in Blender (via `execute_blender_code`, paste the file
content) — it defines `theme`, helpers, and `setup_scene()`. Call:
```python
setup_scene(w=1080, h=1920, fps=30, seconds=15, engine="EEVEE")
```
This sets resolution, fps, frame range, Filmic/AgX "Medium High Contrast" view,
an orthographic 2D camera framing the canvas, and the compositor stack
(grade + grain + vignette). Load display fonts with `load_font(path)`
(Montserrat/Inter/Clash Display .ttf from user or Google Fonts).

Two building modes — pick per scene:
- **3D/2D scene (motion graphics, titles, logos)**: text objects, planes with
  emission materials, rendered by EEVEE. Animate objects + material alpha.
- **VSE (footage edits)**: footage as MOVIE strips, overlays as the 3D scene strip
  (`SCENE` strip with transparent film) or TEXT strips; Ken Burns via strip
  `transform`. Compositor applies only when "Compositing" post-processing is on.

### Step 3 — Build
Read `references/motion-patterns.md` (helper usage: entrance, stagger, word reveal,
bg mesh, grade/grain/vignette, Ken Burns, counters, spark mark, exits, breathing,
parallax, transitions, motion blur, audio sync, captions). For pacing, palettes,
typography, sound, read `references/design-rules.md`.

Scene rhythm: HIT → hold (15–20 still frames) → build → HIT. Something moves in the
first 15 frames. Never >90 frames without a new visual element.

### Step 4 — Verify (mandatory, cheap)
For frames like 15, 45, 90, 150: `scene.frame_set(f)` then
`get_screenshot_of_area_as_image` (camera view, Rendered/Material preview) or
`render_viewport_to_path`. Look for, in order:
- Text overflowing or touching edges; 9:16 critical content inside middle 75 %.
- Elements visible before entrance / after exit (missing alpha keys at 0, or
  F-curve overshoot from BACK/ELASTIC going below 0 on alpha — clamp alpha with EXPO).
- Hero color on >1 element per frame; dim text unreadable after grade.
- Layer order / Z-fighting (keep ≥0.01 Z between stacked planes, or use
  `show_in_front` / blend mode).
- Graph Editor check: no LINEAR or CONSTANT left (`audit_linear()` helper).
Fix → re-check → only then final render.

### Step 5 — Final render (only when the user approves)
```python
final_render("//out/video.mp4", crf="HIGH")  # FFmpeg H.264, AAC 192k
```
For the user's weak PC prefer EEVEE, 16–32 samples, motion blur only if needed.
Verify the encode with `ffprobe` + extract 3 frames with
`ffmpeg -v error -ss 1.5 -i video.mp4 -frames:v 1 check.png`.

### Editing existing footage
Put the clip in the VSE (`add_footage(path)`), set frame range from the strip,
overlay a transparent motion-graphics scene as a SCENE strip above it, enable
Compositing for grade/grain. Captions: see §17 of motion-patterns.

## Reference files
- `assets/theme.py` — palette, easings, spring-like presets, fonts, timings.
- `assets/mograph.py` — helper library (includes theme). Paste/exec in Blender.
- `references/motion-patterns.md` — how to build each pattern with the helpers.
- `references/design-rules.md` — color, type, pacing, sound, pre-delivery checklist.

## Common failure modes
- Forgetting interpolation after `keyframe_insert` → Blender default BEZIER
  auto-clamped (soft, generic) or LINEAR if user prefs say so. Always set it.
- Animating `material alpha` without `blend_method`/EEVEE Next transparency →
  invisible fades. Use the `make_emission_mat()` helper (alpha via Mix Shader input).
- Text objects with default Bfont for hero text. Always load a display font.
- Emoji in text objects render as tofu boxes — draw icons with curves/planes.
- Silent delivery: add SFX strips 2–3 frames before each hit (`add_sfx`).
- Scene frame_end mismatched with content → dead air.
- Rendering to stale files: version output names or overwrite explicitly.
