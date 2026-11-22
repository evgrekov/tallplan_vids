# /// script
# dependencies = []
# ///
"""Transparent full-body pose cutouts of Dana and the CEO for layout animation (gpt-image edits from the sheet)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent)); import oai

ROOT = pathlib.Path(__file__).parent.parent
STYLE = ("Cinematic editorial illustration, serious graphic-novel feature for a business magazine: realistic proportions, painterly digital brushwork "
         "with clean confident line work, muted palette of deep navy, charcoal and warm skin tones with a single cool blue accent. "
         "Not cartoonish, not cute, not anime, not 3D render, not photoreal.")
DANA = ("Same woman as the reference sheet: around 40, sharp intelligent face, light olive skin, dark brown hair in a low practical ponytail with a few loose strands, "
        "thin gold stud earrings, charcoal blazer over a plain black crew-neck top, dark trousers, no glasses.")
CUT = "Single full-figure cutout from head to knees, centred, facing the viewer, isolated on a fully transparent background, no floor, no shadow, no props, no text."
POSES = {
    "dana_neutral": f"{DANA} Standing calm and composed, arms relaxed, slight confident half-smile. {CUT}",
    "dana_wry": f"{DANA} One eyebrow raised, dry knowing look, arms crossed. {CUT}",
    "dana_point": f"{DANA} Pointing to her right side (viewer's left) with an open hand, presenting something, focused expression. {CUT}",
    "dana_shrug": f"{DANA} Small shrug with both palms up, deadpan expression as if saying 'well, there it is'. {CUT}",
    "ceo": ("A different person: male CEO around 55, silver short hair, clean-shaven, navy suit, white shirt, no tie, holding a phone, "
            f"impatient demanding expression, leaning slightly forward. {CUT}"),
}
for name in sys.argv[1:] or POSES:
    out = ROOT / "poses" / f"{name}.png"
    if out.exists(): continue
    oai.edit(f"{STYLE} {POSES[name]}", [ROOT / "char/sheet.png"], out, quality="high", background="transparent")
    print(f"🧍 {name}  ${oai.spent:.3f}")
