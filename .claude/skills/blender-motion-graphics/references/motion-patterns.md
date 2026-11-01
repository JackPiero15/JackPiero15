# Motion Patterns — Blender implementation

All helpers live in `assets/mograph.py` (exec it first). Units: 1 BU = 100 px,
origin = frame center. Frames always via `sec()`.

## 1. Premium entrance (alpha + rise + scale)
```python
t = add_text("Ship faster", size=1.3, color="text", loc=(0, 1.5, 1))
entrance(t, start=sec(0.3))              # EXPO out alpha, smooth rise, 0.94->1 scale
entrance(logo, sec(1), spring="bouncy")  # ELASTIC on transform only, never alpha
```
Manual control: `key_ease(obj, "location", f, v, "out", index=1)` — sets
interpolation + easing on that key. Never call bare `keyframe_insert`.

## 2. Stagger
```python
stagger([card1, card2, card3], start=sec(2), per=sec(0.15))
```
Words 3 frames, cards 4–5, big blocks 6.

## 3. Word-by-word reveal
```python
word_reveal("Edit like a pro in Blender", start=sec(0.2), size=1.2, y=2,
            gap_px=26, hero_word="pro")
```
Gap is in pixels (converted to BU) — never derive spacing from font size.

## 4. Background mesh
`bg_mesh()` → base plane + two spherical-gradient blobs (primary 20 %, accent 13 %)
drifting with sine drivers. Never a flat World color alone.

## 5. Color grade (compositor)
`setup_compositor(grade=0.18, glow=True)` → Color Balance lift tinted toward the hero,
Glare BLOOM for the hero glow. 0.10–0.15 light themes, 0.18–0.25 dark. Per-asset fix:
add a Hue/Saturation node in the material or a strip modifier (VSE).
To see it in screenshots: viewport Shading → Compositor "Always" (4.2+).

## 6. Grain + 7. Vignette
Created by `camera_overlays()` as camera-parented planes (noise 4D with W driven by
frame = flicker; elliptical radial alpha). Top-most layer, always.

## 8. Ken Burns
```python
img = add_image_plane("C:/assets/photo.jpg")      # cover-fit the canvas
ken_burns(img, sec(0), sec(4), zoom_to=1.08, zoom_in=True)
ken_burns(img2, sec(4), sec(8), zoom_in=False)     # alternate
```
VSE strips: `ken_burns_strip(strip, f0, f1)` (keys on `strip.transform`).
Rounded card look: add a Bevel-less plane mask or use a Boolean-free approach —
a slightly larger `bgAlt` plane behind at z-0.01 plus a soft shadow plane.

## 9. Counter
```python
n = add_text("0%", 2.2, "text", loc=(0, 0, 1))
counter(n, sec(1), sec(2.5), 98.6, "{:.1f}%")
```
Handler-based: re-run `counter()` after reopening the .blend (handlers are not saved).
Use a monospace/tabular font to avoid jitter.

## 10. Spark logo mark
`spark(start=sec(0.2), rays=12, size=3)` — rays grow staggered (1.2 f), container
spins in from −120° and scales with ELASTIC. Glow comes from compositor bloom.

## 11. Exits — faster than entrances
`exit_fast(obj, end=sec(4))` → alpha + lift with EXPO ease-in over ~10 frames.
Apply to every visible element or to a holder Empty.

## 12. Idle breathing
```python
h = holder(title)      # keys stay on title, drivers go on the holder
breathe(h, amp=0.015, period_frames=22)
```

## 13. Parallax
`parallax([(bg, 0.3), (mid, 0.6), (fg, 1.0)], sec(0), sec(3), travel=-1.2)`

## 14. Transitions (8–14 frames)
- **Whip pan**: move a scene group 15 BU in 6 frames (`"inOut"`), enable motion blur
  for that shot, cut hidden mid-whip.
- **Scale-through**: A scales to 1.3 + alpha→0; B scales 0.8→1 underneath.
- **Mask wipe**: hero-colored plane sweeps across the canvas; swap content behind it.
- VSE: GAMMA_CROSS / WIPE effect strips only as a last resort; prefer the above.

## 15. Motion blur
`sc().render.use_motion_blur = True` (EEVEE/Cycles), shutter 0.5. Only on shots with
>30 px/frame motion — costs render time.

## 16. Audio + SFX sync
```python
add_music("C:/sfx/bed.mp3", volume=0.25)
add_sfx("C:/sfx/whoosh.wav", frame_hit=sec(0.3) + sec(0.66), lead=3)
fpb = frames_per_beat(120)  # place cuts on multiples
```
Music ~−18 dB under SFX/VO. Final loudness −14 LUFS (ffmpeg loudnorm).

## 17. Word-synced captions
Get word timestamps with Whisper (`--word_timestamps True`, JSON), then:
```python
captions(words, per_page=3, size=0.95)  # at ~65% height, active word = primary
```
2–4 words per page, heavy display font, uppercase.
