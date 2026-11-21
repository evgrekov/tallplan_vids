# /// script
# dependencies = ["pillow"]
# ///
"""Google App campaign video #2 "1am googling": late-night search → TallPlan locked prediction → 6'3" reveal → end card.
Usage: uv run gads/googling.py   (idempotent: voice/music are cached in gads/googling/)
"""
from PIL import Image, ImageDraw
import kit
from kit import SW, SH, archivo, ease

D = kit.ROOT / "gads/googling"
QUERY = "am i done growing at 16"
SUGGEST = ["am i done growing at 15", "am i done growing quiz", "am i a late bloomer", "how tall will i be"]
RESULTS = [("Most guys stop growing around 16", 3), ("Some keep growing until 21", 2), ("It depends on your parents", 3), ("Late bloomers: how to tell", 2)]
LINES = [  # (key, text, voice direction)
    ("l1", "1 AM. Googling: am I done growing at sixteen?", kit.TEEN + " Half-whispering, it's late at night."),
    ("l2", "Every answer's different.", kit.TEEN),
    ("l3", "So I checked TallPlan.", kit.TEEN),
    ("l4", "Six-three?! Okay, let's go!", kit.TEEN + " Excited and hyped.", 0.3),
    ("l5", f"{kit.CTA}!", kit.TEEN + " Hyped call to action."),
]

LOCKED = Image.open(kit.SHOTS / "01-home-locked.png").convert("RGB")
HOME = Image.open(kit.SHOTS / "01-home.png").convert("RGB")
BAR = kit.bar("1:07")

def lens(d, x, y, s, fill):
    d.ellipse((x - s, y - s, x + s * 0.6, y + s * 0.6), outline=fill, width=max(3, s // 5))
    d.line((x + s * 0.45, y + s * 0.45, x + s * 1.1, y + s * 1.1), fill=fill, width=max(4, s // 4))

def search(typed, cursor, suggest, scroll):
    """Unbranded dark search screen: pill with the typed query, then suggestions or contradicting results (scroll 0..1)."""
    im = Image.new("RGB", (SW, SH), kit.BG); im.paste(BAR, (0, 0))
    d = ImageDraw.Draw(im)
    q = archivo(84, 500)
    if scroll is None:
        d.rounded_rectangle((50, 260, SW - 50, 460), 100, fill=(34, 35, 40))
        lens(d, 145, 355, 32, (160, 162, 170))
        d.text((225, 362), typed, font=q, fill="white", anchor="lm")
        if cursor: x = 220 + q.getlength(typed) + 6; d.rectangle((x, 310, x + 7, 410), fill=kit.LIME)
        for i in range(suggest):
            y = 590 + i * 190
            lens(d, 145, y, 26, (120, 122, 130))
            s = SUGGEST[i]; head = s[:len(typed)] if s.startswith(typed) else ""
            d.text((220, y + 6), head, font=archivo(76, 450), fill=(150, 152, 160), anchor="lm")
            d.text((220 + archivo(76, 450).getlength(head), y + 6), s[len(head):], font=archivo(76, 800), fill="white", anchor="lm")
        return im
    off = -scroll * 500
    d.rounded_rectangle((60, 230, SW - 60, 370), 70, fill=(34, 35, 40))
    lens(d, 150, 297, 24, (160, 162, 170)); d.text((215, 302), QUERY, font=archivo(70, 500), fill="white", anchor="lm")
    for i, (title, bars) in enumerate(RESULTS):
        y = 480 + i * 560 + off
        d.rounded_rectangle((60, y, SW - 60, y + 500), 40, fill=(22, 23, 27))
        d.rounded_rectangle((110, y + 50, 300, y + 80), 15, fill=(60, 62, 70))
        d.text((110, y + 115), title, font=archivo(72, 800), fill="white")
        for b in range(bars):
            d.rounded_rectangle((110, y + 250 + b * 70, SW - 160 - b * 180, y + 290 + b * 70), 20, fill=(55, 57, 64))
    return im

def scenes(st):
    typed_by = st["l1"][0] + 0.55 * st["l1"][1]  # the query is typed under the first half of the line

    def screen(t):
        if t < st["l2"][0] - 0.1:  # cut 1: typing, cut 2: suggestions drop
            n = round(len(QUERY) * ease(t / typed_by))
            return search(QUERY[:n], int(t * 2.5) % 2 == 0, 0 if t < typed_by else min(4, int((t - typed_by) * 8) + 1), None)
        if t < st["l3"][0] - 0.1:  # cut 3: contradicting results scroll by
            return search(QUERY, False, 0, (t - st["l2"][0]) / st["l2"][1])
        return kit.shots(t, [(st["l3"][0] - 0.1, st["l4"][0] - 0.1, dict(img=LOCKED, z=(1, 1.12), f=(0.5, 0.42), at=(658, 1244))),  # tap "See how tall I'll be"
                             (st["l4"][0] - 0.1, None, dict(img=HOME, z=(1, 1.12), f=(0.5, 0.2), flash=True))])  # 6'3" reveal
    return screen

if __name__ == "__main__":
    kit.make(D, LINES, scenes, "Estimate based on your data. Not medical advice.",
             "Late-night lo-fi hip hop beat, soft dusty drums, warm Rhodes chords, mellow and intimate, 80 BPM, about 25 seconds.")
