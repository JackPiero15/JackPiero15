# mograph.py — Blender motion-graphics helper library (Blender 4.2 – 5.x).
# Exec once per session through the Blender MCP (paste the file into
# execute_blender_code), or: exec(open(r"<path>/mograph.py").read())
# Canvas convention: 1 Blender unit = 100 px, origin = frame center, XY plane,
# orthographic camera looking down -Z. A 1080x1920 frame spans x ±5.4, y ±9.6.
import bpy
import math
import mathutils

# ---------------------------------------------------------------- theme ----
def hex_rgba(h, a=1.0):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)

theme = {
    "colors": {"bg": "#0A0A0F", "bgAlt": "#12121A", "primary": "#7C3AED",
               "accent": "#22D3EE", "text": "#F4F4F5", "textDim": "#A1A1AA"},
    "fonts": {"display": "", "body": ""},
    "ease": {"out": ("EXPO", "EASE_OUT"), "inOut": ("QUINT", "EASE_IN_OUT"),
             "in": ("EXPO", "EASE_IN")},
    "spring": {"snappy": ("BACK", "EASE_OUT", 1.2), "smooth": ("EXPO", "EASE_OUT", None),
               "bouncy": ("ELASTIC", "EASE_OUT", None)},
    "timing": {"enter": 0.66, "exit": 0.33, "stagger_word": 0.1,
               "stagger_card": 0.15, "hold": 0.6},
}
C = lambda name, a=1.0: hex_rgba(theme["colors"][name], a)

def sc():
    return bpy.context.scene

def sec(s):
    """Seconds -> frames, always from scene fps."""
    r = sc().render
    return round(s * r.fps / r.fps_base)

# ------------------------------------------------------------ fcurves -----
def _fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    try:  # legacy / 4.x compatibility API
        fcs = act.fcurves
        if fcs is not None and len(fcs):
            return list(fcs)
    except AttributeError:
        pass
    out = []  # layered (slotted) actions, 4.4+ / 5.x
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            cb = strip.channelbag(ad.action_slot) if ad.action_slot else None
            if cb:
                out.extend(cb.fcurves)
    return out

def key_ease(idb, path, frame, value, ease="out", index=-1):
    """Set + keyframe a property with a non-linear interpolation.
    idb: any ID / struct with keyframe_insert (object, material.node_tree, strip...).
    ease: key of theme['ease'] or theme['spring'] (snappy/smooth/bouncy)."""
    # resolve owner for nested paths like 'nodes["Mix"].inputs[0].default_value'
    if "." in path or "[" in path:
        owner_path, _, prop = path.rpartition(".")
        owner = idb.path_resolve(owner_path) if owner_path else idb
    else:
        owner, prop = idb, path
    if index >= 0:
        getattr(owner, prop)[index] = value
    else:
        setattr(owner, prop, value)
    owner.keyframe_insert(prop, index=index, frame=frame)
    if ease in theme["ease"]:
        interp, easing = theme["ease"][ease]
        back = None
    else:
        interp, easing, back = theme["spring"][ease]
    id_owner = idb.id_data
    full = path if isinstance(idb, bpy.types.ID) else idb.path_from_id(path)
    for fc in _fcurves(id_owner):
        if fc.data_path != full or (index >= 0 and fc.array_index != index):
            continue
        for kp in fc.keyframe_points:
            if abs(kp.co[0] - frame) < 0.5:
                kp.interpolation = interp
                kp.easing = easing
                if back is not None:
                    kp.back = back

def audit_linear():
    """Return every LINEAR keyframe in the file. Must be empty before delivery."""
    bad = []
    for a in bpy.data.actions:
        fcs = []
        try:
            fcs = list(a.fcurves)
        except AttributeError:
            for layer in a.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        fcs.extend(cb.fcurves)
        for fc in fcs:
            for kp in fc.keyframe_points:
                if kp.interpolation == "LINEAR":
                    bad.append((a.name, fc.data_path, fc.array_index, kp.co[0]))
    return bad

# ------------------------------------------------------------- scene ------
def _strips(se):
    return se.strips if hasattr(se, "strips") else se.sequences

def setup_scene(w=1080, h=1920, fps=30, seconds=15, engine="EEVEE",
                transparent=False, grade=True):
    s = sc()
    r = s.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    r.fps, r.fps_base = fps, 1
    s.frame_start, s.frame_end = 1, sec(seconds)
    for eng in (("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE") if engine == "EEVEE" else (engine,)):
        try:
            r.engine = eng
            break
        except TypeError:
            continue
    r.film_transparent = transparent
    vs = s.view_settings
    for vt in ("AgX", "Filmic"):
        try:
            vs.view_transform = vt
            break
        except TypeError:
            pass
    try:
        vs.look = "AgX - Medium High Contrast" if vs.view_transform == "AgX" else "Medium High Contrast"
    except TypeError:
        pass
    # world = bg color (bg mesh planes sit above it)
    world = s.world or bpy.data.worlds.new("MG_World")
    s.world = world
    world.use_nodes = True
    bgn = world.node_tree.nodes.get("Background")
    if bgn:
        bgn.inputs[0].default_value = C("bg")
    # ortho camera framing the canvas
    cam = bpy.data.objects.get("MG_Camera")
    if not cam:
        cam = bpy.data.objects.new("MG_Camera", bpy.data.cameras.new("MG_Camera"))
        s.collection.objects.link(cam)
    cam.location, cam.rotation_euler = (0, 0, 20), (0, 0, 0)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(w, h) / 100
    cam.data.clip_end = 100
    s.camera = cam
    if grade:
        setup_compositor()
    return cam

def canvas():
    r = sc().render
    return r.resolution_x / 100, r.resolution_y / 100  # width, height in units

# ---------------------------------------------------------- materials -----
def make_emission_mat(name, color, strength=1.0, image=None):
    """Emission + Transparent mixed by node 'Alpha' (Mix Shader). Animate alpha with
    key_ease(mat.node_tree, 'nodes["Alpha"].inputs[0].default_value', f, v)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.name = "Emit"
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.name = "Alpha"
    mix.inputs[0].default_value = 1.0
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    if image:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image, check_existing=True)
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.name = "AlphaMul"
        nt.links.new(tex.outputs["Alpha"], mul.inputs[0])
        mul.inputs[1].default_value = 1.0
        nt.links.new(mul.outputs[0], mix.inputs[0])
        # animate 'nodes["AlphaMul"].inputs[1].default_value' for image alpha
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        if hasattr(m, attr):
            try:
                setattr(m, attr, val)
            except TypeError:
                pass
    return m

def alpha_path(mat):
    return ('nodes["AlphaMul"].inputs[1].default_value' if "AlphaMul" in mat.node_tree.nodes
            else 'nodes["Alpha"].inputs[0].default_value')

def key_alpha(obj, frame, value, ease="out"):
    m = obj.active_material
    key_ease(m.node_tree, alpha_path(m), frame, value, ease if ease in theme["ease"] else "out")

# ------------------------------------------------------------ objects -----
_fonts = {}
def load_font(path):
    if path and path not in _fonts:
        _fonts[path] = bpy.data.fonts.load(path, check_existing=True)
    return _fonts.get(path)

def add_text(body, size=1.0, color="text", font="display", align="CENTER",
             loc=(0, 0, 1), name=None, extrude=0.0):
    """size in units (1.0 = 100 px cap height approx)."""
    cu = bpy.data.curves.new(name or "T_" + body[:12], "FONT")
    cu.body = body
    cu.size = size
    cu.align_x, cu.align_y = align, "CENTER"
    cu.extrude = extrude
    cu.space_character = 0.97  # tight tracking (-0.03em)
    f = load_font(theme["fonts"].get(font, ""))
    if f:
        cu.font = f
    ob = bpy.data.objects.new(cu.name, cu)
    sc().collection.objects.link(ob)
    ob.location = loc
    ob.data.materials.append(make_emission_mat("M_" + cu.name, C(color)))
    return ob

def add_plane(w, h, loc=(0, 0, 0), color="bgAlt", image=None, name="Plane"):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (w, h, 1)
    bpy.ops.object.transform_apply(scale=True)
    ob.data.materials.append(make_emission_mat("M_" + name, C(color), image=image))
    return ob

def add_image_plane(path, loc=(0, 0, 0.1), fit="cover", name="Img"):
    img = bpy.data.images.load(path, check_existing=True)
    iw, ih = img.size
    cw, ch = canvas()
    k = max(cw / iw, ch / ih) if fit == "cover" else min(cw / iw, ch / ih)
    return add_plane(iw * k, ih * k, loc, image=path, name=name)

# ---------------------------------------------------------- motion --------
def entrance(obj, start, rise=0.4, scale_from=0.94, dur=None, spring="smooth"):
    """Premium entrance: alpha 0->1 + rise in Y + scale up. Never a lone fade."""
    d = dur or sec(theme["timing"]["enter"])
    y = obj.location.y
    s = obj.scale.copy()
    key_alpha(obj, start, 0.0)
    key_alpha(obj, start + d, 1.0)
    key_ease(obj, "location", start, y - rise, "out", index=1)
    key_ease(obj, "location", start + d, y, spring, index=1)
    for i in range(3):
        key_ease(obj, "scale", start, s[i] * scale_from, "out", index=i)
        key_ease(obj, "scale", start + d, s[i], spring, index=i)

def exit_fast(obj, end, lift=0.42, dur=None):
    """Exit ends at `end`, ~half the entrance duration, EASE_IN."""
    d = dur or sec(theme["timing"]["exit"])
    y = obj.location.y
    key_alpha(obj, end - d, 1.0, "in")
    key_alpha(obj, end, 0.0, "in")
    key_ease(obj, "location", end - d, y, "in", index=1)
    key_ease(obj, "location", end, y + lift, "in", index=1)
    obj.location.y = y

def stagger(objs, start, per=None, **kw):
    per = per or sec(theme["timing"]["stagger_card"])
    for i, o in enumerate(objs):
        entrance(o, start + i * per, **kw)

def word_reveal(text, start, size=1.2, y=0.0, gap_px=26, per=None, color="text",
                hero_word=None, max_width=None):
    """One text object per word, laid out centered (wraps at max_width units),
    staggered snappy entrances. hero_word gets the primary color."""
    per = per or sec(theme["timing"]["stagger_word"])
    max_width = max_width or canvas()[0] * 0.8
    words = []
    for wd in text.split():
        col = "primary" if hero_word and wd.strip(".,!?").lower() == hero_word.lower() else color
        o = add_text(wd, size, col, align="LEFT", loc=(0, y, 1), name="W_" + wd)
        words.append(o)
    bpy.context.view_layer.update()
    gap = gap_px / 100
    lines, cur, cw = [], [], 0
    for o in words:
        w = o.dimensions.x
        if cur and cw + gap + w > max_width:
            lines.append((cur, cw)); cur, cw = [], 0
        cw += (gap if cur else 0) + w
        cur.append(o)
    lines.append((cur, cw))
    lh = size * 1.1
    top = y + (len(lines) - 1) * lh / 2
    for li, (ln, width) in enumerate(lines):
        x = -width / 2
        for o in ln:
            o.location = (x, top - li * lh, 1)
            x += o.dimensions.x + gap
    for i, o in enumerate(words):
        entrance(o, start + i * per, rise=0.3, scale_from=1.0, spring="snappy")
    return words

def breathe(obj, amp=0.015, period_frames=22, float_amp=0.03):
    """Idle micro-motion via drivers (scale sine + Y float). Safe with keyframes
    only if the object has no scale/location keys — else parent to an Empty."""
    for i in range(2):
        fc = obj.driver_add("scale", i)
        base = obj.scale[i]
        fc.driver.expression = f"{base}*(1+sin(frame/{period_frames})*{amp})"
    fc = obj.driver_add("location", 1)
    fc.driver.expression = f"{obj.location.y}+sin(frame/30)*{float_amp}"

def holder(obj, name=None):
    """Wrap obj in an Empty so entrance keys (on obj) and breathe (on empty) stack."""
    e = bpy.data.objects.new(name or "H_" + obj.name, None)
    sc().collection.objects.link(e)
    e.location = obj.location.copy()
    obj.parent = e
    obj.location = (0, 0, 0)
    return e

def ken_burns(obj, start, end, zoom_to=1.08, pan=-0.25, zoom_in=True):
    s0, s1 = (1.0, zoom_to) if zoom_in else (zoom_to, 1.0)
    x = obj.location.x
    for i in range(2):
        key_ease(obj, "scale", start, s0, "inOut", index=i)
        key_ease(obj, "scale", end, s1, "inOut", index=i)
    key_ease(obj, "location", start, x, "inOut", index=0)
    key_ease(obj, "location", end, x + pan, "inOut", index=0)

def ken_burns_strip(strip, start, end, zoom_to=1.08, pan_px=-25, zoom_in=True):
    t = strip.transform
    s0, s1 = (1.0, zoom_to) if zoom_in else (zoom_to, 1.0)
    for f, v in ((start, s0), (end, s1)):
        for p in ("scale_x", "scale_y"):
            key_ease(t, p, f, v, "inOut")
    key_ease(t, "offset_x", start, 0, "inOut")
    key_ease(t, "offset_x", end, pan_px, "inOut")

def bg_mesh():
    """Never a flat background: base plane + two soft drifting color blobs."""
    cw, ch = canvas()
    add_plane(cw * 1.2, ch * 1.2, (0, 0, -1), "bg", name="BG_Base")
    blobs = []
    for nm, col, a, size, pos, div, amp in (
            ("BG_Blob1", "primary", 0.20, 12, (-3, ch * 0.3), 55, 0.5),
            ("BG_Blob2", "accent", 0.13, 9, (2.5, -ch * 0.3), 70, 0.4)):
        ob = add_plane(size, size, (*pos, -0.9), col, name=nm)
        nt = ob.active_material.node_tree
        grad = nt.nodes.new("ShaderNodeTexGradient")
        grad.gradient_type = "SPHERICAL"
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        nt.links.new(tc.outputs["Object"], mp.inputs[0])
        # Object coords span ±size/2 -> normalise to ±1 (sphere radius 1)
        mp.inputs["Scale"].default_value = (2 / size, 2 / size, 1)
        nt.links.new(mp.outputs[0], grad.inputs[0])
        pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"
        pw.inputs[1].default_value = 2.2  # soft falloff
        nt.links.new(grad.outputs["Fac"], pw.inputs[0])
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = a
        nt.links.new(pw.outputs[0], mul.inputs[0])
        nt.links.new(mul.outputs[0], nt.nodes["Alpha"].inputs[0])
        d = ob.driver_add("location", 0).driver
        d.expression = f"{pos[0]}+sin(frame/{div})*{amp}"
        blobs.append(ob)
    return blobs

def counter(obj, start, end, target, fmt="{:.1f}%"):
    """Animated number on a text object (frame_change handler, EXPO ease-out)."""
    def _upd(scene, *_):
        f = scene.frame_current
        t = min(max((f - start) / max(end - start, 1), 0), 1)
        e = 1 - 2 ** (-10 * t) if t < 1 else 1
        obj.data.body = fmt.format(target * e)
    _upd.__name__ = "mg_counter_" + obj.name
    bpy.app.handlers.frame_change_pre[:] = [h for h in bpy.app.handlers.frame_change_pre
                                            if getattr(h, "__name__", "") != _upd.__name__]
    bpy.app.handlers.frame_change_pre.append(_upd)

def spark(start, rays=12, size=3.0, loc=(0, 0, 1)):
    """Radial logo mark: staggered rays growing from center, container spins in."""
    root = bpy.data.objects.new("Spark", None)
    sc().collection.objects.link(root)
    root.location = loc
    for i in range(rays):
        r = add_plane(size * 0.085, size * 0.46, (0, 0, 0), "primary", name=f"Ray{i}")
        r.data.transform(mathutils.Matrix.Translation((0, size * 0.3, 0)))  # pivot at base
        r.parent = root
        r.rotation_euler.z = math.tau * i / rays
        f = start + round(i * 1.2)
        key_ease(r, "scale", f, 0.0, "out", index=1)
        key_ease(r, "scale", f + sec(0.5), 1.0, "snappy", index=1)
    key_ease(root, "rotation_euler", start, math.radians(-120), "out", index=2)
    key_ease(root, "rotation_euler", start + sec(1.0), 0.0, "smooth", index=2)
    for i in range(3):
        key_ease(root, "scale", start, 0.3, "out", index=i)
        key_ease(root, "scale", start + sec(0.8), 1.0, "bouncy", index=i)
    return root

def parallax(layers, start, end, travel=-1.2):
    """layers: [(obj, factor)], e.g. bg 0.3, mid 0.6, fg 1.0."""
    for ob, k in layers:
        x = ob.location.x
        key_ease(ob, "location", start, x, "inOut", index=0)
        key_ease(ob, "location", end, x + travel * k, "inOut", index=0)

# ------------------------------------------------ grade / grain / vignette -
def _comp_tree():
    s = sc()
    if hasattr(s, "compositing_node_group"):  # Blender 5.x
        tree = s.compositing_node_group or bpy.data.node_groups.new("MG_Comp", "CompositorNodeTree")
        s.compositing_node_group = tree
        if not any(i.name == "Image" for i in tree.interface.items_tree):
            tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        tree.nodes.clear()
        out = tree.nodes.new("NodeGroupOutput")
        return tree, out, out.inputs[0]
    s.use_nodes = True
    tree = s.node_tree
    tree.nodes.clear()
    out = tree.nodes.new("CompositorNodeComposite")
    return tree, out, out.inputs["Image"]

def setup_compositor(grade=0.18, glow=True, grain=0.05, vignette=0.22):
    """Render Layers -> tint grade (Color Balance toward hero) -> bloom on hero
    -> film grain -> vignette -> output. Visible in viewport Rendered mode when
    the viewport compositor is enabled (Shading > Compositor: Always)."""
    tree, out, out_in = _comp_tree()
    N, L = tree.nodes.new, tree.links.new
    rl = N("CompositorNodeRLayers")
    cur = rl.outputs["Image"]
    try:  # grade: lift shadows toward hero hue, warm/cool gain
        cb = N("CompositorNodeColorBalance")
        p = C("primary")
        k = grade
        cb.lift = (1 - k * 0.5 + p[0] * k * 0.5, 1 - k * 0.5 + p[1] * k * 0.5, 1 - k * 0.5 + p[2] * k * 0.5)
        L(cur, cb.inputs["Image"]); cur = cb.outputs["Image"]
    except Exception as e:
        print("grade skipped:", e)
    if glow:
        try:
            gl = N("CompositorNodeGlare")
            for gt in ("BLOOM", "FOG_GLOW"):
                try:
                    gl.glare_type = gt; break
                except TypeError:
                    pass
            L(cur, gl.inputs["Image"]); cur = gl.outputs["Image"]
        except Exception as e:
            print("glow skipped:", e)
    tree.links.new(cur, out_in)
    # grain + vignette as camera-parented overlay planes (version-proof, and they
    # show up in viewport screenshots used for verification)
    camera_overlays(grain, vignette)

def camera_overlays(grain=0.05, vignette=0.22):
    cam = sc().camera
    cw, ch = canvas()
    for nm in ("FX_Grain", "FX_Vignette"):
        if nm in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[nm])
    # vignette: radial alpha, black
    v = add_plane(cw * 1.01, ch * 1.01, (0, 0, 0), "bg", name="FX_Vignette")
    nt = v.active_material.node_tree
    nt.nodes["Emit"].inputs["Color"].default_value = (0, 0, 0, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    # elliptical distance: sqrt((x/(w/2))^2 + (y/(h/2))^2)
    def m(op, a=None, b=None):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = op
        for i, val in enumerate((a, b)):
            if isinstance(val, (int, float)):
                n.inputs[i].default_value = val
            elif val is not None:
                nt.links.new(val, n.inputs[i])
        return n.outputs[0]
    dx = m("MULTIPLY", sep.outputs[0], 2 / cw)
    dy = m("MULTIPLY", sep.outputs[1], 2 / ch)
    d = m("SQRT", m("ADD", m("MULTIPLY", dx, dx), m("MULTIPLY", dy, dy)))
    ramp = m("MULTIPLY", m("MAXIMUM", m("SUBTRACT", d, 0.56), 0.0), 1 / 0.85)  # clear centre
    nt.links.new(m("MULTIPLY", m("MINIMUM", ramp, 1.0), vignette), nt.nodes["Alpha"].inputs[0])
    # grain: animated noise, low alpha
    g = add_plane(cw * 1.01, ch * 1.01, (0, 0, 0), "bg", name="FX_Grain")
    nt = g.active_material.node_tree
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = 900.0
    nz.inputs["Detail"].default_value = 2.0
    drv = nz.inputs["W"].driver_add("default_value").driver
    drv.expression = "frame*7.13"
    nt.links.new(nz.outputs["Fac"], nt.nodes["Emit"].inputs["Color"])
    nt.nodes["Alpha"].inputs[0].default_value = grain * 2  # mid-grey noise, faint
    for ob, z in ((v, -0.5), (g, -0.6)):  # in front of everything, behind lens
        ob.parent = cam
        ob.location = (0, 0, z)
        ob.hide_select = True
    return v, g

# --------------------------------------------------------------- VSE -------
def _se():
    s = sc()
    return s.sequence_editor or s.sequence_editor_create()

def add_footage(path, channel=1, frame=1, fit_scene=True):
    se = _se()
    st = _strips(se).new_movie("Footage", path, channel, frame)
    if fit_scene:
        sc().frame_end = st.frame_final_end - 1
    return st

def add_sfx(path, frame_hit, volume=0.7, channel=6, lead=3):
    """SFX starts `lead` frames BEFORE the visual hit (early feels synced)."""
    st = _strips(_se()).new_sound("SFX", path, channel, max(1, frame_hit - lead))
    st.volume = volume
    return st

def add_music(path, volume=0.25, channel=8):
    st = _strips(_se()).new_sound("Music", path, channel, 1)
    st.volume = volume
    return st

def frames_per_beat(bpm):
    r = sc().render
    return r.fps / r.fps_base * 60 / bpm

# ---------------------------------------------------------- captions -------
def captions(words, y=None, size=0.95, per_page=3, gap_px=24):
    """words: [{'word': str, 'start': s, 'end': s}] (Whisper word timestamps).
    Builds 2–4 word pages at ~65% height; active word flips to primary."""
    cw, ch = canvas()
    y = ch * (0.5 - 0.65) if y is None else y
    pages = [words[i:i + per_page] for i in range(0, len(words), per_page)]
    objs = []
    for pg in pages:
        f0, f1 = sec(pg[0]["start"]) + 1, sec(pg[-1]["end"]) + 1
        made = []
        for w in pg:
            o = add_text(w["word"].strip().upper(), size, "text", align="LEFT",
                         loc=(0, y, 2), name="C_" + w["word"].strip())
            made.append(o)
        bpy.context.view_layer.update()
        gap = gap_px / 100
        total = sum(o.dimensions.x for o in made) + gap * (len(made) - 1)
        x = -total / 2
        for o, w in zip(made, pg):
            o.location.x = x
            x += o.dimensions.x + gap
            em = o.active_material.node_tree
            path = 'nodes["Emit"].inputs[0].default_value'
            ws, we = sec(w["start"]) + 1, sec(w["end"]) + 1
            for f, col in ((ws - 2, "text"), (ws, "primary"), (we, "primary"), (we + 2, "text")):
                for i in range(3):
                    key_ease(em, path, f, C(col)[i], "out", index=i)
        for o in made:
            key_alpha(o, f0 - 1, 0.0); key_alpha(o, f0 + 3, 1.0)
            key_alpha(o, f1, 1.0, "in"); key_alpha(o, f1 + 2, 0.0, "in")
            key_ease(o, "location", f0 - 1, y - 0.2, "out", index=1)
            key_ease(o, "location", f0 + 4, y, "snappy", index=1)
        objs += made
    return objs

# ------------------------------------------------------------ render ------
def final_render(path="//out/video.mp4", crf="HIGH", samples=24):
    s = sc()
    r = s.render
    r.filepath = path
    ims = r.image_settings
    if hasattr(ims, "media_type"):
        ims.media_type = "VIDEO"
    ims.file_format = "FFMPEG"
    r.ffmpeg.format = "MPEG4"
    r.ffmpeg.codec = "H264"
    r.ffmpeg.constant_rate_factor = crf
    r.ffmpeg.ffmpeg_preset = "GOOD"
    r.ffmpeg.audio_codec = "AAC"
    r.ffmpeg.audio_bitrate = 192
    try:
        s.eevee.taa_render_samples = samples
    except AttributeError:
        pass
    leftovers = audit_linear()
    if leftovers:
        print("WARNING linear keys:", leftovers[:10])
    bpy.ops.render.render(animation=True)
