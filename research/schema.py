"""Draft codebook for the TT farm sheet. Prints JSON payloads for headers, codebook and formula rows.
Usage: schema.py headers|codebook|cols"""
import json, string, sys

def col(i):  # 0 -> A
    return string.ascii_uppercase[i] if i < 26 else string.ascii_uppercase[i // 26 - 1] + string.ascii_uppercase[i % 26]

# (column, layer, meaning, allowed values)
REFVIDS = [
    ("post_id", "id", "TikTok video id", "digits"),
    ("handle", "id", "channel handle, matches Refs", "@handle"),
    ("url", "id", "video link", "url"),
    ("posted", "id", "publish date (UTC)", "yyyy-mm-dd"),
    ("duration_s", "form", "length in seconds", "number"),
    ("views", "stats", "views in the latest Stats snapshot", "formula"),
    ("likes", "stats", "likes, latest snapshot", "formula"),
    ("comments", "stats", "comments, latest snapshot", "formula"),
    ("shares", "stats", "reposts, latest snapshot", "formula"),
    ("saves", "stats", "saves, latest snapshot", "formula"),
    ("engagement_rate", "stats", "(likes + comments + shares + saves) / views, the main quality signal", "formula"),
    ("x_channel_median", "stats", "views / channel median views (Refs)", "formula"),
    ("like_rate", "stats", "likes / views", "formula"),
    ("comment_rate", "stats", "comments / views", "formula"),
    ("save_rate", "stats", "saves / views; high = useful, people come back", "formula"),
    ("share_rate", "stats", "shares / views", "formula"),
    ("scraped", "stats", "date of the latest snapshot in Stats", "formula"),
    ("format", "what", "overall format", "talking head / slides / 3d animation / stop-motion / screen recording / grid / footage cuts"),
    ("character", "what", "who is on screen", "short name, matches 02_sources/characters/<slug>"),
    ("character_style", "what", "how the character is made", "real person / photoreal 3d / stylized 3d / 2d cartoon / mannequin / none"),
    ("character_gender", "what", "gender read of the character", "male / female / both / neutral / none"),
    ("character_age", "what", "apparent age", "teen / 18-25 / older / n/a"),
    ("person_ethnicity", "what", "apparent ethnicity of the person on screen", "white / black / asian / latino / middle eastern / south asian / mixed / n/a"),
    ("hair", "what", "hair: color, length, style", "text or n/a"),
    ("outfit", "what", "clothes", "text or none"),
    ("accessories", "what", "glasses, rings, bracelets, chains, hats", "comma separated or none"),
    ("standout_object", "what", "anything that catches the eye: mic in hand, bright or unusual object", "text or none"),
    ("on_camera_speech", "what", "does the person speak on camera", "talks to camera / voiceover / silent / no person"),
    ("background", "what", "main backdrop", "bedroom / apartment / car / gym / street / nature / studio / solid color (name) / green screen / mixed"),
    ("background_motion", "what", "does the background move", "static / camera moves / scene moves / green screen"),
    ("location_switch", "what", "jumps to a different, often realistic, place", "yes / no"),
    ("character_vibe", "feel", "first impression of the character", "cute / creepy / cute-creepy / cool / funny / neutral"),
    ("character_novelty", "feel", "how unusual the character is in the feed", "common / unusual / strange"),
    ("eyes", "feel", "eyes of the character", "none / normal / oversized cartoon"),
    ("eye_contact", "feel", "looks into the camera", "yes / no"),
    ("expressiveness", "feel", "how the character acts", "static / poses / gestures and reactions"),
    ("emotion", "feel", "main emotion the viewer gets", "curiosity / fear of missing out / hope / humor / inspiration / controversy"),
    ("emotional_arc", "feel", "how emotion moves through the video", "free text, a → b → c"),
    ("humor", "feel", "humor present", "none / light / main"),
    ("honesty", "feel", "admits limits or realistic expectations", "yes / no"),
    ("address", "feel", "how it talks to the viewer", "you + slang / you neutral / third person / none"),
    ("hook_text", "craft", "words of the first 2 s (voice or text)", "text"),
    ("hook_type", "craft", "hook mechanics", "question about viewer / promise of result / shock fact / you are doing it wrong / before-after / trend"),
    ("hook_visual", "craft", "what is on screen in the first 2 s", "text"),
    ("result_shown_first", "craft", "the promised result is shown in the first frames", "yes / no"),
    ("literal_visuals", "craft", "picture illustrates the spoken word at that moment", "yes / partly / no"),
    ("color_coding", "craft", "colors carry meaning (problem / fixed)", "text or no"),
    ("xray_highlight", "craft", "glowing body part, x-ray view", "yes / no"),
    ("social_proof_scene", "craft", "other people react on screen", "yes / no"),
    ("props_with_text", "craft", "text written on objects in the scene", "yes / no"),
    ("caption_layers", "craft", "kinds of on-screen text", "word-by-word / title / labels, comma separated"),
    ("caption_style", "craft", "look of the main captions", "color, stroke, position"),
    ("visual_change_s", "craft", "seconds between visual changes (cut, angle, zoom)", "number"),
    ("hard_cuts", "craft", "hard cuts found by scene detection", "number"),
    ("camera", "craft", "camera behaviour", "static / push-ins / orbit / handheld"),
    ("voice", "craft", "voice type", "none / male / female / ai male / ai female"),
    ("voice_effect", "craft", "voice processing", "none / pitched up / pitched down / robotic / sped up / unchecked"),
    ("voice_wpm", "craft", "speech speed, words per minute", "number"),
    ("music_bed", "craft", "music under the voice", "none / quiet / loud"),
    ("structure", "craft", "story structure", "listicle / story / myth-fact / before-after / tutorial / skit"),
    ("items_count", "craft", "number of list items", "number"),
    ("explains_why", "craft", "explains why each item works", "yes / no"),
    ("twist_end", "craft", "turn at the end (brutal truth, reveal)", "text or no"),
    ("specifics", "craft", "concrete numbers in the script", "text or no"),
    ("exotic_names", "craft", "unusual or foreign exercise names", "yes / no"),
    ("cta", "craft", "call to action", "none / follow / comment / link / app"),
    ("typos", "craft", "visible typos in text", "yes / no"),
    ("lang", "form", "spoken language", "en / es / ru ..."),
    ("sound_id", "sound", "TikTok music id, matches Music", "digits"),
    ("description", "pack", "post caption", "text"),
    ("hashtags", "pack", "hashtags", "text"),
    ("top_comments", "insight", "what the top comments say (Bright Data Comments)", "text"),
    ("why_it_works", "insight", "our reading of why it got its numbers", "text"),
    ("transcript", "insight", "speech, local Whisper", "text"),
    ("drive_video", "files", "saved video on Drive", "path in 02_sources/references/tiktok"),
]
HEAD = [c[0] for c in REFVIDS]
C = {name: col(i) for i, name in enumerate(HEAD)}
LAYERS = {}  # layer -> (first index, end index)
for i, (_, layer, _, _) in enumerate(REFVIDS):
    a, _ = LAYERS.get(layer, (i, i)); LAYERS[layer] = (a, i + 1)

STATS = ["date", "kind", "post_id", "handle", "views", "likes", "comments", "shares", "saves", "engagement_rate", "age_days"]
CHANNELS = ["date", "handle", "followers", "videos", "total_likes", "posts_scraped", "median_views", "max_views", "source"]
REFS = ["handle", "url", "nickname", "niche", "format", "character", "why_interesting", "followers", "videos",
        "total_likes", "posts_scraped", "median_views", "top_views", "top_post_url", "created", "lang", "added", "last_scraped", "notes"]
MUSIC = ["sound_id", "title", "author", "type", "has_voice", "music_bed", "used_in", "median_views", "best_views", "best_video", "drive_audio", "notes"]

def refvids_formulas(r):
    """Stats columns of a RefVids row r: latest snapshot from the Stats journal + rates."""
    q = f"${C['scraped']}{r}"
    # FILTER with = (not SUMIFS/MAXIFS criteria): 19-digit ids must match as exact text, not as rounded numbers
    f = {"scraped": f"=IFERROR(MAX(FILTER(Stats!$A:$A,Stats!$C:$C=$A{r})),\"\")"}
    for name, src in zip(["views", "likes", "comments", "shares", "saves"], "EFGHI"):
        f[name] = f"=IFERROR(INDEX(FILTER(Stats!{src}:{src},Stats!$C:$C=$A{r},Stats!$A:$A={q}),1),0)"
    v = f"{C['views']}{r}"
    tot = "+".join(f"{C[n]}{r}" for n in ["likes", "comments", "shares", "saves"])
    f["engagement_rate"] = f"=IF({v}=0,0,({tot})/{v})"
    f["x_channel_median"] = f"={v}/XLOOKUP($B{r},Refs!$A:$A,Refs!$L:$L)"
    for name, src in [("like_rate", "likes"), ("comment_rate", "comments"), ("save_rate", "saves"), ("share_rate", "shares")]:
        f[name] = f"=IF({v}=0,0,{C[src]}{r}/{v})"
    return f

def stats_formulas(r):
    return {"engagement_rate": f"=IF(E{r}=0,0,(F{r}+G{r}+H{r}+I{r})/E{r})",
            "age_days": f"=IF(B{r}=\"ref\",A{r}-XLOOKUP(C{r},RefVids!$A:$A,RefVids!$D:$D),\"\")"}

def refs_formulas(r):
    f = {"last_scraped": f"=MAXIFS(ChannelStats!$A:$A,ChannelStats!$B:$B,$A{r})"}
    for name, src in zip(["followers", "videos", "total_likes", "posts_scraped", "median_views"], "CDEFG"):
        f[name] = f"=SUMIFS(ChannelStats!{src}:{src},ChannelStats!$B:$B,$A{r},ChannelStats!$A:$A,$R{r})"
    f["top_views"] = f"=MAXIFS(RefVids!${C['views']}:${C['views']},RefVids!$B:$B,$A{r})"
    f["top_post_url"] = f"=IFERROR(INDEX(FILTER(RefVids!$C:$C,RefVids!$B:$B=$A{r},RefVids!${C['views']}:${C['views']}=$M{r}),1),\"\")"
    return f

def music_formulas(r):
    s, v = f"RefVids!${C['sound_id']}:${C['sound_id']}", f"RefVids!${C['views']}:${C['views']}"
    return {"used_in": f"=SUMPRODUCT({s}=$A{r})", "median_views": f"=IFERROR(MEDIAN(FILTER({v},{s}=$A{r})),\"\")",
            "best_views": f"=IFERROR(MAX(FILTER({v},{s}=$A{r})),0)", "best_video": f"=IFERROR(INDEX(FILTER(RefVids!$C:$C,{s}=$A{r},{v}=$I{r}),1),\"\")"}

if __name__ == "__main__":
    what = sys.argv[1]
    if what == "codebook":
        print(json.dumps([["column", "letter", "layer", "meaning", "values"]] + [[n, C[n], l, m, v] for n, l, m, v in REFVIDS], ensure_ascii=False))
    elif what == "cols":
        print(json.dumps(C), json.dumps(LAYERS))
    elif what == "headers":
        print(json.dumps({"refvids": HEAD, "stats": STATS, "channels": CHANNELS, "refs": REFS, "music": MUSIC}))
