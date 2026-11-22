"""Ep. 2 keyframes: Dana in the same office on a bright morning (gpt-image edits). Usage: python3 keyframes/make.py [scene...]"""
import pathlib, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import oai

REFS = [ROOT / "char/sheet.png", ROOT / "char/s1.png"]
BASE = ("Use the woman from the first image (character sheet): exactly the same face, age, dark brown low ponytail with loose strands, "
        "gold stud earrings, charcoal blazer over a black crew-neck top. Same office and the same cinematic editorial graphic-novel illustration style "
        "as the second image, realistic proportions, painterly brushwork with clean line work, but now on a bright morning: warm sunlight through the "
        "windows, soft daylight, a few colleagues blurred in the background. Vertical 9:16. No text, no logos, no readable screens. ")
SCENES = {
    "k1": "Monday morning. She sits at her desk in front of an open laptop, grinning, raising a coffee mug in a small victory toast, "
          "genuinely pleased with herself. Medium shot, her face in the middle of the frame, empty bright wall space in the upper third.",
    "k2": "Tuesday morning, same desk. She stares at the laptop, her smile frozen and fading, coffee mug stopped halfway to her mouth, "
          "eyebrows raised in disbelief. Medium close-up, empty space in the upper third.",
    "k3": "She drops her forehead into her palm in a wry, exasperated facepalm, elbow on the desk next to the laptop, a tired half-smile. Medium shot.",
    "k4": "She leans back with a confident, knowing smile, arms crossed, the laptop open in front of her showing soft blurred charts. "
          "Medium shot, she looks slightly past the camera, relaxed and in control.",
}
todo = sys.argv[1:] or list(SCENES)
def make(k):
    print(f"🎨 {k}...", flush=True)
    oai.edit(BASE + SCENES[k], REFS, ROOT / f"keyframes/{k}.png", quality="high")
    print(f"✅ {k}", flush=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(make, todo))
print(f"💰 ~${oai.spent:.2f}")
