# /// script
# dependencies = ["pillow"]
# ///
"""Google App campaign video #7 "not breaking my streak": workout player → rest timer → 34-day streak → badge → end card.
Strength and habit only: the workouts are never tied to height here.
Usage: uv run gads/streak.py
"""
from PIL import Image
import kit

D = kit.ROOT / "gads/streak"
LINES = [
    ("l1", "Started the daily core workout.", kit.TEEN + " Proud, energetic."),
    ("l2", "Eleven minutes a day.", kit.TEEN),
    ("l3", "Thirty-four days in. Not breaking my streak now.", kit.TEEN + " Hyped and proud.", 0.25),
    ("l4", f"{kit.CTA}!", kit.TEEN + " Hyped call to action."),
]
S = {n: Image.open(kit.SHOTS / f"{n}.png").convert("RGB") for n in ("11-workout-overview", "13-workout-player", "14-workout-rest", "16-streak", "18-badge-earned")}

def scenes(st):
    (s1, d1), (s2, d2), (s3, d3) = st["l1"], st["l2"], st["l3"]
    m1, m3 = s1 + d1 * 0.45, s3 + d3 * 0.45  # two cuts under each long line
    return lambda t: kit.shots(t, [
        (0, m1, dict(img=S["11-workout-overview"], z=(1.05, 1.15), f=(0.5, 0.75), at=(660, 2650))),  # tap "Start workout"
        (m1, s2 - 0.1, dict(img=S["13-workout-player"], z=(1.1, 1.25), f=(0.5, 0.4))),
        (s2 - 0.1, s3 - 0.1, dict(img=S["14-workout-rest"], z=(1, 1.15), f=(0.5, 0.45))),
        (s3 - 0.1, m3, dict(img=S["16-streak"], z=(1.1, 1.4), f=(0.5, 0.5))),
        (m3, None, dict(img=S["18-badge-earned"], z=(1, 1.1), f=(0.5, 0.45), flash=True))])

if __name__ == "__main__":
    kit.make(D, LINES, scenes, "Daily workouts, sleep and meals in one app.",
             "Energetic modern workout trap beat, punchy 808s, crisp claps, motivating and fresh, 140 BPM, about 25 seconds.")
