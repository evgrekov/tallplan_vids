# /// script
# dependencies = ["pillow"]
# ///
"""Google App campaign video #1 "everyone came back taller": a notes-app rant → TallPlan locked → "+4 in to grow" → end card.
No shots of bodies or friends side by side (body comparison is off-limits); only my notes and the app.
Usage: uv run gads/summer.py
"""
from PIL import Image, ImageDraw
import kit
from kit import SW, SH, archivo, ease

D = kit.ROOT / "gads/summer"
NOTE = ["first day back.", "everyone grew over the summer??", "jay: like 3 inches", "sam: taller too", "me: same \U0001F480"]
LINES = [
    ("l1", "Everyone came back from summer taller. Except me.", kit.TEEN + " Dramatic, half-joking complaint."),
    ("l2", "Am I done growing? Let's check.", kit.TEEN),
    ("l3", "Four more inches to go? I'm not done!", kit.TEEN + " Relieved and hyped.", 0.25),
    ("l4", f"{kit.CTA}!", kit.TEEN + " Hyped call to action."),
]
BAR = kit.bar("7:58")
LOCKED = Image.open(kit.SHOTS / "01-home-locked.png").convert("RGB")
HOME = Image.open(kit.SHOTS / "01-home.png").convert("RGB")

def notes(chars):
    """Unbranded dark notes screen with the rant typed up to `chars` characters."""
    im = Image.new("RGB", (SW, SH), kit.BG); im.paste(BAR, (0, 0))
    d = ImageDraw.Draw(im)
    d.text((90, 290), "‹ Notes", font=archivo(58, 600), fill=kit.LIME, anchor="lm")
    d.text((90, 420), "summer recap", font=archivo(110, 900), fill="white")
    f, y, left = archivo(76, 500), 640, chars
    for line in NOTE:
        if left <= 0: break
        part = line[:left]; left -= len(line)
        x = kit.rich(im, (90, y), part, f, "white")
        if 0 < len(part) < len(line) or left <= 0: d.rectangle((x + 6, y + 6, x + 12, y + 92), fill=kit.LIME)  # cursor
        y += 130
    return im

def scenes(st):
    total = sum(len(l) for l in NOTE)
    s2 = st["l2"][0]

    def screen(t):
        if t < s2 - 0.1:  # the rant types itself under the first line
            return notes(round(total * ease(t / (s2 - 0.3))))
        return kit.shots(t, [(s2 - 0.1, st["l3"][0] - 0.1, dict(img=LOCKED, z=(1, 1.12), f=(0.5, 0.42), at=(658, 1244))),
                             (st["l3"][0] - 0.1, None, dict(img=HOME, z=(1, 1.7), f=(0.72, 0.17), flash=True))])  # push in on "+4 in to grow"
    return screen

if __name__ == "__main__":
    kit.make(D, LINES, scenes, "Estimate based on your data. Not medical advice.",
             "Funny modern TikTok beat, bouncy trap hi-hats, playful bass, a little dramatic then hopeful, 120 BPM, about 25 seconds.")
