"""Dana character sheet (gpt-image). Usage: python3 char/sheet.py → char/sheet.png, char/hero.png"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import oai

OUT = pathlib.Path(__file__).parent
DANA = ("Dana, Head of Growth at a B2B software company. Woman around 40, sharp intelligent face, light olive skin, "
        "dark brown hair in a low practical ponytail with a few loose strands, subtle tired eyes but focused, thin gold stud earrings, "
        "charcoal blazer over a plain black crew-neck top, no jewelry besides earrings, no glasses.")
STYLE = ("Cinematic editorial illustration in the style of a serious graphic-novel feature for a business magazine: "
         "realistic proportions, painterly digital brushwork with clean confident line work, muted palette of deep navy, charcoal and warm skin tones "
         "with a single cool blue accent, soft directional light. Mature and grounded, not cartoonish, not cute, not anime, not 3D render, not photoreal.")

print("🎨 character sheet...")
oai.image(f"Character turnaround sheet. {DANA} {STYLE} Three full-height-from-waist views side by side on a plain warm light-grey background: "
          "front view, three-quarter view, side profile. Neutral calm expression, arms relaxed. Same face, hair and outfit in all three views. "
          "No text, no labels, no logos.", OUT / "sheet.png", quality="high", size="1536x1024")
print(f"💰 ~${oai.spent:.2f}")
print("🎨 hero frame...")
oai.image(f"{DANA} {STYLE} Night, she sits at her desk in a dark open-plan office, lit mostly by the cool glow of a monitor off-frame, "
          "city lights blurred through the window behind her. Medium close-up, she looks at the screen with quiet worry. "
          "Vertical 9:16 composition, face in the upper third. No text, no logos, no readable screen.", OUT / "hero.png", quality="high", size="1024x1536")
print(f"✅ char/sheet.png, char/hero.png · 💰 ~${oai.spent:.2f}")
