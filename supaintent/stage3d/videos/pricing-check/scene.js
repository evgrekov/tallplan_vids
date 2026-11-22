// "Before ChatGPT recommends you, it checks your pricing page": 1 in 11 ChatGPT searches target one vendor's site, 1 in 8 ask for official info.
// Source: SupaIntent, 17,962 recorded ChatGPT searches (fan-out queries), 2026.
import { C, anim, at, LINES as L, VO_END, text, image, card, onCard, logo, chip, crown, pop, slide, float, leave, cameraKeys, endcard, lockup } from "/web/engine.js";

export const LENGTH = Math.ceil(VO_END + 3);
const art = n => `/videos/pricing-check/art/${n}.png`;
const type = (o, s, t0, cps = 26) => anim(t => o.update(s.slice(0, Math.max(0, Math.floor((t - t0) * cps))) || " "));

cameraKeys([[0, [0, 0, 0], [0, 0, 0]], [L[1], [-0.3, 0.5, -1], [0, 1, 0]], [L[3], [0, 0, 0], [0, 0, 0]]]);

// 1. Hook: ChatGPT inspects the pricing page
pop(text([["BEFORE IT ", C.ink], ["RECOMMENDS\n", C.ink], ["IT CHECKS ", C.ink], ["YOUR PRICING", C.acc]], { size: 0.9, y: 6.1, z: 0.5 }), -0.3, { t1: L[1] - 0.1 });
const page = card({ w: 6.4, h: 3.4, y: 2.0, z: 0.2 });
onCard(page, text("yourbrand.com/pricing", { size: 0.38, color: C.grey, weight: 700 }), 0, 1.15);
[-1.9, 0, 1.9].forEach(x => onCard(page, card({ w: 1.7, h: 1.7, r: 0.2, color: "#e8edf6", depth: 0.03 }), x, -0.35));
float(slide(page, 0, [0, -1, -2], { dur: 0.6 }), { tilt: 0.05 }); leave(page, L[1] - 0.1, [-9, 0, 0]);
const gpt = card({ w: 1.5, h: 1.5, r: 0.75, y: 2.0, z: 1.2 }); onCard(gpt, logo("chatgpt", { size: 0.95 }));
anim(t => { gpt.position.x += 2.4 * Math.sin(t * 2.2); gpt.position.y += 0.4 * Math.cos(t * 3); });
pop(gpt, 0.3, { t1: L[1] - 0.2 });
const ceo = slide(image(art("ceo_magnifier"), { h: 6.4, x: 1.6, y: -4.8 }), 0, [6, 0, 0], { dur: 0.45 }); float(ceo, { amp: 0.04 }); leave(ceo, L[3], [7, 0, 0]);

// 2-3. One in eleven / one in eight: search bar typing + tile grids
function stat(t0, t1, big, n, query, sub) {
  const head = text(big, { size: 1.6, color: C.acc, y: 6.3, z: 0.5 }); pop(head, t0, { t1 });
  const s = text(sub, { size: 0.42, weight: 700, y: 5.0, z: 0.5 }); pop(s, t0 + 0.15, { t1 });
  const bar = card({ w: 7.6, h: 1.1, r: 0.55, y: 3.7, z: 0.3 }); pop(bar, t0 + 0.1, { t1 });
  const q = text(" ", { size: 0.4, weight: 600, align: "left", maxW: 6.6 }); onCard(bar, q, -3.3, 0); type(q, query, t0 + 0.3);
  for (let i = 0; i < n; i++) {
    const x = (i % 6 - 2.5) * 1.25, y = 2.2 - Math.floor(i / 6) * 1.4;
    const tile = card({ w: 1.0, h: 1.15, r: 0.15, color: i ? "#ffffff" : C.acc, depth: 0.08, x, y, z: 0.2 });
    pop(tile, t0 + 0.4 + i * 0.05, { t1 });
  }
}
stat(L[1], L[2] - 0.1, "1 IN 11", 11, "site:hubspot.com crm small business pricing", "ChatGPT searches one vendor's own site");
stat(L[2], L[3] - 0.1, "1 IN 8", 8, "[brand] official pricing", "searches ask for official information");

// 4. Hidden pricing loses
pop(text([["HIDE IT, ", C.ink], ["LOSE IT", C.red]], { size: 1.0, y: 6.4, z: 0.5 }), L[3], { t1: L[4] - 0.1 });
const hidden = card({ w: 3.7, h: 3.2, x: -2.05, y: 2.6, z: 0.2, color: "#e4e7ec" });
onCard(hidden, text("Pricing", { size: 0.4, color: C.grey }), 0, 0.9); onCard(hidden, text("Contact\nsales", { size: 0.5, color: C.grey }), 0, -0.3);
const shown = card({ w: 3.7, h: 3.2, x: 2.05, y: 2.6, z: 0.2 });
onCard(shown, text("Pricing", { size: 0.4, color: C.grey }), 0, 0.9); onCard(shown, text("Clear plans\n$ / month", { size: 0.5, color: C.acc }), 0, -0.3);
for (const c of [hidden, shown]) { pop(c, L[3] + (c === shown ? 0.2 : 0)); leave(c, L[4] - 0.1, [0, 9, 0]); float(c, { phase: c === shown ? 1 : 0 }); }
const cr = crown({ s: 0.5, x: 2.05, y: 4.7, z: 0.6 }); pop(cr, at("wins")); leave(cr, L[4] - 0.1, [0, 9, 0]);
const hide = slide(image(art("marketer_hiding"), { h: 6.4, x: -1.6, y: -4.8 }), L[3], [-6, 0, 0]); float(hide, { amp: 0.04 }); leave(hide, L[4], [-7, 0, 0]);

// 5. CTA
const cta = card({ w: 7.4, h: 3.6, y: 3.2, z: 0.4 });
onCard(cta, lockup({ size: 0.6 }), 0, 0.8);
onCard(cta, text("the real searches behind your prompts", { size: 0.36, weight: 700 }), 0, -0.3);
onCard(cta, logo("chatgpt", { size: 0.8 }), 0, -1.2);
pop(cta, L[4]); float(cta, { tilt: 0.05 });
const point = slide(image(art("marketer_point"), { h: 6.4, x: -1.2, y: -4.8 }), L[4], [-6, 0, 0]); float(point, { amp: 0.04 });

endcard(VO_END + 0.2, "See what ChatGPT searches about your brand.");
