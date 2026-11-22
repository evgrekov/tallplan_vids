# TikTok script v2: "How to rank in ChatGPT"

Format: vertical 9:16, ~32 s, same style as the YouTube video: Gemini TTS "Puck" slowed 10%, karaoke captions, zooms into screenshots with the spoken row highlighted, SupaIntent end card.
Rules: real logos only (repo or official sites), mobile screenshots of the sites and the tool.

## What changed after the YouTube Shorts feedback

1. **The first second must stop the swipe.** v1 opened with a calm question. v2 opens on a high-contrast frame and a bold claim: a real ChatGPT answer whose sources are all third-party "best CRM" lists, plus "ChatGPT isn't reading your website".
2. **Pay off inside the video.** Every promise is delivered on screen (the 3 steps, with the real sources and numbers). The CTA only offers the next thing (check your own niche), never the answer we held back.
3. **Shorter.** ~32 s instead of ~40 s: the "answer in one sentence" step is merged into step 3, the intro counter is cut down.

## Script

| # | Time | Visual | Voiceover | On-screen |
|---|---|---|---|---|
| 1 | 0–2.5 s | **High contrast from frame 1:** real ChatGPT answer "best CRM for startups" (`chatgpt-best-crm-answer-mobile.jpg`: Attio, HubSpot…), hard cut to its sources (`chatgpt-best-crm-sources-mobile.jpg`): every source is a "Best CRM for Startups" article, no CRM's own site. Sources flash yellow one by one. | "ChatGPT isn't reading your website." | **ChatGPT isn't reading your website** |
| 2 | 2.5–7 s | Top Citation Domains, ChatGPT tab (mobile). Zoom + highlight: G2 24% → Trustpilot 12% → Capterra 11% → Reddit 6%. Small "162,000 AI answers" badge. | "We checked 162,000 AI answers. It reads G2, Trustpilot, Capterra and Reddit." | **It reads what others say about you** |
| 3 | 7–12 s | Step 1: real G2, Capterra, Trustpilot logos pop in as a checklist, then the Reddit logo with the reddit.com row from the tool. | "So, step one: reviews on G2 and Capterra, and real answers in Reddit threads." | **1. Reviews + Reddit** |
| 4 | 12–17 s | Step 2: the Emergent listicle that ChatGPT cited (`listicle-emergent-title-mobile.jpg`), then its list (`listicle-emergent-list-mobile.jpg`): Attio, Pipedrive, Zoho, Close highlighted, the same brands ChatGPT recommended. | "Step two: get into the 'best tools' lists. ChatGPT copies them." | **2. Get on "best X" lists** |
| 5 | 17–23 s | Step 3: your page on mobile, H2 as a question, the first sentence highlighted as a quote box with a number. | "Step three: on your site, answer the question in one sentence, with a real number. That's the line it quotes." | **3. One-sentence answer + a number** |
| 6 | 23–28 s | SupaIntent prompt tracking (mobile): same prompt on two days, brands shuffle, counter "~30% gone". | "And check daily: about a third of today's brands are gone tomorrow." | **~30% change overnight** |
| 7 | 28–32 s | End card, SupaIntent logo. | "See who ChatGPT cites in your niche, free, at SupaIntent." | **supaintent.com/tools/top-domains** |

~85 words, ~32 s at the slowed pace. The hook claim (scene 1) is paid off by scene 2's data within 5 seconds; all three steps are fully shown before the CTA.

## Data behind each claim

| Claim | Source |
|---|---|
| 162,000 AI answers | SupaIntent dataset, Aug–Oct 2026 |
| G2 24%, Trustpilot 12%, Capterra 11%, Reddit 6% of ChatGPT answers | Top AI Citation Domains tool, ChatGPT tab, Nov 1, 2026 |
| ~30% of brands gone the next day | SupaIntent prompt tracking, ~54,000 answers, Sep 15–Oct 15, 2026 (`/blog/ai-prompt-tracking`) |
| "Best X" lists matter | Seer Interactive: listicles ≈ 16.6% of 2M ChatGPT citations |
| One clear answer + numbers get quoted | Princeton GEO paper: adding statistics and citing sources were the top tactics |

"ChatGPT isn't reading your website" is a hook simplification of "its top sources are third-party sites"; scene 2 shows the evidence right away.

## Assets collected (Nov 3, 2026, mobile 375 px)

| File | What it is |
|---|---|
| `screenshots/chatgpt-best-crm-answer-mobile.jpg` | ChatGPT (logged out) answer to "best CRM for startups": Attio #1, HubSpot. All screenshots in light theme |
| `screenshots/chatgpt-best-crm-sources-mobile.jpg` | Its sources: SoftwareCompare.net, saaslete, Emergent, TechRadar; all "Best CRM for Startups" lists, no vendor site |
| `screenshots/listicle-emergent-title-mobile.jpg`, `listicle-emergent-list-mobile.jpg` | emergent.sh "8 Best CRMs for Startups in 2026", one of the cited sources, and its list |
| `screenshots/top-domains-chatgpt-tab-mobile.jpg` | Top Domains, ChatGPT tab, Nov 2, 2026: G2 24%, Trustpilot 12%, Capterra 11%, BBB 6%, Reddit 6% |
| `screenshots/top-domains-chatgpt-list-mobile.jpg` | Same, top 12 |
| `logos/` | Real logos: SupaIntent and G2, ChatGPT (from the site repo); Reddit, Trustpilot, Capterra (official favicons) |

Still missing:
- Reddit thread: reddit.com is blocked in my browser; scene 3 uses the Reddit row from the tool instead.
- Prompt tracking (scene 6) needs the logged-in app; only desktop screenshots exist in `public/images/blog/ai-prompt-tracking/`.
- Capterra logo is only 48 px (their site blocks downloads); fine as a small icon.
