# /// script
# dependencies = ["pillow"]
# ///
"""Final height X: the year-by-year path (ref @staturesecrets, rules C-STAT): black ruler stage, our lime pill character grows age by age
(12 → 18, % of adult height from CDC boys' medians), grey ghosts of past years, finish line at the final height, one add-on card
(countries / parents...), "genes set your range", TallPlan-style prediction card last, CTA, packshot. Slowed phonk from a ref under the voice.
The script is the same for every video: the spec only sets the final height and the add-on (C-STAT-1). Only TTS (~$0.02).

  uv run path.py <work>/spec.json   -> <work>/final.mp4   (idempotent: delete a wav to redo that line)
"""
import json, pathlib, sys
from PIL import Image, ImageDraw
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "slides"))
from kit import W, H, LIME, font, ftin, say, timeline, figure, tallcard, render

MUSIC = pathlib.Path.home() / "Library/CloudStorage/GoogleDrive-evgrekov@gmail.com/My Drive/Projects/TT30/tallplan/02_sources/music"
BG, GRID, GREY, GROUND, PXC = "#0B0B0D", "#2A2A2E", "#9A9A9A", 1290, 3.6  # PXC = pixels per cm: 201 cm reaches y≈567
PCT = {12: 84, 13: 88, 14: 92, 15: 96, 16: 98, 17: 99, 18: 100}  # % of adult height, CDC stature-for-age 50th pct boys (~176.5 cm at 20)
TAGS = {12: "BEFORE THE SPURT", 13: "THE SPURT STARTS", 14: "TURBO MODE · UP TO 12 CM/YR", 15: "ALREADY 96% THERE", 16: "GROWTH SLOWS",
        17: "ALMOST DONE", 18: "FINAL HEIGHT"}
spec_f = pathlib.Path(sys.argv[1]).resolve()
spec, d = json.loads(spec_f.read_text()), spec_f.parent
final = spec["final_cm"]
fin = round(final / 2.54)
cm = {a: round(final * p / 100) for a, p in PCT.items()}
assert all(cm[a] < cm[a + 1] for a in range(12, 18)), "heights must grow every year"

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
def w2(n): return ONES[n] if n < 20 else TENS[n // 10] + (f"-{ONES[n % 10]}" if n % 10 else "")
def cmw(c): r = c % 100; return f"{ONES[c // 100]} " + (w2(r) if r >= 10 else f"oh-{ONES[r]}" if r else "hundred")  # 154 → "one fifty-four"
def ftw(i): return f"{ONES[i // 12]} foot" if i % 12 == 0 else f"{ONES[i // 12]} {ONES[i % 12]}"  # G11: short spoken numbers
assert cmw(154) == "one fifty-four" and cmw(201) == "two oh-one" and ftw(72) == "six foot" and ftw(68) == "five eight"

# 1) the fixed script, numbers from the spec
texts = {"intro": f"Final height {ftw(fin)}. {cmw(final).capitalize()} centimeters. Year by year.",
         "a12": f"Twelve. {cmw(cm[12]).capitalize()}. {w2(PCT[12]).capitalize()} percent there.",
         "a13": f"Thirteen. {cmw(cm[13]).capitalize()}. {w2(PCT[13]).capitalize()} percent.",
         "a14": f"Fourteen. {cmw(cm[14]).capitalize()}. Turbo mode.",
         "a15": f"Fifteen. {cmw(cm[15]).capitalize()}. {w2(PCT[15]).capitalize()} percent.",
         "a16": f"Sixteen. {cmw(cm[16]).capitalize()}. Slowing down.",
         "a17": f"Seventeen. {cmw(cm[17]).capitalize()}.",
         "a18": f"Eighteen. {cmw(cm[18]).capitalize()}. Final height.",
         "addon": spec["addon"]["say"],
         "genes": "Genes set your range. Sleep, protein and movement get you to the top of it.",
         "app": "TallPlan predicts your own path.",
         "outro": "How tall are you? Comment your age and height."}
cues, end = timeline([say(d, spec, n, t) for n, t in texts.items()])

# 2) states: one full frame per line
def stage(label, big, sub, tag=None):
    im = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(im)
    for c in range(100, 201, 10):  # ruler grid every 10 cm, labelled on the right
        y = GROUND - c * PXC
        dr.line((90, y, 990, y), fill=GRID, width=2)
        dr.text((1000, y), str(c), font=font(24, 700), fill="#55555C", anchor="lm")
    dr.line((90, GROUND, 990, GROUND), fill="#E6E6E6", width=6)
    dr.text((W / 2, 300), label, font=font(40, 700), fill=GREY, anchor="mm")
    size = 130
    while font(size, 900).getlength(big) > W * 0.8: size -= 4  # G20: text within 80% of the width
    dr.text((W / 2, 385), big, font=font(size, 900), fill="white", anchor="mm")
    dr.text((W / 2, 470), sub, font=font(44, 700), fill=GREY, anchor="mm")
    if tag:
        f = font(34, 800); tw = f.getlength(tag)
        dr.rounded_rectangle((W / 2 - tw / 2 - 28, 510, W / 2 + tw / 2 + 28, 566), 28, outline=LIME, width=3)
        dr.text((W / 2, 538), tag, font=f, fill=LIME, anchor="mm")
    return im, dr

def finish(dr):  # dashed finish line at the final height
    y = GROUND - final * PXC
    for x0 in range(120, 960, 30): dr.line((x0, y, x0 + 16, y), fill=LIME, width=4)
    dr.text((960, y - 22), "FINAL", font=font(26, 800), fill=LIME, anchor="rm")

def bar(dr, pct):
    dr.rounded_rectangle((160, 1360, 920, 1384), 12, fill="#26262B")
    dr.rounded_rectangle((160, 1360, 160 + 760 * pct / 100, 1384), 12, fill=LIME)
    dr.text((W / 2, 1425), f"{pct}% OF ADULT HEIGHT", font=font(34, 800), fill="white", anchor="mm")

states = []
im, dr = stage("FINAL HEIGHT", f"{final} CM", ftin(fin), "THE YEAR BY YEAR PATH")
finish(dr); figure(im, 600, GROUND, final * PXC, LIME, 0, face="#111"); states.append(im)
for a in range(12, 19):
    im, dr = stage(f"AGE {a}", f"{cm[a]} CM", ftin(round(cm[a] / 2.54)), TAGS[a])
    finish(dr)
    for p in range(max(12, a - 2), a):  # grey ghosts of the last two years
        figure(im, 600 - 175 * (a - p), GROUND, cm[p] * PXC, "#3A3A40", p, face=None)
    figure(im, 600, GROUND, cm[a] * PXC, LIME, 0, face="#111")
    bar(dr, PCT[a]); states.append(im)
ad = spec["addon"]
im, dr = stage(ad["label"], ad["title"], f"YOU: {final} CM · {ftin(fin)}")
dr.rounded_rectangle((110, 620, 970, 640 + 120 * len(ad["rows"])), 36, fill="#18181C")
for k, (name, v) in enumerate(ad["rows"]):
    y = 690 + 120 * k; hl = k == ad["hl"]
    if hl: dr.rounded_rectangle((130, y - 50, 950, y + 50), 26, fill=LIME)
    dr.text((170, y), name, font=font(52, 800), fill="#111" if hl else "white", anchor="lm")
    dr.text((910, y), f"{v} CM", font=font(52, 900), fill="#111" if hl else "white", anchor="rm")
states.append(im)
im, dr = stage("SUPPORT YOUR GROWTH", "GENES SET", "YOUR RANGE")
finish(dr); figure(im, 600, GROUND, final * PXC, LIME, 0, face="#111")
f = font(40, 900); pills = [(w, f.getlength(w) + 52) for w in ("SLEEP", "PROTEIN", "MOVEMENT")]
x = (W - sum(pw for _, pw in pills) - 30 * (len(pills) - 1)) / 2  # centred row, 30 px gaps
for w, pw in pills:
    dr.rounded_rectangle((x, 1350, x + pw, 1420), 35, fill="white")
    dr.text((x + pw / 2, 1385), w, font=f, fill="#111", anchor="mm"); x += pw + 30
states.append(im)

# 3) TallPlan card last (C-STAT-3), slowed phonk from the ref under the voice
tallcard(d / "app.png", fin)
render(d, states, [cues[k][1] for k in range(1, len(states))], cues, end, cues[-2][1], d / "app.png", MUSIC / spec["music"])
