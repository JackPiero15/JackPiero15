"""Helpers to run INSIDE Blender 5.x (Video Sequencer) through the Blender MCP execute_blender_code tool.

Load once per session (functions stay in the namespace you pass):
    exec(open(r"<skill>/scripts/blender_vse_helpers.py", encoding="utf-8").read(), globals())
then call e.g.  result = build_scene("M2_foca_916", r"...\\clips\\clips_manifest.json", r"...\\audio\\M2_foca_916_voz_nivelada.wav")

Every function works on scenes by name and never renders. Times are in scene seconds; frame = round(t*fps)+1.
Channels: 1 voz nivelada | 2 video (clips ya en 9:16) | 4 memes | 5 subtítulos | 6 música | 7-8 efectos.
"""
import bpy, os, json

FPS = 30
FONT_PATH = r"C:\Windows\Fonts\seguibl.ttf"   # Segoe UI Black
CAPTION_STYLE = dict(font_size=82, location=(0.5, 0.30), wrap_width=0.88, color=(1, 1, 1, 1),
                     outline_width=0.12, shadow_offset=0.05, shadow_blur=0.3)
TOP_W, TOP_H, TOP_Y = 560, 520, 560          # meme overlay: max width/height (px) and offset above centre


def F(t, fps=FPS):
    return round(t * fps) + 1


def _kf(owner, prop, frame, value):
    setattr(owner, prop, value)
    owner.keyframe_insert(prop, frame=frame)


def _areas(view_type=None):
    win = bpy.context.window
    for a in win.screen.areas:
        if a.type == 'SEQUENCE_EDITOR' and (view_type is None or a.spaces.active.view_type == view_type):
            yield win, a, next(r for r in a.regions if r.type == 'WINDOW')


def stop_playback():
    win = bpy.context.window
    if win and win.screen.is_animation_playing:
        a = win.screen.areas[0]
        rg = next(r for r in a.regions if r.type == 'WINDOW')
        with bpy.context.temp_override(window=win, area=a, region=rg):
            bpy.ops.screen.animation_cancel(restore_frame=False)


def show_scene(name, frame=1, play=False):
    """Make the sequencer show this scene (Blender 5 uses workspace.sequencer_scene), frame all, optionally play."""
    stop_playback()
    win = bpy.context.window
    sc = bpy.data.scenes[name]
    win.scene = sc
    win.workspace.sequencer_scene = sc
    sc.frame_current = frame
    for s in sc.sequence_editor.strips:
        s.select = False
    for w, a, rg in _areas():
        with bpy.context.temp_override(window=w, area=a, region=rg):
            if a.spaces.active.view_type == 'PREVIEW':
                bpy.ops.sequencer.view_all_preview()
            else:
                bpy.ops.sequencer.view_all()
    if play:
        for w, a, rg in _areas('SEQUENCER'):
            with bpy.context.temp_override(window=w, area=a, region=rg):
                bpy.ops.screen.animation_play()
            break
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    return {"scene": name, "frame": frame}


def fullscreen_preview(on=True):
    """Maximise the preview area for screenshots (on=True) or restore the layout (on=False)."""
    win = bpy.context.window
    if on:
        w, a, rg = next(_areas('PREVIEW'))
        with bpy.context.temp_override(window=w, area=a, region=rg):
            bpy.ops.screen.screen_full_area()
        w, a, rg = next(_areas())
        with bpy.context.temp_override(window=w, area=a, region=rg):
            bpy.ops.sequencer.view_all_preview()
    else:
        w, a, rg = next(_areas())
        with bpy.context.temp_override(window=w, area=a, region=rg):
            bpy.ops.screen.back_to_previous()
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)


def new_scene(name, fps=FPS, w=1080, h=1920):
    """Fresh 9:16 scene (replaces one with the same name). Prefetch off: it crashed Blender on this kind of PC."""
    win = bpy.context.window            # None in background mode
    old = bpy.data.scenes.get(name)
    if old:
        if win and win.scene == old:
            tmp = bpy.data.scenes.get("_tmp") or bpy.data.scenes.new("_tmp")
            win.scene = tmp
            win.workspace.sequencer_scene = tmp
        for other in bpy.data.scenes:   # drop SceneStrips that point at the old scene
            if other.sequence_editor:
                for s in [s for s in other.sequence_editor.strips if s.type == 'SCENE' and s.scene == old]:
                    other.sequence_editor.strips.remove(s)
        bpy.data.scenes.remove(old)
    sc = bpy.data.scenes.new(name)
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    r.fps, r.fps_base = fps, 1.0
    r.use_sequencer = True
    sc.view_settings.view_transform = 'Standard'
    sc.sync_mode = 'AUDIO_SYNC'
    sc.frame_start = 1
    sed = sc.sequence_editor_create()
    sed.use_prefetch = False
    tmp = bpy.data.scenes.get("_tmp")
    if tmp:
        if win and win.scene == tmp:
            win.scene = sc
            win.workspace.sequencer_scene = sc
        bpy.data.scenes.remove(tmp)
    return sc


def build_scene(name, manifest_path, stem_path, fps=FPS):
    """Place the baked clips of one scene back to back (trimmed to the cut, handles kept) plus the leveled voice."""
    man = json.load(open(manifest_path, encoding="utf-8-sig"))[name]
    sc = new_scene(name, fps)
    st = sc.sequence_editor.strips
    rec = 1
    for i, c in enumerate(man):
        mv = st.new_movie(f"s{i+1:02d}_video", c["file"], channel=2, frame_start=rec - c["handle_in"])
        mv.frame_offset_start = c["handle_in"]
        mv.frame_offset_end = mv.frame_duration - c["handle_in"] - c["cut_frames"]
        sc.timeline_markers.new(f"{i+1}", frame=rec)
        rec = mv.frame_final_end
    stem = st.new_sound("voz_nivelada", stem_path, channel=1, frame_start=1)
    sc.frame_end = rec - 1
    for s in st:
        s.select = False
    return {"video_frames": rec - 1, "stem_frames": stem.frame_final_duration}   # must be equal


def add_captions(name, captions_path, style=None):
    """Replace the scene's subtitles with captions.json entries (white Segoe UI Black, outline + shadow)."""
    stl = dict(CAPTION_STYLE, **(style or {}))
    caps = json.load(open(captions_path, encoding="utf-8"))[name]
    sc = bpy.data.scenes[name]
    st = sc.sequence_editor.strips
    for s in [s for s in st if s.type == 'TEXT' and s.name.startswith("sub_")]:
        st.remove(s)
    font = bpy.data.fonts.load(FONT_PATH, check_existing=True)
    for i, c in enumerate(caps):
        f0 = F(c["t0"]); f1 = max(F(c["t1"]), f0 + 1)
        t = st.new_effect(f"sub_{i+1:03d}", 'TEXT', channel=5, frame_start=f0, length=f1 - f0)
        t.text = c["text"]; t.font = font
        t.font_size = stl["font_size"]; t.color = stl["color"]
        t.location = stl["location"]; t.wrap_width = stl["wrap_width"]
        t.anchor_x = 'CENTER'; t.anchor_y = 'CENTER'; t.alignment_x = 'CENTER'
        t.use_outline = True; t.outline_color = (0, 0, 0, 1); t.outline_width = stl["outline_width"]
        t.use_shadow = True; t.shadow_color = (0, 0, 0, 0.55)
        t.shadow_offset = stl["shadow_offset"]; t.shadow_blur = stl["shadow_blur"]
        t.select = False
    n = len([s for s in st if s.type == 'TEXT' and s.name.startswith("sub_")])
    return {"expected": len(caps), "placed": n}   # if they differ, a strip collided: re-run or re-add the missing one


def add_image(name, path, t0, t1, mode="top"):
    """Meme image. mode='top': pops in above the character's head; mode='full': end card covering the screen."""
    sc = bpy.data.scenes[name]
    st = sc.sequence_editor.strips
    s = st.new_image("meme_" + os.path.splitext(os.path.basename(path))[0], path, channel=4, frame_start=F(t0))
    s.frame_final_duration = max(F(t1) - F(t0), 2)
    w, h = bpy.data.images.load(path, check_existing=True).size
    a, b = s.frame_final_start, s.frame_final_end
    if mode == "top":
        k = min(TOP_W / w, TOP_H / h)
        s.transform.offset_y = TOP_Y
        for fr, v in ((a, 0.0), (a + 3, k * 1.15), (a + 5, k)):
            _kf(s.transform, "scale_x", fr, v); _kf(s.transform, "scale_y", fr, v)
        _kf(s, "blend_alpha", b - 4, 1.0); _kf(s, "blend_alpha", b, 0.0)
    else:
        k = max(1080 / w, 1920 / h)
        for fr, v in ((a, k * 1.12), (a + 6, k)):
            _kf(s.transform, "scale_x", fr, v); _kf(s.transform, "scale_y", fr, v)
    s.select = False
    return [s.name, a, b, s.channel]


def set_image_end(name, strip_name, t1):
    """Shorten/extend an overlay and move its fade-out (Blender 5 actions are layered: delete keys, don't touch fcurves)."""
    s = bpy.data.scenes[name].sequence_editor.strips[strip_name]
    old = s.frame_final_end
    for fr in (old - 4, old):
        try:
            s.keyframe_delete("blend_alpha", frame=fr)
        except RuntimeError:
            pass
    s.frame_final_end = F(t1)
    _kf(s, "blend_alpha", s.frame_final_end - 4, 1.0); _kf(s, "blend_alpha", s.frame_final_end, 0.0)
    return [s.frame_final_start, s.frame_final_end]


def add_sfx(name, path, t0, vol, t_end=None, channel=7, envelope=None, label=None):
    """Sound effect / music. envelope=[(t, vol), ...] overrides the default hold-then-fade (use it to duck under speech)."""
    sc = bpy.data.scenes[name]
    st = sc.sequence_editor.strips
    s = st.new_sound("sfx_" + (label or os.path.splitext(os.path.basename(path))[0][:14]) + f"_{t0:.1f}",
                     path, channel=channel, frame_start=F(t0))
    if t_end is not None and F(t_end) < s.frame_final_end:
        s.frame_final_end = F(t_end)
    a, b = s.frame_final_start, s.frame_final_end
    if envelope:
        for t, v in envelope:
            _kf(s, "volume", F(t), v)
    else:
        _kf(s, "volume", a, vol); _kf(s, "volume", max(b - 6, a + 1), vol); _kf(s, "volume", b, 0.0)
    return [s.name, a, b]


def add_zoom(name, t_in, t_full, t_out=None, z=1.2):
    """Punch-in on the video under t_in: 1.0 -> z, back to 1.0 at t_out (or keep until the cut)."""
    st = bpy.data.scenes[name].sequence_editor.strips
    v = [s for s in st if s.type == 'MOVIE' and s.frame_final_start <= F(t_in) < s.frame_final_end][0]
    pts = [(F(t_in), 1.0), (F(t_full), z)]
    if t_out is not None and F(t_out) < v.frame_final_end:
        pts += [(F(t_out) - 1, z), (F(t_out), 1.0)]
    for fr, val in pts:
        _kf(v.transform, "scale_x", fr, val); _kf(v.transform, "scale_y", fr, val)
    return v.name


def remove_strips(name, prefixes):
    st = bpy.data.scenes[name].sequence_editor.strips
    gone = [s.name for s in st if s.name.startswith(tuple(prefixes))]
    for n in gone:
        st.remove(st[n])
    return gone


def build_final(final_name, scenes, intro=None, fps=FPS):
    """Final TikTok: optional intro, then each scene as a SceneStrip back to back (no title cards).

    intro = {"dur": 3.5, "title1": "MOMENTOS INCÓMODOS", "title2": "DE PODCAST ROBLOX",
             "song": r"...mp3", "song_vol": 0.72, "shots": [(clip_path, source_frame), ...]}
    """
    sc = new_scene(final_name, fps)
    st = sc.sequence_editor.strips
    rec = 1
    if intro:
        n_intro = round(intro.get("dur", 3.5) * fps)
        shots = intro.get("shots", [])
        f = 1
        for i, (path, src_f) in enumerate(shots):
            n = n_intro // len(shots) if i < len(shots) - 1 else n_intro - (n_intro // len(shots)) * (len(shots) - 1)
            mv = st.new_movie(f"intro_{i+1}", path, channel=2, frame_start=f - src_f)
            mv.frame_offset_start = src_f
            mv.frame_offset_end = mv.frame_duration - src_f - n
            mv.color_multiply = 0.55
            _kf(mv.transform, "scale_x", f, 1.0); _kf(mv.transform, "scale_y", f, 1.0)
            _kf(mv.transform, "scale_x", f + n - 1, 1.08); _kf(mv.transform, "scale_y", f + n - 1, 1.08)
            f += n
        font = bpy.data.fonts.load(FONT_PATH, check_existing=True)
        # two separate text strips, far enough apart: each title wraps to two lines at these sizes
        for nm, text, size, y, start, color in (("intro_titulo_1", intro.get("title1", ""), 124, 0.62, 1, (1, 1, 1, 1)),
                                                ("intro_titulo_2", intro.get("title2", ""), 100, 0.45, 8, (1.0, 0.84, 0.12, 1))):
            if not text:
                continue
            t = st.new_effect(nm, 'TEXT', channel=5, frame_start=start, length=n_intro - start + 1)
            t.text = text; t.font = font; t.font_size = size; t.color = color
            t.location = (0.5, y); t.anchor_x = t.anchor_y = 'CENTER'; t.alignment_x = 'CENTER'; t.wrap_width = 0.92
            t.use_outline = True; t.outline_color = (0, 0, 0, 1); t.outline_width = 0.12
            t.use_shadow = True; t.shadow_color = (0, 0, 0, 0.6); t.shadow_offset = 0.05; t.shadow_blur = 0.3
            for fr, v in ((start, 0.0), (start + 4, 1.18), (start + 7, 1.0)):
                _kf(t.transform, "scale_x", fr, v); _kf(t.transform, "scale_y", fr, v)
        if intro.get("song"):
            s = st.new_sound("intro_cancion", intro["song"], channel=7, frame_start=1)
            s.frame_final_end = min(s.frame_final_end, n_intro + 7)
            vol = intro.get("song_vol", 0.72)
            _kf(s, "volume", 1, vol); _kf(s, "volume", n_intro - 4, vol); _kf(s, "volume", s.frame_final_end, 0.0)
        rec = n_intro + 1
    parts = []
    for name in scenes:
        src = bpy.data.scenes[name]
        s = st.new_scene(name, src, channel=1, frame_start=rec)
        s.scene_input = 'SEQUENCER'
        s.frame_final_duration = src.frame_end - src.frame_start + 1
        sc.timeline_markers.new(name.split("_")[0], frame=rec)
        parts.append({"scene": name, "starts_s": round((rec - 1) / fps, 2), "dur_s": round(s.frame_final_duration / fps, 2)})
        rec = s.frame_final_end
    sc.frame_end = rec - 1
    for s in st:
        s.select = False
    return {"parts": parts, "total_s": round(sc.frame_end / fps, 2)}


def refresh_final(final_name="TIKTOK_final"):
    """After changing a scene's length, resync the SceneStrip durations and the final end frame."""
    sc = bpy.data.scenes[final_name]
    st = sorted([s for s in sc.sequence_editor.strips if s.type == 'SCENE'], key=lambda s: s.frame_final_start)
    rec = st[0].frame_final_start if st else 1
    for s in st:
        s.frame_start = rec
        s.frame_final_duration = s.scene.frame_end - s.scene.frame_start + 1
        rec = s.frame_final_end
    sc.frame_end = rec - 1
    return {"total_s": round(sc.frame_end / FPS, 2)}


def set_export(final_name, out_path):
    """Best-quality TikTok settings: 1080x1920 30 fps, H.264 perceptually lossless, AAC 320 kbps 48 kHz."""
    sc = bpy.data.scenes[final_name]
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
    r.use_sequencer = True
    r.use_compositing = False
    ims = r.image_settings
    if hasattr(ims, "media_type"):
        ims.media_type = 'VIDEO'          # Blender 5: otherwise 'FFMPEG' is not a valid file_format
    ims.file_format = 'FFMPEG'
    ff = r.ffmpeg
    ff.format = 'MPEG4'; ff.codec = 'H264'
    ff.constant_rate_factor = 'PERC_LOSSLESS'; ff.ffmpeg_preset = 'GOOD'; ff.gopsize = 30
    ff.audio_codec = 'AAC'; ff.audio_bitrate = 320; ff.audio_mixrate = 48000; ff.audio_channels = 'STEREO'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    r.filepath = out_path
    r.use_file_extension = False
    return {"out": out_path, "frames": [sc.frame_start, sc.frame_end]}


def save_version(path):
    """Save a NEW versioned .blend (tiktok_vNN_*.blend); never overwrite the previous version."""
    bpy.ops.wm.save_as_mainfile(filepath=path)
    return {"saved": bpy.data.filepath}
