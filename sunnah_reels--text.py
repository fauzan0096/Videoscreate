"""Fonts, Arabic shaping and text wrapping."""
import os
from PIL import ImageFont, features

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(HERE, "assets", "fonts")
HAS_RAQM = features.check("raqm")

LATIN = ["EBGaramond-Regular.ttf", "EBGaramond12-Regular.ttf", "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
ARABIC = ["Amiri-Regular.ttf", "ScheherazadeNew-Regular.ttf", "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
MONO = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
_cache = {}


def _find(names):
    for n in names:
        p = n if os.path.isabs(n) else os.path.join(FONT_DIR, n)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("No usable font; put Amiri-Regular.ttf and EBGaramond-Regular.ttf in assets/fonts/")


def font(kind, size):
    key = (kind, size)
    if key not in _cache:
        path = _find({"latin": LATIN, "arabic": ARABIC, "mono": MONO}[kind])
        _cache[key] = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM if HAS_RAQM else ImageFont.Layout.BASIC)
    return _cache[key]


def shape_ar(s):
    """Return (text, kwargs) ready for ImageDraw.text for an Arabic string."""
    if HAS_RAQM:
        return s, dict(direction="rtl", language="ar")
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(s)), {}
    except ImportError:
        raise RuntimeError("Arabic needs libraqm, or: pip install arabic-reshaper python-bidi")


def wrap(draw, text, fnt, maxw, arabic=False):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        s, kw = shape_ar(t) if arabic else (t, {})
        if draw.textlength(s, font=fnt, **kw) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
