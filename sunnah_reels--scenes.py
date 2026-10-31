"""Stick-figure scene templates. All coordinates are 1x px on a 720x1280 frame.
Lines are drawn on a 2x supersampled layer; glows are drawn on the base image."""
import math, random
import numpy as np
from PIL import Image, ImageDraw

W, H, GROUND = 720, 1280, 820
L_Y0, L_Y1, K = 150, 1100, 2          # supersampled layer window (y range) and factor

PALETTES = {
    "night": dict(top=(7, 9, 20), bot=(3, 4, 9), glow=(255, 190, 90), fig=(240, 232, 220), dim=(120, 120, 130), moon=True),
    "dawn": dict(top=(26, 22, 34), bot=(14, 11, 14), glow=(255, 160, 80), fig=(245, 235, 220), dim=(130, 120, 120), moon=False),
    "warm": dict(top=(34, 24, 16), bot=(17, 13, 10), glow=(255, 190, 80), fig=(30, 22, 16), dim=(90, 70, 40), moon=False),
}
THEME_PALETTE = {"food": "warm", "family": "warm", "home": "warm", "fasting": "dawn"}

ease = lambda x: x * x * (3 - 2 * x)
clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
lerp = lambda a, b, t: a + (b - a) * t
def seg(u, a, b): return ease(clamp((u - a) / (b - a)))


def P(*xy): return tuple(xy)
POSES = {
    "stand": dict(head=P(0, -162), sh=P(0, -140), hip=P(0, -70), kl=P(-6, -35), fl=P(-9, 0), kr=P(6, -35), fr=P(9, 0), hl=P(-10, -85), hr=P(10, -85)),
    "sujood": dict(head=P(52, -16), sh=P(18, -26), hip=P(-34, -46), kl=P(-62, -12), fl=P(-92, -4), kr=P(-62, -12), fr=P(-92, -4), hl=P(48, -4), hr=P(38, -4)),
    "dua": dict(head=P(0, -162), sh=P(0, -140), hip=P(0, -70), kl=P(-6, -35), fl=P(-9, 0), kr=P(6, -35), fr=P(9, 0), hl=P(26, -150), hr=P(32, -158)),
    "reach": dict(head=P(0, -162), sh=P(0, -140), hip=P(0, -70), kl=P(-6, -35), fl=P(-9, 0), kr=P(6, -35), fr=P(9, 0), hl=P(-10, -85), hr=P(52, -128)),
    "lying": dict(head=P(-78, -16), sh=P(-56, -14), hip=P(30, -12), kl=P(62, -34), fl=P(96, -10), kr=P(62, -24), fr=P(98, -8), hl=P(-30, -8), hr=P(-40, -12)),
    "sit": dict(head=P(0, -108), sh=P(0, -88), hip=P(0, -14), kl=P(-34, -10), fl=P(-8, -2), kr=P(34, -10), fr=P(8, -2), hl=P(-14, -40), hr=P(36, -42)),
    "bend": dict(head=P(46, -92), sh=P(30, -102), hip=P(-6, -70), kl=P(-8, -35), fl=P(-9, 0), kr=P(4, -35), fr=P(9, 0), hl=P(60, -52), hr=P(66, -44)),
}
def walk_pose(ph):
    s, c = math.sin(ph), math.cos(ph)
    p = dict(POSES["stand"])
    p.update(fl=P(26 * s, -max(0, -c) * 10), kl=P(13 * s, -36), fr=P(-26 * s, -max(0, c) * 10), kr=P(-13 * s, -36),
             hl=P(-22 * s, -88), hr=P(22 * s, -88))
    return p
def mix(a, b, t): return {k: P(lerp(a[k][0], b[k][0], t), lerp(a[k][1], b[k][1], t)) for k in a}


class Ctx:
    def __init__(self, base, pal, t):
        self.base, self.pal, self.t = base, pal, t
        self.layer = Image.new("RGBA", (W * K, (L_Y1 - L_Y0) * K), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.layer)
        self.bd = ImageDraw.Draw(base)
    def pt(self, x, y): return (x * K, (y - L_Y0) * K)
    def line(self, pts, w, col):
        q = [self.pt(*p) for p in pts]
        self.d.line(q, fill=col, width=int(w * K), joint="curve")
        for p in (q[0], q[-1]): r = w * K / 2; self.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
    def circ(self, c, r, fill=None, outline=None, w=2):
        x, y = self.pt(*c); r *= K
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline, width=int(w * K))
    def rect(self, x0, y0, x1, y1, fill, outline=None, w=2):
        a, b = self.pt(x0, y0), self.pt(x1, y1); self.d.rectangle([*a, *b], fill=fill, outline=outline, width=int(w * K))
    def poly(self, pts, fill): self.d.polygon([self.pt(*p) for p in pts], fill=fill)
    def glow(self, c, r, col, a=0.5):
        r = int(max(r, 4)); n = r * 2
        yy, xx = np.mgrid[-r:r, -r:r]; m = np.clip(1 - np.sqrt(xx ** 2 + yy ** 2) / r, 0, 1) ** 2 * a
        x0, y0 = int(c[0] - r), int(c[1] - r)
        box = self.base.crop((x0, y0, x0 + n, y0 + n)) if False else None
        src = np.asarray(self.base.crop((max(x0, 0), max(y0, 0), min(x0 + n, W), min(y0 + n, H)))).astype(float)
        if src.size == 0: return
        ox, oy = max(-x0, 0), max(-y0, 0)
        mm = m[oy:oy + src.shape[0], ox:ox + src.shape[1], None]
        out = src * (1 - mm) + np.array(col, float) * mm
        self.base.paste(Image.fromarray(out.astype("uint8")), (max(x0, 0), max(y0, 0)))
    def text(self, xy, s, fnt, col, anchor="mm"): self.bd.text(xy, s, font=fnt, fill=col, anchor=anchor)

    def figure(self, x, pose, col=None, flip=False, s=1.0, gy=GROUND, w=8):
        col = col or self.pal["fig"]
        f = lambda p: (x + (-p[0] if flip else p[0]) * s, gy + p[1] * s)
        j = {k: f(v) for k, v in pose.items()}
        self.line([j["sh"], j["hip"]], w, col)
        self.line([j["hip"], j["kl"], j["fl"]], w - 1, col); self.line([j["hip"], j["kr"], j["fr"]], w - 1, col)
        self.line([j["sh"], j["hl"]], w - 2, col); self.line([j["sh"], j["hr"]], w - 2, col)
        self.circ(j["head"], 17 * s, fill=col)
        return j
    def ground(self, col=None):
        self.line([(0, GROUND), (W, GROUND)], 2, col or tuple(int(c * .35) for c in self.pal["fig"]))
    def finish(self):
        small = self.layer.resize((W, L_Y1 - L_Y0), Image.LANCZOS)
        self.base.paste(small, (0, L_Y0), small)


def background(pal, t, stars):
    top, bot = np.array(pal["top"], float), np.array(pal["bot"], float)
    g = np.linspace(0, 1, H)[:, None, None]
    arr = (top * (1 - g) + bot * g) * np.ones((H, W, 3))
    img = Image.fromarray(arr.astype("uint8"))
    px = img.load()
    for (x, y, b, ph) in stars:
        v = int(b * (0.6 + 0.4 * math.sin(t * 1.5 + ph)))
        px[x, y] = (v, v, v + 10 if v < 245 else v)
    return img

def make_stars(seed):
    r = random.Random(seed)
    return [(r.randrange(W), r.randrange(0, 700), r.randrange(90, 200), r.random() * 6) for _ in range(90)]

def moon(c, pos=(600, 280)):
    c.glow(pos, 90, (150, 160, 200), .35)
    c.circ(pos, 22, fill=(235, 225, 200)); c.circ((pos[0] + 9, pos[1] - 4), 20, fill=c.pal["top"] if pos[1] < 700 else (10, 10, 20))

# ---------------------------------------------------------------- templates
def t_walk_light(c, u, i, n):
    gx = 600; c.glow((gx, GROUND - 120), lerp(60, 330, seg(u, .1, .9)), c.pal["glow"], .55)
    c.ground(); c.line([(gx, GROUND), (gx, GROUND - 150)], 5, c.pal["dim"]); c.circ((gx, GROUND - 158), 9, fill=c.pal["glow"])
    x = lerp(90, 430, seg(u, 0, .85)); moving = u < .85
    c.figure(x, walk_pose(u * 38) if moving else POSES["stand"])

def t_counter(c, u, i, n):
    c.ground(); c.glow((360, GROUND - 90), lerp(40, 220, u), c.pal["glow"], .35)
    c.figure(300, POSES["stand"])
    good = int(10 + u * 40); gl = c.pal["glow"]
    f = __import__("sunnah_reels.text", fromlist=["font"]).font
    c.text((200, 960), "GOOD DEEDS", f("mono", 20), tuple(int(v * .8) for v in gl)); c.text((520, 960), "BAD DEEDS", f("mono", 20), c.pal["dim"])
    c.text((200, 1020), str(good), f("latin", 70), (250, 225, 160)); c.text((520, 1020), "0", f("latin", 70), (190, 190, 190))

def t_meet(c, u, i, n):
    c.ground(); m = seg(u, 0, .45)
    ax, bx = lerp(90, 290, m), lerp(630, 430, m)
    wa = walk_pose(u * 40) if m < 1 else POSES["stand"]
    c.glow((360, GROUND - 120), lerp(0, 260, seg(u, .45, .9)), c.pal["glow"], .6)
    c.figure(ax, wa); c.figure(bx, walk_pose(u * 40 + 1.5) if m < 1 else POSES["stand"], flip=True, col=tuple(int(v * .8) for v in c.pal["fig"]))
    for k in range(10):
        a = seg(u, .5, 1) * ((k * .17 + u * 2) % 1)
        if a > 0: c.circ((360 + math.sin(k * 2.1) * 60, GROUND - 120 - a * 230), 3, fill=c.pal["glow"])

def t_prayer(c, u, i, n):
    c.ground(); mx = 540
    c.glow((mx, GROUND - 90), lerp(80, 300, seg(u, .2, .9)), c.pal["glow"], .5)
    c.rect(mx - 70, GROUND - 90, mx + 70, GROUND, (26, 26, 34), outline=(55, 55, 66))
    c.poly([(mx - 70, GROUND - 90), (mx - 50, GROUND - 140), (mx, GROUND - 165), (mx + 50, GROUND - 140), (mx + 70, GROUND - 90)], (26, 26, 34))
    c.rect(mx - 14, GROUND - 70, mx + 14, GROUND - 20, c.pal["glow"]); c.circ((mx, GROUND - 178), 8, outline=c.pal["glow"], w=2)
    p = mix(POSES["stand"], POSES["dua"], seg(u, .1, .3)); p = mix(p, POSES["sujood"], seg(u, .5, .75))
    c.figure(250, p)

def t_home(c, u, i, n):
    c.ground(); hx = 500; lit = seg(u, .45, .8)
    c.glow((hx, GROUND - 100), lerp(60, 300, lit), c.pal["glow"], .55)
    c.rect(hx - 90, GROUND - 130, hx + 90, GROUND, (44, 32, 24), outline=(90, 66, 40))
    c.poly([(hx - 110, GROUND - 130), (hx, GROUND - 200), (hx + 110, GROUND - 130)], (60, 42, 30))
    c.rect(hx - 60, GROUND - 100, hx - 20, GROUND - 60, c.pal["glow"]); c.rect(hx + 10, GROUND - 90, hx + 40, GROUND, (20, 14, 10))
    x = lerp(90, hx + 20, seg(u, 0, .6))
    if u < .62: c.figure(x, walk_pose(u * 36), col=(235, 220, 200))
    else: c.figure(hx + 20, POSES["stand"], col=(235, 220, 200), s=lerp(1, .0, seg(u, .62, .75)) if False else 1)
    if u >= .62: c.rect(hx + 10, GROUND - 90, hx + 40, GROUND, c.pal["glow"])

def t_give(c, u, i, n):
    c.ground(); m = seg(u, .15, .55); orb = (lerp(300, 420, m), GROUND - 128)
    c.figure(250, mix(POSES["stand"], POSES["reach"], seg(u, .05, .25)), col=(235, 220, 200))
    c.figure(470, POSES["stand"], flip=True, col=(200, 190, 175))
    c.glow(orb, 70, c.pal["glow"], .7); c.circ(orb, 10, fill=(255, 235, 170))
    for k in range(9):
        a = seg(u, .55, 1) * ((k * .13 + u) % 1)
        if a > 0: c.glow((470 + (k - 4) * 28, GROUND - 160 - a * 200), 26, c.pal["glow"], .6)

def t_sleep(c, u, i, n):
    c.ground(); c.glow((600, 300), 160, (150, 160, 210), .3); moon(c, (600, 300))
    c.rect(120, GROUND - 22, 440, GROUND, (40, 40, 56)); c.figure(280, POSES["lying"], gy=GROUND - 22, col=(225, 218, 205))
    for k in range(3):
        a = ((u * 2 + k * .33) % 1); c.text((420 + k * 26, GROUND - 90 - a * 150), "z", __import__("sunnah_reels.text", fromlist=["font"]).font("latin", 36 - k * 6), tuple(int(v * (1 - a)) for v in (200, 200, 230)))

def t_meal(c, u, i, n):
    c.ground(); c.glow((420, GROUND - 40), lerp(80, 260, seg(u, 0, .6)), c.pal["glow"], .5)
    c.rect(220, GROUND - 6, 560, GROUND, (80, 56, 34))
    c.circ((420, GROUND - 14), 34, fill=None, outline=(150, 110, 60), w=3)
    p = mix(POSES["sit"], dict(POSES["sit"], hr=P(70, -22)), (math.sin(u * 12) + 1) / 2)
    c.figure(300, p, col=(235, 215, 190))

def t_tree(c, u, i, n):
    c.ground(); g = seg(u, .2, .95); h = lerp(10, 260, g); x = 470
    c.glow((x, GROUND - h), lerp(40, 260, g), c.pal["glow"], .35)
    c.line([(x, GROUND), (x, GROUND - h)], lerp(4, 11, g), (110, 78, 48))
    for k, (dx, dy, r) in enumerate([(-30, .75, 34), (32, .85, 40), (0, 1.0, 50), (-40, .95, 30), (44, .7, 28)]):
        if g > .25: c.circ((x + dx, GROUND - h * dy), r * g, fill=(50, 120, 70))
    c.figure(300, mix(POSES["stand"], POSES["bend"], 1 - seg(u, .25, .5)))

def t_ask(c, u, i, n):
    """Series 'qa': a man walks up to the Prophet's companion-figure and asks; last beat = answer glow."""
    from .text import font
    c.ground(); ax = lerp(90, 300, seg(u, 0, .22)); walking = u < .22
    c.figure(ax, walk_pose(u * 60) if walking else POSES["stand"])
    c.figure(480, POSES["stand"], flip=True, col=(255, 240, 200))
    if i >= 1: c.text((ax, GROUND - 215 - 6 * math.sin(u * 30)), "?", font("latin", 64), c.pal["glow"])
    if i >= n - 1: c.glow((480, GROUND - 120), 200 + 20 * math.sin(u * 20), c.pal["glow"], .45)

VERDICT_COL = dict(sahih=(70, 170, 100), hasan=(232, 190, 110), weak=(205, 70, 60))
def t_myth(c, u, i, n):
    """Series 'myth': a scroll with a '?' that turns into a verdict stamp on the last beat."""
    from .text import font
    c.ground(); c.figure(130, POSES["reach"])
    c.rect(230, 380, 510, 680, (74, 58, 40), outline=(200, 170, 110), w=4)
    for k in range(5): c.line([(262, 430 + k * 50), (478, 430 + k * 50)], 3, (120, 100, 70))
    v = getattr(c, "idea", {}).get("verdict", "sahih"); col = VERDICT_COL[v]
    if i < n - 1:
        c.text((370, 320 - 6 * math.sin(u * 30)), "?", font("latin", 70), c.pal["glow"])
    else:
        r = 70 * (1 + .12 * math.sin(u * 25)); cx, cy = 370, 530
        c.circ((cx, cy), r, outline=col, w=10)
        if v == "weak": c.line([(cx - 34, cy - 34), (cx + 34, cy + 34)], 12, col); c.line([(cx + 34, cy - 34), (cx - 34, cy + 34)], 12, col)
        else: c.line([(cx - 36, cy + 2), (cx - 8, cy + 30), (cx + 40, cy - 30)], 12, col)
        c.glow((cx, cy), 220, col, .25)

TEMPLATES = dict(ask=t_ask, myth=t_myth, walk_light=t_walk_light, counter=t_counter, meet=t_meet, prayer=t_prayer, home=t_home,
                 give=t_give, sleep=t_sleep, meal=t_meal, tree=t_tree)
