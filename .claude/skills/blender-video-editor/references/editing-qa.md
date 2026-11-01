# Editing QA Gates (adapted from the DaVinci social-editor skills)

Run these before calling any TikTok/YouTube edit done.

## Story coherence
Structure: **hook/agenda -> body (complete ideas in order) -> recap/CTA**.
Reject cuts that start after needed context, stitch unrelated snippets, drop the setup of a later claim, or end without the main promise.
Transcript timestamps only *locate* material; cut on complete ideas, pauses and sentence boundaries.

## Jump-cut prevention
Each cut needs at least one: new angle, new crop scale (punch-in/out via strip `transform.scale_x/y`), B-roll/graphic over the seam, short dissolve at a section boundary, motivated hard cut, or natural pause.
Same clip + same scale on both sides of a cut = fail. Avoid video crossfades on talking heads (ghosting); prefer hard cut + 2-4 frame audio fade, J/L-cuts, punch-ins or B-roll.

## B-roll
B-roll is evidence, not filler: record which claim it proves or which jump it covers. Hold 1.2-3 s, full opacity (no low-opacity overlays on faces). Keep the speaker on screen for trust beats; static slides/boards max 3-5 s in vertical.
Stock: only licensed sources (e.g. Coverr, Pexels) and note URL + license per clip.

## Frame safety
Speaker visible during speech. Vertical: eyes near the upper third, captions off the mouth/chin and above the bottom ~20% (TikTok/Reels UI). No black/blank angles. Check stills at opening, each beat, CTA, closing.

## Captions
Netflix style: big white bold sans, black outline or translucent box, max 2 lines, bottom-safe. Proofread names/brands. An SRT alone is not "done": there must be a burned-in review render or visible text strips.

## Audio (voice first, music is texture)
- Audit sources first (`scripts/audio_quality_audit.py`); pick the best dialogue, mute weak/scratch tracks.
- Broken stereo (one dead channel) -> duplicate the good channel to dual mono before anything else.
- Music ducked under speech (Blender: keyframe sound strip `volume`, or FFmpeg `sidechaincompress`). Duck subtle (~3-5 dB), never louder than voice.
- Targets: TikTok/Reels about **-14 LUFS** (range -15 to -13), YouTube **-14 LUFS**, true peak **below -1 dBTP**.
- 2-4 frame fades at every dialogue cut to avoid pops.

## Render runtime
Looped music or still images must not extend the video: cap with scene `frame_end` (Blender) or `-t`/`-shortest` (FFmpeg). Verify output duration against the edit plan.

## Color (documentary / creator look)
Neutral skin, moderate contrast, lifted mids if dark, restrained saturation (no crunchy LUTs). Normalize -> balance -> enhance, in that order.

## Final answer must state
Output path, duration/resolution/fps, what was checked (stills, loudness), and anything not verified.
