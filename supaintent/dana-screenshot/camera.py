"""Camera over a screenshot: eased pans/zooms between keyed regions, slow push-in between moves,
spotlight + marker highlight + numbered badge on the region being spoken about."""
from PIL import Image, ImageDraw, ImageFont, ImageOps

PAD = 800  # border around the source so the camera can frame past its edges

def smooth(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)

class Shot:
    def __init__(self, path, font_path, cover=()):
        src = Image.open(path).convert("RGBA")
        self.bg = src.getpixel((4, src.height - 4))
        for b in cover: ImageDraw.Draw(src).rectangle(b, fill=self.bg)  # hide browser chrome such as extension widgets
        self.src = ImageOps.expand(src, PAD, fill=self.bg)
        self.font_path = font_path

    def frame(self, keys, t, move=0.45):
        """keys: [(t0, (cx, cy, w))] in source px; each key is reached by an eased move starting at t0."""
        cur = keys[0][1]
        for t0, k in keys[1:]:
            if t < t0: break
            e = smooth((t - t0) / move); cur = tuple(a + (b - a) * e for a, b in zip(cur, k))
        cx, cy, w = cur
        return cx, cy, w * (1 - 0.025 * (t - keys[0][0]))  # constant slow push-in keeps the frame alive

    def render(self, t, keys, marks, size, acc, dim=(0, 0, 0, 165), radius=36):
        """View image of `size`. marks: [(t0, (x1, y1, x2, y2), badge or None)]; the latest active one gets the spotlight."""
        vw, vh = size
        cx, cy, w = self.frame(keys, t)
        h = w * vh / vw; k = vw / w; left, top = cx - w / 2, cy - h / 2
        view = self.src.crop((round(left + PAD), round(top + PAD), round(left + PAD + w), round(top + PAD + h))).resize(size, Image.LANCZOS)
        scr = lambda b: (int((b[0] - left) * k), int((b[1] - top) * k), int((b[2] - left) * k), int((b[3] - top) * k))
        on = [m for m in marks if t >= m[0]]
        if on:  # spotlight: dim everything except the current region
            t0, b, _ = on[-1]; x1, y1, x2, y2 = scr(b); p = 14
            a = int(dim[3] * smooth((t - t0) / 0.2))
            shade = Image.new("RGBA", size, dim[:3] + (a,))
            ImageDraw.Draw(shade).rounded_rectangle((x1 - p, y1 - p, x2 + p, y2 + p), 18, fill=(0, 0, 0, 0))
            view.alpha_composite(shade)
        hl = Image.new("RGBA", size); d = ImageDraw.Draw(hl)
        for i, (t0, b, badge) in enumerate(on):
            x1, y1, x2, y2 = scr(b); p = 14
            e = smooth((t - t0) / 0.3); cur = i == len(on) - 1
            d.rounded_rectangle((x1 - p, y1 - p, x1 - p + (x2 - x1 + 2 * p) * e, y2 + p), 18, fill=acc + ((70,) if cur else (40,)))
            if cur: d.rounded_rectangle((x1 - p, y1 - p, x2 + p, y2 + p), 18, outline=acc + (255,), width=7)
            if badge:
                r = 28 * smooth((t - t0) / 0.15); bx, by = max(x1 - p - 6, 44), max(y1 - p - 6, 44)  # keep the badge inside the view
                d.ellipse((bx - r, by - r, bx + r, by + r), fill=acc + (255,))
                if r > 16: d.text((bx, by), badge, font=ImageFont.truetype(self.font_path, 34), fill="#ffffff", anchor="mm")
        view.alpha_composite(hl)
        m = Image.new("L", size); ImageDraw.Draw(m).rounded_rectangle((0, 0, vw - 1, vh - 1), radius, fill=255)
        out = Image.new("RGBA", size); out.paste(view, (0, 0), m)
        return out
