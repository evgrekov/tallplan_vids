# /// script
# dependencies = ["pillow"]
# ///
"""Google App campaign video #8 "honest height app": where the estimate comes from → my prediction → daily habits → end card.
No competitor names and no "pills/stretching" words (even a denial can land the ad in body modification).
Usage: uv run gads/honest.py
"""
from PIL import Image
import kit

D = kit.ROOT / "gads/honest"
LINES = [
    ("l1", "No fake promises.", kit.TEEN + " Confident, a bit fed up with hype."),
    ("l2", "Just your real predicted height,", kit.TEEN),
    ("l3", "and the habits that actually matter: sleep, food, workouts.", kit.TEEN, 0.25),
    ("l4", f"{kit.CTA}!", kit.TEEN + " Hyped call to action."),
]
S = {n: Image.open(kit.SHOTS / f"{n}.png").convert("RGB") for n in ("02-estimate-sources", "01-home", "07-sleep", "09-meals", "11-workout-overview")}

def scenes(st):
    (s2, d2), (s3, d3) = st["l2"], st["l3"]
    a, b = s3 + d3 / 3, s3 + 2 * d3 / 3  # three habits, one per third of the line
    return lambda t: kit.shots(t, [
        (0, s2 - 0.1, dict(img=S["02-estimate-sources"], z=(1, 1.1), f=(0.5, 0.1))),  # "General guidance, not medical advice", ±1.1 in
        (s2 - 0.1, s3 - 0.1, dict(img=S["01-home"], z=(1, 1.15), f=(0.5, 0.2), flash=True)),
        (s3 - 0.1, a, dict(img=S["07-sleep"], z=(1.05, 1.2), f=(0.5, 0.3))),
        (a, b, dict(img=S["09-meals"], z=(1.05, 1.2), f=(0.5, 0.3))),
        (b, None, dict(img=S["11-workout-overview"], z=(1.05, 1.2), f=(0.5, 0.3)))])

if __name__ == "__main__":
    kit.make(D, LINES, scenes, "Estimate based on your data. Not medical advice.",
             "Confident modern hip hop beat, clean drums, warm bass, chill but punchy, 95 BPM, about 25 seconds.")
