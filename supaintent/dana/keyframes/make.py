"""Scene keyframes with Dana from the character sheet (gpt-image edits). Usage: python3 keyframes/make.py [scene...]"""
import pathlib, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import oai

REFS = [ROOT / "char/sheet.png", ROOT / "char/hero.png"]
BASE = ("Use the woman from the first image (character sheet): exactly the same face, age, dark brown low ponytail with loose strands, "
        "gold stud earrings, charcoal blazer over a black crew-neck top. Setting, night lighting and illustration style as in the second image: "
        "cinematic editorial graphic-novel illustration, realistic proportions, painterly brushwork with clean line work, deep navy and charcoal palette, "
        "cool monitor glow as the key light, blurred city lights through the window. Vertical 9:16. No text, no logos, no readable screens. ")
SCENES = {
    "s1": "Medium close-up, she sits at her desk late at night staring at a monitor just off-frame, tense jaw, quiet worry. "
          "Her face sits in the middle of the frame with dark empty office space in the upper third.",
    "s2": "Three-quarter view from behind her shoulder: she leans toward an open laptop and types a question, hands on the keyboard, "
          "the laptop screen glows softly and shows only blurred abstract light, focused expression in profile.",
    "s4": "She leans back in her office chair, one hand at her temple, eyes still on the screen, the realization sinking in. "
          "Medium shot, the monitor light washes across her face, the empty office behind her.",
    "s6": "She calmly closes the laptop lid with one hand and looks up past the camera, determined, the beginning of a plan. "
          "Medium close-up, the laptop glow fades on her face, city lights behind her.",
}
todo = sys.argv[1:] or list(SCENES)
def make(k):
    print(f"🎨 {k}...", flush=True)
    oai.edit(BASE + SCENES[k], REFS, ROOT / f"keyframes/{k}.png", quality="high")
    print(f"✅ {k}", flush=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(make, todo))
print(f"💰 ~${oai.spent:.2f}")
