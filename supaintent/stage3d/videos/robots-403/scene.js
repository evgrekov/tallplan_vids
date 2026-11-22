// "robots.txt says yes, the server says no": test AI crawler access with the bot's User-Agent and look for a 200.
// Source: SupaIntent GEO guide (robots.txt can allow a crawler while hosting still returns a 403).
import { C, anim, at, LINES as L, VO_END, text, image, card, onCard, logo, chip, pop, slide, float, leave, cameraKeys, endcard, lockup } from "/web/engine.js";

export const LENGTH = Math.ceil(VO_END + 3);
const art = n => `/videos/robots-403/art/${n}.png`;
const GREEN = "#16a34a", TERM = "#0f172a";
const type = (o, s, t0, cps = 30) => anim(t => o.update(s.slice(0, Math.max(0, Math.floor((t - t0) * cps))) || " "));

cameraKeys([[0, [0, 0, 0], [0, 0, 0]], [at("slam"), [0, 0.3, -0.8], [0, 1.5, 0]], [L[2], [0.2, 0.6, -1.2], [0, 1.2, 0]], [L[3], [0, 0, 0], [0, 0, 0]]]);

// 1. Hook: robots.txt allows, the server door slams
pop(text([["ROBOTS.TXT: ", C.ink], ["YES", GREEN]], { size: 1.0, y: 6.6, z: 0.5 }), -0.3, { t1: L[1] - 0.1 });
const rob = card({ w: 6.4, h: 2.6, y: 3.9, z: 0.2 });
onCard(rob, text("User-agent: GPTBot", { size: 0.48, weight: 700, align: "left" }), -2.7, 0.45);
onCard(rob, text("Allow: /", { size: 0.48, weight: 700, color: GREEN, align: "left" }), -2.7, -0.45);
float(slide(rob, 0, [0, -1, -2], { dur: 0.6 })); leave(rob, L[1] - 0.1, [-9, 0, 0]);
const srv = text([["SERVER: ", C.ink], ["NO", C.red]], { size: 1.0, y: 1.3, z: 0.6 });
slide(srv, at("slam"), [0, 6, 0], { dur: 0.25 }); leave(srv, L[1] - 0.1, [9, 0, 0]);
anim(t => { const k = t - at("slam") - 0.25; if (k > 0 && k < 0.3) srv.position.x += 0.15 * Math.sin(k * 90) * (1 - k / 0.3); });
const ok = slide(image(art("dev_confident"), { h: 6.4, x: -1.5, y: -4.8 }), 0, [-6, 0, 0], { dur: 0.45 }); float(ok, { amp: 0.04 }); leave(ok, L[1], [-7, 0, 0]);

// 2. 403 for AI crawlers
const e403 = card({ w: 6.8, h: 4.6, y: 3.4, z: 0.3, color: C.red });
onCard(e403, text("403", { size: 2.6, color: "#ffffff" }), 0, 0.5);
onCard(e403, text("Forbidden for AI crawlers", { size: 0.42, color: "#ffffff", weight: 700 }), 0, -1.4);
slide(pop(e403, L[1], { dur: 0.25 }), L[1], [0, 0, 4], { dur: 0.25 }); float(e403); leave(e403, L[2] - 0.1, [0, 9, 0]);
const palm = slide(image(art("dev_facepalm"), { h: 6.4, x: 1.5, y: -4.8 }), L[1] + 0.1, [6, 0, 0]); float(palm, { amp: 0.04 }); leave(palm, L[2], [7, 0, 0]);

// 3. Test like the bot: curl with GPTBot's User-Agent → 200
pop(text("TEST LIKE THE BOT", { size: 0.9, y: 6.8, z: 0.5 }), L[2], { t1: L[3] - 0.1 });
const term = card({ w: 8.0, h: 4.2, y: 3.2, z: 0.2, color: TERM });
const cmd = text(" ", { size: 0.36, weight: 600, color: "#e2e8f0", align: "left", maxW: 7.2 }); onCard(term, cmd, -3.6, 1.1);
type(cmd, '$ curl -A "GPTBot" -sI yoursite.com', L[2] + 0.4);
const res = text("HTTP/2 200", { size: 0.9, color: "#4ade80", align: "left" }); onCard(term, res, -3.6, -0.6);
anim(t => { res.visible = t >= at("two") - 0.1; });
pop(term, L[2]); float(term, { tilt: 0.04 }); leave(term, L[3] - 0.1, [0, 9, 0]);
const typing = slide(image(art("dev_typing"), { h: 5.2, x: 0, y: -5.2 }), L[2] + 0.2, [0, -5, 0]); float(typing, { amp: 0.03 }); leave(typing, L[4], [0, -7, 0]);

// 4. Can't read = can't cite
const t1 = text([["CAN'T READ IT?\n", C.ink], ["CAN'T CITE IT.", C.red]], { size: 1.0, y: 4.6, z: 0.5 });
pop(t1, L[3], { t1: L[4] - 0.1 });
["chatgpt", "gemini", "google-ai-mode", "perplexity"].forEach((n, i) => {
  const c = card({ w: 1.5, h: 1.5, r: 0.75, x: (i - 1.5) * 1.9, y: 1.6, z: 0.3 }); onCard(c, logo(n, { size: 0.9 }));
  pop(c, L[3] + 0.3 + i * 0.1, { t1: L[4] - 0.1 }); float(c, { phase: i });
});

// 5. CTA
const cta = card({ w: 7.4, h: 3.2, y: 3.4, z: 0.4 });
onCard(cta, lockup({ size: 0.62 }), 0, 0.6);
onCard(cta, text("Does AI name your brand?", { size: 0.42, weight: 700 }), 0, -0.6);
pop(cta, L[4]); float(cta, { tilt: 0.05 });
const back = slide(image(art("dev_confident"), { h: 6.4, x: 1.5, y: -4.8 }), L[4], [6, 0, 0]); float(back, { amp: 0.04 });

endcard(VO_END + 0.2, "Check whether AI names your brand.");
