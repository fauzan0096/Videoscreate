"""Timeline + frame compositor + ffmpeg pipe."""
import os, subprocess, math
import numpy as np
from PIL import Image, ImageDraw
from . import scenes as S
from .text import font, wrap, shape_ar, draw_mixed

W, H = S.W, S.H
GOLD, WHITE, DIM = (232, 190, 110), (240, 236, 228), (150, 140, 120)
CTA = "Send this to someone who needs it."


def build_timeline(idea, fps, target=None):
    beats = []
    for ln in idea["lines"]:
        gold = ln.startswith("^")
        txt = ln.lstrip("^")
        beats.append(dict(text=txt, gold=gold, dur=max(2.6, 0.38 * len(txt.split()) + 1.0)))
    cap_total = sum(b["dur"] for b in beats)
    quote = 3.0 + 0.42 * len(idea["quote_en"].split()) + 1.5
    target = target or idea.get("target")
    if target:                                   # stretch holds so the reel lands on the target length (30-60 s)
        k = max(1.0, (min(target, 60) - 2.6) / (cap_total + quote))
        for b in beats: b["dur"] *= k
        cap_total *= k; quote *= k
    return dict(beats=beats, cap=cap_total, quote=quote, cta=2.6, total=cap_total + quote + 2.6)


def fade(t, a, b, fi=0.5, fo=0.5):
    return S.clamp(min((t - a) / fi, (b - t) / fo, 1.0))


def draw_text_block(layer, lines, fnt, y, color, alpha, arabic=False, lh=1.25, maxw=600):
    if alpha <= 0: return y
    d = ImageDraw.Draw(layer)
    col = (*color, int(255 * alpha))
    for ln in lines:
        s, kw = shape_ar(ln) if arabic else (ln, {})
        if arabic: d.text((W / 2, y), s, font=fnt, fill=col, anchor="ma", **kw)
        else: draw_mixed(d, (W / 2, y), s, fnt, col, "ma")
        y += int(fnt.size * lh)
    return y


class Renderer:
    def __init__(self, idea, fps=30, draft=False, target=None):
        self.idea, self.fps, self.draft = idea, fps, draft
        self.tl = build_timeline(idea, fps, target)
        self.pal = dict(S.PALETTES[S.THEME_PALETTE.get(idea.get("theme"), "night")])
        self.stars = S.make_stars(idea["id"])
        self.tpl = S.TEMPLATES[idea["template"]]
        d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        self.ar_lines = wrap(d, idea["arabic"], font("arabic", 54), 600, arabic=True) if idea.get("arabic") else []
        self.en_lines = wrap(d, "“" + idea["quote_en"] + "”", font("latin", 38), 580)
        self.cta_lines = wrap(d, CTA, font("latin", 44), 560)

    @property
    def frames(self): return int(self.tl["total"] * self.fps)

    def frame(self, n):
        t = n / self.fps; tl = self.tl; cap, q = tl["cap"], tl["quote"]
        base = S.background(self.pal, t, self.stars)
        if self.pal["moon"] and self.idea["template"] != "sleep":
            c0 = S.Ctx(base, self.pal, t); S.moon(c0, (610, 250)); c0.finish()
        u = S.clamp(t / (cap + q)); c = S.Ctx(base, self.pal, t)
        beat_i, acc = 0, 0
        for k, b in enumerate(tl["beats"]):
            if t >= acc: beat_i = k
            acc += b["dur"]
        c.idea = self.idea; c.cap = cap; self.tpl(c, u, beat_i, len(tl["beats"])); c.finish()
        text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        acc = 0
        for b in tl["beats"]:                                    # caption beats
            a = fade(t, acc, acc + b["dur"], .5, .45)
            if a > 0: draw_text_block(text, wrap(ImageDraw.Draw(text), b["text"], font("latin", 52), 580), font("latin", 52), 150, GOLD if b["gold"] else WHITE, a)
            acc += b["dur"]
        if cap <= t < cap + q:                                   # hadith card
            veil = Image.new("RGBA", (W, H), (0, 0, 0, int(170 * fade(t, cap, cap + q, .6, .5))))
            base.paste(veil, (0, 0), veil)
            a1 = fade(t, cap + .3, cap + q, .8, .5); a2 = fade(t, cap + 1.6, cap + q, .8, .5); a3 = fade(t, cap + 2.4, cap + q, .8, .5)
            y = 230
            if self.ar_lines: y = draw_text_block(text, self.ar_lines, font("arabic", 54), y, GOLD, a1, arabic=True, lh=1.5) + 30
            y = draw_text_block(text, self.en_lines, font("latin", 38), y, WHITE, a2 if self.ar_lines else a1)
            draw_text_block(text, [self.idea["ref"]], font("latin", 28), y + 20, GOLD, a3)
        if t >= cap + q:                                         # CTA
            a = fade(t, cap + q, tl["total"] + .5, .6, 1)
            draw_text_block(text, self.cta_lines, font("latin", 44), 520, WHITE, a)
        if self.draft:
            ImageDraw.Draw(text).text((W / 2, 1200), "DRAFT · UNVERIFIED SOURCE", font=font("mono", 22), fill=(255, 90, 90, 220), anchor="mm")
        out = base.convert("RGBA"); out.alpha_composite(text)
        return out.convert("RGB")

    def render(self, path, music=None, progress=True):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(self.fps), "-i", "-"]
        dur = self.tl["total"]
        if music: cmd += ["-stream_loop", "-1", "-i", music, "-af", f"afade=t=in:d=1,afade=t=out:st={dur-1.5:.2f}:d=1.5,volume=0.5"]
        else: cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "fast", "-c:a", "aac", "-b:a", "128k", "-t", f"{dur:.2f}", "-movflags", "+faststart", path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for n in range(self.frames):
            p.stdin.write(self.frame(n).tobytes())
            if progress and n % 60 == 0: print(f"\r  frame {n}/{self.frames}", end="", flush=True)
        p.stdin.close(); p.wait(); print()
        return path
