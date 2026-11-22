"""Flat geometric adult characters drawn in code, so every limb, brow, blink and mouth can be animated.
Character(...).render(pose, height) -> RGBA cutout with feet at the bottom centre."""
import math
from dataclasses import dataclass
from PIL import Image, ImageDraw

CW, CH, FX, FY = 1200, 1400, 600, 1360  # local canvas, feet origin; body is ~1000 units tall
SS = 2  # supersampling for clean edges

def shade(hexc, k):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c * k))) for c in (r, g, b))

@dataclass
class Character:
    skin: str
    hair: str
    jacket: str
    shirt: str
    pants: str
    shoes: str = "#1d2433"
    hairstyle: str = "short"  # short | bun | pony
    tie: str | None = None
    shoulders: int = 118
    waist: int = 92

    def render(self, pose=None, height=900):
        p = dict(la=(8, 6), ra=(8, 6), tilt=0, blink=0, mouth=0, brows=0, look=0, lean=0, prop=None) | (pose or {})
        img = Image.new("RGBA", (CW * SS, CH * SS)); d = ImageDraw.Draw(img)
        P = lambda x, y: (FX * SS + x * SS, FY * SS + y * SS)
        def poly(pts, fill): d.polygon([P(*q) for q in pts], fill=fill)
        def disc(x, y, r, fill): d.ellipse((*P(x - r, y - r), *P(x + r, y + r)), fill=fill)
        def seg(a, b, w, fill, w2=None):
            """Tapered capsule from a (width w) to b (width w2)."""
            w2 = w if w2 is None else w2
            dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy) or 1; nx, ny = -dy / n, dx / n
            poly([(a[0] + nx * w / 2, a[1] + ny * w / 2), (b[0] + nx * w2 / 2, b[1] + ny * w2 / 2),
                  (b[0] - nx * w2 / 2, b[1] - ny * w2 / 2), (a[0] - nx * w / 2, a[1] - ny * w / 2)], fill)
            disc(*a, w / 2, fill); disc(*b, w2 / 2, fill)

        def arm(side, a1, a2, back):
            sh = (side * (self.shoulders - 18), -772)
            u = math.radians(a1); el = (sh[0] + side * 195 * math.sin(u), sh[1] + 195 * math.cos(u))
            v = math.radians(a1 + a2); hd = (el[0] + side * 180 * math.sin(v), el[1] + 180 * math.cos(v))
            c = shade(self.jacket, 0.82 if back else 1)
            seg(sh, el, 60, c, 52); seg(el, hd, 52, c, 42)
            cuff = (hd[0] - (hd[0] - el[0]) * 0.08, hd[1] - (hd[1] - el[1]) * 0.08)
            disc(*cuff, 18, shade(self.shirt, 0.9 if back else 1))
            d.ellipse((*P(hd[0] - 21, hd[1] - 26), *P(hd[0] + 21, hd[1] + 26)), fill=shade(self.skin, 0.9 if back else 1))
            return hd

        # back arm, legs, torso
        arm(-1, *p["la"], back=True)
        for s in (-1, 1):
            seg((s * 44, -470), (s * 46, -46), 76, shade(self.pants, 0.85 if s < 0 else 1), 54)
            d.ellipse((*P(s * 46 - 34 + s * 14, -42), *P(s * 46 + 34 + s * 14, 2)), fill=self.shoes)
        sw, wa = self.shoulders, self.waist
        poly([(-sw, -770), (-wa, -600), (-wa - 8, -440), (wa + 8, -440), (wa, -600), (sw, -770), (sw - 30, -806), (-sw + 30, -806)], self.jacket)
        poly([(0, -806), (sw - 30, -806), (sw, -770), (wa, -600), (wa + 8, -440), (0, -440)], shade(self.jacket, 0.9))
        disc(-sw + 30, -776, 30, self.jacket); disc(sw - 30, -776, 30, shade(self.jacket, 0.9))
        poly([(-34, -806), (34, -806), (0, -660)], self.shirt)
        if self.tie: poly([(-11, -790), (11, -790), (16, -660), (0, -630), (-16, -660)], self.tie)
        poly([(-34, -806), (-6, -700), (-50, -770)], shade(self.jacket, 1.15))  # lapels
        poly([(34, -806), (6, -700), (50, -770)], shade(self.jacket, 1.05))
        hand = arm(1, *p["ra"], back=False)
        if p["prop"] == "phone":
            d.rounded_rectangle((*P(hand[0] - 20, hand[1] - 52), *P(hand[0] + 20, hand[1] + 14)), 7 * SS, fill="#111827")

        # neck, head, hair, face
        hx, hy = 6 * p["tilt"], -905
        seg((0, -820), (hx * 0.4, -850), 44, shade(self.skin, 0.88))
        hc = shade(self.hair, 0.82)
        if self.hairstyle == "pony": seg((hx + 52, hy - 20), (hx + 74, hy + 90), 40, hc, 18)
        if self.hairstyle == "bun": disc(hx + 10, hy - 82, 32, hc)
        for s in (-1, 1): d.ellipse((*P(hx + s * 62 - 12, hy - 4), *P(hx + s * 62 + 12, hy + 26)), fill=shade(self.skin, 0.9))  # ears
        d.ellipse((*P(hx - 60, hy - 78), *P(hx + 60, hy + 80)), fill=self.skin)
        d.chord((*P(hx - 66, hy - 88), *P(hx + 66, hy + 40)), 180, 360, fill=self.hair)
        poly([(hx - 66, hy - 24), (hx - 30, hy - 74), (hx + 70, hy - 50), (hx + 66, hy - 22), (hx + 20, hy - 46)], self.hair)  # side-swept fringe
        if self.hairstyle != "short": poly([(hx - 66, hy - 26), (hx - 58, hy + 30), (hx - 48, hy - 20)], self.hair)
        ink, lx = "#1f2430", hx + 7 * p["look"]
        for s in (-1, 1):
            ex, ey = lx + s * 25, hy + 2
            eh = 9 * (1 - p["blink"]) + 1.5
            d.ellipse((*P(ex - 6, ey - eh), *P(ex + 6, ey + eh)), fill=ink)
            b = p["brows"] * 8; tilt = s * p["brows"] * -4  # raised brows lift and soften, negative brows frown inward
            d.line((*P(ex - 14, ey - 22 - b + tilt), *P(ex + 14, ey - 22 - b - tilt)), fill=self.hair, width=6 * SS)
        d.line((*P(lx + 2, hy + 4), *P(lx + 8, hy + 20), *P(lx, hy + 22)), fill=shade(self.skin, 0.75), width=4 * SS)  # nose
        my = hy + 42
        if p["mouth"] > 0.1:
            m = 4 + 12 * p["mouth"]
            d.ellipse((*P(lx - 13, my - m / 2), *P(lx + 13, my + m / 2)), fill="#5b2a2a")
        else:
            d.line((*P(lx - 12, my), *P(lx + 12, my)), fill=shade(self.skin, 0.55), width=5 * SS)

        if p["lean"]: img = img.rotate(-p["lean"], Image.BICUBIC, center=(FX * SS, FY * SS))
        k = height / 1000
        return img.resize((round(CW * k), round(CH * k)), Image.LANCZOS)

    @staticmethod
    def feet(height):
        """Feet origin inside a cutout rendered at `height`."""
        k = height / 1000; return FX * k, FY * k

def smooth(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)

def blend(a, b, e):
    """Pose a→b at progress e: numbers and tuples interpolate, the prop switches halfway."""
    out = dict(a)
    for k, v in b.items():
        u = a.get(k, v)
        out[k] = (tuple(x + (y - x) * e for x, y in zip(u, v)) if isinstance(v, tuple) else
                  u + (v - u) * e if isinstance(v, (int, float)) and isinstance(u, (int, float)) else v if e > 0.5 else u)
    return out

BASE = dict(la=(8, 6), ra=(8, 6), tilt=0, blink=0, mouth=0, brows=0, look=0, lean=0, prop=None)

class Actor:
    """Character on a timeline. keys: [(t, pose)] reached by eased 0.3 s moves; xs: [(t, x)] slides; talk: [(s, e)] lip-flap spans."""
    def __init__(self, ch, keys, xs, height=700, talk=(), seed=0):
        self.ch, self.keys, self.xs, self.h, self.talk, self.seed = ch, keys, xs, height, talk, seed

    def track(self, keys, t, base, move):
        cur = base
        for t0, k in keys:
            if t < t0: break
            cur = blend(cur, k, smooth((t - t0) / move)) if isinstance(k, dict) else cur + (k - cur) * smooth((t - t0) / move)
        return cur

    def draw(self, img, t, floor):
        pose = self.track(self.keys, t, BASE, 0.3)
        if (t + self.seed) % 3.3 < 0.13: pose["blink"] = 1
        if any(a <= t < b for a, b in self.talk): pose["mouth"] = abs(math.sin(t * 19 + self.seed))
        x = self.track(self.xs, t, self.xs[0][1], 0.45)
        pose["tilt"] += 0.6 * math.sin(t * 1.7 + self.seed)  # idle sway
        c = self.ch.render(pose, self.h); fx, fy = Character.feet(self.h)
        d = ImageDraw.Draw(img); r = self.h * 0.2
        d.ellipse((x - r, floor - r * 0.12, x + r, floor + r * 0.12), fill="#d5dbe8")  # floor shadow
        img.paste(c, (round(x - fx), round(floor - fy + 3 * math.sin(t * 2.4 + self.seed))), c)  # breathing; paste allows off-canvas offsets

CEO = Character(skin="#e8b896", hair="#c9ccd3", jacket="#1e2a44", shirt="#f4f5f7", pants="#1a2338", tie="#2563eb")
CMO = Character(skin="#c98f6a", hair="#2a1d17", jacket="#3b4252", shirt="#e9edf5", pants="#262c38", hairstyle="pony", shoulders=104, waist=78)

if __name__ == "__main__":
    poses = [{}, {"ra": (95, -5), "look": 1, "mouth": 0.6}, {"la": (25, 70), "ra": (25, 70), "brows": -1, "tilt": 2},
             {"ra": (150, 15), "brows": 1}, {"prop": "phone", "ra": (12, 130), "look": 1}, {"la": (-10, -110), "ra": (-10, -110), "brows": 1, "tilt": -2}]
    sheet = Image.new("RGBA", (6 * 420, 1000), "#eef1f7")
    for i, pz in enumerate(poses):
        c = (CMO if i % 2 else CEO).render(pz, 760)
        sheet.alpha_composite(c, (i * 420 + 210 - round(Character.feet(760)[0]), 960 - round(Character.feet(760)[1])))
    sheet.convert("RGB").save("out/people-sheet.jpg")
