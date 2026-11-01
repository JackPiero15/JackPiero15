# Design Rules — Color, Type, Pacing, Sound, Checklist (Blender)

## Color system
One dark (or light) base + ONE hero color + one accent + neutrals. 60/30/10:
60% base, 30% secondary surfaces, 10% hero. The hero color appears on AT MOST
one element per frame — it directs the eye.

Proven palettes (edit `theme["colors"]`):
- Dark tech: base #0A0A0F, hero #7C3AED, accent #22D3EE, text #F4F4F5
- Warm editorial: base #FAF7F2, hero #D97757, ink #1F1E1B
- Warm premium: base #1A120B, hero #E8A33D, accent #F4E9DA
- Clean light: base #F7F5F2, ink #1A1A1A + one saturated accent
- True crime / suspense: base #0B0B0D, hero #C1121F, text #EDEDED

Glow on the hero only: emission strength 2–4 on that object + compositor Glare
BLOOM. More than one glowing element per frame = Vegas. Don't.

## Typography
- Hero text: display face (Clash Display, Cabinet Grotesk, Satoshi, Montserrat
  ExtraBold — Fontshare / Google Fonts), loaded with `load_font()`. Never Bfont.
  Weight 600–800, `space_character` 0.97, line height 1.05.
- Reels hero size: 0.8–1.4 BU (80–140 px) at 1080 wide. Landscape: 1.0–1.6 BU.
- Body/captions: clean sans (Inter) 400–500, `textDim` color.
- Highlight ONE word per headline: hero color, animated underline plane, or a pill
  plane scaling in behind it 5 frames after the word lands.
- Numbers: `counter()` with a tabular/mono font.

## Scene architecture
30 s Reel:
```
0.0–1.5s  HOOK    boldest visual + claim. Movement within the FIRST 15 frames.
1.5–3.0s  CONTEXT one line, one visual, still moving.
3–22s     BODY    3–4 beats. Each beat: HIT -> hold (15–20 still frames) -> build.
22–27s    PAYOFF  result/number/demo. Biggest animation of the video.
27–30s    CTA     one action, calm, glow on the CTA word.
```
- New visual element at least every 90 frames.
- Holds are a design tool: fast move -> complete stillness -> next move.
- 9:16 safe zone: critical content within the middle ~75% vertically
  (y between −7.2 and +7.2 BU at 1920 high).
- 5 s logo sting: mark in (0–0.8 s) -> wordmark (0.6–1.8 s) -> tagline (2–3.5 s)
  -> breathe -> exit (last 0.5 s).

## Sound design (50% of perceived quality — never deliver silent unless asked)
- Every entrance HIT: whoosh/click 2–3 frames BEFORE the visual lands (`add_sfx`).
- Transitions: riser into the cut, bass hit ON the cut.
- Counters: soft tick loop while counting.
- Music bed ~0.2–0.3 volume, ducked further under VO. Final −14 LUFS.
- Pick music first; `frames_per_beat(bpm)`; cut on beats.
- Free SFX: Pixabay, Mixkit, freesound.org. 10-file kit: 2 whooshes, 2 clicks,
  riser, bass hit, shimmer, tick, pop, reverse-swoosh.

## Asset generation guidance
Lock a prompt skeleton, vary only the subject, same lighting + palette words,
generate at final aspect ratio:
```
[subject], cinematic product photography, dark moody studio, [hero color] rim
lighting, deep shadows, shallow depth of field, 9:16
```

## Render settings
- Masters: FFmpeg MPEG4 / H.264, CRF HIGH, AAC 192k (`final_render`).
- EEVEE 16–32 samples is enough for flat mograph; Cycles only for real 3D.
- Weak PC: verify with viewport screenshots, render ONCE at the end, with approval.
- Inspect easing in the Graph Editor — flaws invisible at 1x are obvious there.

## PRE-DELIVERY CHECKLIST
- [ ] `audit_linear()` returns []; no BACK/ELASTIC on alpha
- [ ] Entrances = 2–3 properties, staggered; nothing enters simultaneously
- [ ] Exits animated, faster than entrances
- [ ] Every still has Ken Burns; fast moves have motion blur
- [ ] 5-layer stack (bg_mesh, assets, type, compositor grade, FX_Grain + FX_Vignette)
- [ ] One hero color, ≤1 hero-colored/glowing element per frame
- [ ] Display font ≥600 weight on heroes; no Bfont hero text
- [ ] Pixel gaps between words/blocks, no overlaps
- [ ] Holds exist: ≥3 moments of stillness
- [ ] SFX on major hits, cuts on beat (if audio in scope)
- [ ] Text inside safe zone; nothing touching frame edges
- [ ] Key frames screenshotted and inspected, fixed, re-inspected; final mp4
      checked with ffprobe + 3 extracted frames
