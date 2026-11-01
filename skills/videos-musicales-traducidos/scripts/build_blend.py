"""Build one format of one piece in Blender's VSE from pieces/<piece>.json + subs/<id>/<fmt>/timing.json.

Run inside Blender (MCP):  g = {"__file__": path, "PROJECT": project_dir}; exec(open(path).read(), g)
                           g["build"]("song", "vertical"); g["save_version"]()
Formats: "vertical" (1080x1920 fragment) and "horizontal" (1920x1080 complete song for YouTube).

Channels: 1 song (master audio) | 2 footage | 4 gradient or plate | 5 subtitles
Footage strips never carry sound: no sound strips are created for them.
Shots (piece[fmt]["shots"]):
  "mode": "montage" -> shots have "k" (beat range, or "t0"/"t1" seconds) + "src" (source in, seconds)
  "mode": "sync"    -> footage = the song's own video; shots have "t" (montage start, seconds);
                       source time = montage time + in + video_offset (lip-sync kept),
                       unless the shot gives "src" (cutaway used to cover a black gap).
Each shot: "cx" source x centre (number or [from, to] for a slow pan), "flip", "scale" (multiplier).
"""
import json
import os

import bpy

ROOT = globals().get("PROJECT") or os.environ.get("MT_PROJECT") or os.getcwd()   # pass PROJECT in the exec namespace
SIZE = {"vertical": (1080, 1920), "horizontal": (1920, 1080)}
SCENE_SUFFIX = {"vertical": "VERTICAL", "horizontal": "YOUTUBE_16x9"}
OUT_SUFFIX = {"vertical": "VERTICAL", "horizontal": "YOUTUBE_COMPLETO_16x9"}
PREFIX = globals().get("BLEND_PREFIX", "proyecto")


def fcurves_of(action):
    out = []
    for layer in action.layers:
        for st in layer.strips:
            for cb in st.channelbags:
                out.extend(cb.fcurves)
    return out


def build(piece_name, fmt):
    piece = json.load(open(os.path.join(ROOT, "pieces", piece_name + ".json"), encoding="utf-8"))
    cfg = piece[fmt]
    W, H = SIZE[fmt]
    sub_dir = os.path.join(ROOT, "subs", piece["id"], fmt)
    timing = json.load(open(os.path.join(sub_dir, "timing.json"), encoding="utf-8"))
    scene_name = f"{piece['scene']}_{SCENE_SUFFIX[fmt]}"

    old = bpy.data.scenes.get(scene_name)
    if old:
        bpy.data.scenes.remove(old)
    sc = bpy.data.scenes.new(scene_name)
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
    r.fps, r.fps_base = cfg.get("fps", piece["fps"])
    fps = r.fps / r.fps_base
    r.use_sequencer = True
    sc.view_settings.view_transform = "Standard"    # keep the footage's own colours
    sc.view_settings.look = "None"
    sc.sequencer_colorspace_settings.name = "sRGB"
    sc["piece_id"] = piece["id"]
    sc["format"] = fmt

    f = lambda s: round(s * fps)
    strips = sc.sequence_editor_create().strips
    a_in_f, a_out_f = f(cfg["in"]), f(cfg["out"])
    n_frames = a_out_f - a_in_f
    sc.frame_start, sc.frame_end = 1, n_frames
    rec0 = 1

    # 1 - master song (only audio in the edit)
    snd = strips.new_sound("SONG", os.path.join(ROOT, piece["audio_file"]), channel=1, frame_start=rec0 - a_in_f)
    snd.frame_offset_start = a_in_f
    snd.frame_offset_end = max(0, snd.frame_duration - a_out_f)
    fi, fo = max(1, f(cfg.get("fade_in", 0.04))), max(1, f(cfg.get("fade_out", 0.08)))
    for fr, v in ((rec0, 0.0), (rec0 + fi, 1.0), (rec0 + n_frames - fo, 1.0), (rec0 + n_frames, 0.0)):
        snd.volume = v
        snd.keyframe_insert("volume", frame=fr)

    # 2 - footage
    vfile = os.path.join(ROOT, cfg["video_file"])
    src_w, src_h = cfg["src_w"], cfg["src_h"]
    base = (H / src_h) if fmt == "vertical" else (W / src_w)
    shots = cfg["shots"]
    dur = cfg["out"] - cfg["in"]
    placed = []
    for i, s in enumerate(shots):
        if cfg.get("mode", "montage") == "montage":
            m0 = s["t0"] if "t0" in s else s["k"][0] * cfg["beat"]
            m1 = min(s["t1"] if "t1" in s else s["k"][1] * cfg["beat"], dur)
            src = s["src"]
        else:
            m0 = s["t"]
            m1 = shots[i + 1]["t"] if i + 1 < len(shots) else dur
            src = s["src"] if "src" in s else m0 + cfg["in"] + cfg.get("video_offset", 0.0)
        r0, r1 = rec0 + f(m0), rec0 + f(m1)
        if i == len(shots) - 1:
            r1 = rec0 + n_frames
        if r1 <= r0:
            continue
        sf = f(src)
        mv = strips.new_movie(f"S{i + 1:03d}", vfile, channel=2, frame_start=r0 - sf)
        mv.frame_offset_start = sf
        mv.frame_offset_end = max(0, mv.frame_duration - (sf + (r1 - r0)))
        scale = base * s.get("scale", 1.0)
        mv.transform.scale_x = mv.transform.scale_y = scale
        mv.use_flip_x = bool(s.get("flip"))
        cx = s.get("cx", src_w / 2)
        sign = -1 if mv.use_flip_x else 1
        half = (W / 2) / scale          # half visible width in source px: never show past the frame edge
        clamp = lambda c: min(max(c, half), src_w - half)
        off = lambda c: sign * (src_w / 2 - clamp(c)) * scale
        mv.transform.offset_y = s.get("oy", 0)
        if isinstance(cx, list):
            mv.transform.offset_x = off(cx[0])
            mv.transform.keyframe_insert("offset_x", frame=r0)
            mv.transform.offset_x = off(cx[1])
            mv.transform.keyframe_insert("offset_x", frame=r1 - 1)
        else:
            mv.transform.offset_x = off(cx)
        if s.get("desc"):
            sc.timeline_markers.new(f"S{i + 1:03d} {s['desc']}"[:60], frame=r0)
        placed.append([mv.name, r0, r1, round(src, 3)])
    for mk in cfg.get("markers", []):          # verses / musical changes, in source seconds
        sc.timeline_markers.new(mk[1][:60], frame=rec0 + f(mk[0] - cfg["in"]))

    # 4 - localized gradient or text-hiding plate
    g = strips.new_image("GRADIENT_O_PLACA", os.path.join(sub_dir, "gradient.png"), channel=4, frame_start=rec0)
    g.frame_final_duration = n_frames
    g.blend_type = "ALPHA_OVER"

    # 5 - subtitles: 3-frame entrance (alpha + 10 px rise, EXPO out), 2-frame exit (EXPO in)
    ent, ex = max(2, f(0.125)), 2
    for t in timing:
        r0, r1 = rec0 + f(t["in"]), rec0 + f(t["out"])
        im = strips.new_image(f"L{t['n']:03d}", os.path.join(sub_dir, t["png"]), channel=5, frame_start=r0)
        im.frame_final_duration = max(1, r1 - r0)
        im.blend_type = "ALPHA_OVER"
        for fr, al, oy in ((r0, 0.0, -10.0), (r0 + ent, 1.0, 0.0)):
            im.blend_alpha = al
            im.keyframe_insert("blend_alpha", frame=fr)
            im.transform.offset_y = oy
            im.transform.keyframe_insert("offset_y", frame=fr)
        im.blend_alpha = 1.0
        im.keyframe_insert("blend_alpha", frame=r1 - ex)
        im.blend_alpha = 0.0
        im.keyframe_insert("blend_alpha", frame=r1)

    for fc in fcurves_of(sc.animation_data.action):
        kps = fc.keyframe_points
        if "blend_alpha" in fc.data_path or "offset_y" in fc.data_path:
            for k, kp in enumerate(kps):
                kp.interpolation, kp.easing = "EXPO", "EASE_IN" if k >= 2 else "EASE_OUT"
        elif "offset_x" in fc.data_path:
            for kp in kps:
                kp.interpolation, kp.easing = "QUINT", "EASE_IN_OUT"
        elif fc.data_path.endswith("volume"):
            for kp in kps:
                kp.interpolation, kp.easing = "SINE", "EASE_IN_OUT"

    # render settings: video only, CRF 17 (audio is muxed once from the source with ffmpeg)
    if hasattr(r.image_settings, "media_type"):
        r.image_settings.media_type = "VIDEO"     # Blender 5.x: must precede file_format
    r.image_settings.file_format = "FFMPEG"
    r.ffmpeg.format = "MPEG4"
    r.ffmpeg.codec = "H264"
    r.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"
    r.ffmpeg.ffmpeg_preset = "GOOD"
    r.ffmpeg.gopsize = round(fps * 2)
    r.ffmpeg.audio_codec = "NONE"
    r.filepath = f"//render/{piece['id']}_{OUT_SUFFIX[fmt]}_video.mp4"

    return {"scene": sc.name, "frames": n_frames, "fps": round(fps, 5), "in_q": a_in_f / fps,
            "out_q": a_out_f / fps, "shots": len(placed), "subs": len(timing)}


def save_version():
    """Save the project (all scenes) as <PREFIX>_vNN.blend in the project folder, paths relative."""
    n = 1
    while os.path.exists(os.path.join(ROOT, f"{PREFIX}_v{n:02d}.blend")):
        n += 1
    path = os.path.join(ROOT, f"{PREFIX}_v{n:02d}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, relative_remap=True)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
    return path
