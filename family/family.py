# /// script
# dependencies = ["pillow"]
# ///
"""Comment reply with a stick-figure family (ref @how.tall.will.i.b, rules C-HTW): a viewer's comment card on top, the whole crooked
family stands on a height scale from frame 1 (each voice line adds that member's height), the mid-parental formula (dad + mom ± 5) ÷ 2
with a big yellow result, a TallPlan-style prediction card as the refinement, honest/comforting outro + CTA, then packshot.
No video or image generation: only TTS (~$0.02).

  uv run family.py <work>/spec.json   -> <work>/final.mp4   (idempotent: delete a wav to redo that line)
"""
import json, pathlib, sys
from PIL import Image, ImageDraw
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "slides"))
from kit import W, H, font, ftin, say, timeline, figure, tallcard, render

GROUND, PX = 1180, 8.2  # PX = pixels per inch; 78 in reaches y≈540, under the comment card
PAPER, YELLOW, INK = "#FBFAF6", "#F7C500", "#222"
spec_f = pathlib.Path(sys.argv[1]).resolve()
spec, d = json.loads(spec_f.read_text()), spec_f.parent
fam = spec["family"]
kid = next(m for m in fam if m.get("kid"))
dad, mom = (next(m["in"] for m in fam if m["who"] == w) for w in ("DAD", "MOM"))
plus = 5 if spec["sex"] == "boy" else -5
mid, rng, adult = round((dad + mom + plus) / 2), spec["range"], spec["app"]["adult"]
assert abs(adult - mid) <= rng, "the app prediction must sit inside the formula range"

# 1) voice: intro, one line per family member, formula, result, app card, outro (the outro plays over the app card)
names = ["intro"] + [f"m{i}" for i in range(len(fam))] + ["formula", "result", "app", "outro"]
texts = [spec["intro"]] + [m["say"] for m in fam] + [spec["formula_say"], spec["result_say"], spec["app"]["say"], spec["outro"]]
cues, end = timeline([say(d, spec, n, t) for n, t in zip(names, texts)])

# 2) states. Frame 1 already shows the whole family on the scale (G02: the hook is the figures, not the math);
#    each member's line only adds their height tag, then the formula, then the kid at 18 fills the "?" slot.
xs = [W * (0.17 + 0.69 * k / len(fam)) for k in range(len(fam) + 1)]  # last slot = the kid at 18

def tag(dr, x, y, text, color, size=44):
    dr.text((x, y), text, font=font(size, 900), fill=color, anchor="mm", stroke_width=5, stroke_fill=PAPER)

im = Image.new("RGB", (W, H), PAPER)
d2 = ImageDraw.Draw(im)
for i in range(48, 79, 6):  # scale: dashed line every 6 in, labelled on the left
    y = GROUND - i * PX
    for x0 in range(150, 1010, 28): d2.line((x0, y, x0 + 16, y), fill="#999", width=4)
    d2.text((62, y), ftin(i), font=font(32, 800), fill="#666", anchor="lm")
d2.line((120, GROUND, 1010, GROUND), fill=INK, width=8)
c = spec["comment"]  # comment card: grey avatar, handle, two lines of text
d2.rounded_rectangle((90, 280, W - 90, 470), 34, fill="white", outline="#E2E2E2", width=3)
d2.ellipse((122, 312, 202, 392), fill="#9aa0a6")
d2.text((226, 330), c["user"], font=font(32, 700), fill="#777", anchor="lm")
d2.multiline_text((226, 360), c["text"], font=font(38, 800), fill="#111", spacing=8)
tops = [figure(im, xs[k], GROUND, m["in"] * PX, m["color"], k, spec.get("hats", False)) for k, m in enumerate(fam)]
for k, m in enumerate(fam): tag(d2, xs[k], GROUND + 38, m["who"], m["color"], 36)
tag(d2, xs[-1], GROUND + 38, "AT 18", "#C99A00", 36)

def with_q(frame):  # the empty "kid at 18" slot until the result line
    f = frame.copy()
    ImageDraw.Draw(f).text((xs[-1], GROUND - 300), "?", font=font(260, 900), fill=YELLOW, anchor="mm", stroke_width=8, stroke_fill=INK)
    return f

states = [with_q(im)]
for k, m in enumerate(fam):
    tag(d2, xs[k], tops[k] - (m["in"] * PX * 0.07 + 30 if spec.get("hats") else 34), ftin(m["in"]), m["color"])
    states.append(with_q(im))
d2.text((W / 2, 1282), f"({dad} + {mom} {'+' if plus > 0 else '−'} 5) ÷ 2 = {mid} in", font=font(56, 800), fill="#111", anchor="mm")
states.append(with_q(im))
ghost = Image.new("RGBA", (W, H))
gtop = figure(ghost, xs[-1], GROUND, mid * PX, (247, 197, 0, 170), 99)
im.paste(ghost, (0, 0), ghost)
tag(d2, xs[-1], gtop - 34, ftin(mid), "#C99A00")
d2.text((W / 2 - 40, 1380), ftin(mid), font=font(150, 900), fill=YELLOW, anchor="mm", stroke_width=8, stroke_fill="#111")
d2.text((W / 2 + 190, 1395), f"± {rng} in", font=font(48, 800), fill="#111", anchor="lm")
states.append(im.copy())

# 3) TallPlan card slides up on the app line; states switch on their lines
tallcard(d / "app.png", adult, kid["in"])
starts = [cues[1 + k][1] for k in range(len(fam))] + [cues[-4][1], cues[-3][1]]
render(d, states, starts, cues, end, cues[-2][1], d / "app.png")
