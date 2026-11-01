# theme.py — single source of truth for every Blender motion-graphics project.
# NEVER inline colors, easings or timings in scene code.

def hex_rgba(h, a=1.0):
    """'#RRGGBB' -> linear RGBA tuple for Blender materials."""
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)

theme = {
    "colors": {  # adjust to the user's brand. Default: dark tech
        "bg": "#0A0A0F",
        "bgAlt": "#12121A",
        "primary": "#7C3AED",  # THE hero color — max one element per frame
        "accent": "#22D3EE",
        "text": "#F4F4F5",
        "textDim": "#A1A1AA",
    },
    "fonts": {  # .ttf paths; load with load_font()
        "display": "",  # e.g. C:/Windows/Fonts/ClashDisplay-Semibold.ttf
        "body": "",
    },
    # (interpolation, easing) pairs. LINEAR is forbidden.
    "ease": {
        "out": ("EXPO", "EASE_OUT"),     # entrances
        "inOut": ("QUINT", "EASE_IN_OUT"),  # moves, Ken Burns
        "in": ("EXPO", "EASE_IN"),       # exits only
    },
    # spring-like presets (Blender BACK/ELASTIC). Never on alpha.
    "spring": {
        "snappy": ("BACK", "EASE_OUT", 1.2),   # words, UI pops (back = overshoot)
        "smooth": ("EXPO", "EASE_OUT", None),  # big elements
        "bouncy": ("ELASTIC", "EASE_OUT", None),  # logos, playful accents
    },
    "timing": {  # seconds
        "enter": 0.66, "exit": 0.33, "stagger_word": 0.1,
        "stagger_card": 0.15, "hold": 0.6,
    },
}
