// "Your first question never gets an ad": ChatGPT shows ads only on a follow-up turn (US only).
// Source: SupaIntent AI Runs (price / where-to-buy follow-ups return ads in ~16-19% of requests) and Ads Radar feed
// (2026-11-22: 4,697 ChatGPT ad creatives, 1,688 advertisers, 100% of appearances US). Ad copy below is real, from the feed.
import { C, ease, anim, at, LINES as L, VO_END, text, image, card, onCard, logo, chip, pop, slide, float, leave, cameraKeys, endcard, lockup } from "/web/engine.js";

export const LENGTH = Math.ceil(VO_END + 3);
const art = n => `/videos/ads-follow-up/art/${n}.png`;
const GREEN = "#16a34a", SOFT = "#e8edf6";
const type = (o, s, t0, cps = 28) => anim(t => o.update(s.slice(0, Math.max(0, Math.floor((t - t0) * cps))) || " "));

cameraKeys([[0, [0, 0, 0], [0, 0, 0]], [L[1], [0.2, 0.5, -0.9], [0, 1.6, 0]], [L[3], [0, 0, 0], [0, 0, 0]], [L[5], [-0.2, 0.4, -0.8], [0, 1.5, 0]], [L[6], [0, 0, 0], [0, 0, 0]]]);

/** Chat bubble: right-aligned user question that types itself. */
function ask(q, t0, y) {
  const b = card({ w: 6.2, h: 1.0, r: 0.5, x: 1.0, y, z: 0.3, color: C.acc, depth: 0.06 });
  const tx = text(" ", { size: 0.36, weight: 700, color: "#ffffff", align: "left", maxW: 5.6 }); onCard(b, tx, -2.8, 0);
  type(tx, q, t0 + 0.15); return pop(b, t0);
}
/** Grey answer lines with the ChatGPT logo. */
function answer(t0, y) {
  const a = card({ w: 7.6, h: 1.9, x: -0.2, y, z: 0.25 });
  onCard(a, logo("chatgpt", { size: 0.6 }), -3.2, 0.45);
  [[0.45, 5.6], [-0.05, 6.4], [-0.55, 4.4]].forEach(([yy, w]) => onCard(a, card({ w, h: 0.22, r: 0.11, color: SOFT, depth: 0.02 }), -2.7 + w / 2, yy));
  return pop(a, t0);
}
/** Sponsored card with real ad copy. */
function ad(brand, title, desc, t0, y, color = C.ink) {
  const c = card({ w: 7.6, h: 2.5, x: -0.2, y, z: 0.4 });
  onCard(c, chip("Sponsored", { bg: C.gold, fg: C.ink, size: 0.26 }), -2.5, 0.75);
  onCard(c, text(brand, { size: 0.34, weight: 700, color: C.grey, align: "left" }), -1.2, 0.75);
  onCard(c, text(title, { size: 0.42, weight: 800, color, align: "left", maxW: 6.8 }), -3.4, 0.05);
  onCard(c, text(desc, { size: 0.3, weight: 600, color: C.grey, align: "left", maxW: 6.8 }), -3.4, -0.65);
  return slide(pop(c, t0, { dur: 0.3 }), t0, [0, 0, 3], { dur: 0.3 });
}

// 1. Hook: first question, clean answer, no ad
pop(text([["FIRST QUESTION:\n", C.ink], ["NO ADS", GREEN]], { size: 0.95, y: 6.6, z: 0.5 }), -0.3, { t1: L[1] - 0.1 });
const q1 = ask("Best CRM for a small team?", 0.1, 4.4), a1 = answer(0.6, 2.6);
const ok = chip("No ads", { bg: GREEN, size: 0.32, x: 2.4, y: 1.3, z: 0.6 }); pop(ok, at("ad") - 0.1, { t1: L[1] - 0.1 });
float(q1, { amp: 0.03 }); leave(q1, L[1], [0, 9, 0]);
float(a1, { amp: 0.03 }); leave(a1, L[3] - 0.1, [0, 9, 0]);
const typing = slide(image(art("marketer_typing"), { h: 6.4, x: -1.5, y: -4.8 }), 0, [-6, 0, 0], { dur: 0.45 }); float(typing, { amp: 0.04 }); leave(typing, L[1], [-7, 0, 0]);

// 2. The follow-up: the first answer scrolls up, the second one comes with a sponsored card
anim(t => { a1.position.y += 3.4 * ease((t - L[1]) / 0.5); });
const q2 = ask("How much does it cost?", L[1] + 0.1, 4.1);
const ad1 = ad("monday CRM", "CRM priced for sales teams of 3 to 20", "Plans start at 3 seats. See the full price for your team.", at("wait") + 0.5, 1.9);
for (const o of [q2, ad1]) { float(o, { amp: 0.03, phase: 1 }); leave(o, L[3] - 0.1, [0, 9, 0]); }
const wow = slide(image(art("marketer_surprised"), { h: 6.4, x: 1.5, y: -4.8 }), L[1], [6, 0, 0]); float(wow, { amp: 0.04 }); leave(wow, L[3], [7, 0, 0]);

// 3. About one in six: tile row, one tile is an ad
pop(text("1 IN 6", { size: 1.7, color: C.acc, y: 6.3, z: 0.5 }), L[3], { t1: L[4] - 0.1 });
pop(text("price & where-to-buy follow-ups\nget a sponsored card", { size: 0.42, weight: 700, y: 4.6, z: 0.5 }), L[3] + 0.15, { t1: L[4] - 0.1 });
for (let i = 0; i < 6; i++) {
  const tile = card({ w: 1.15, h: 1.5, r: 0.18, color: i === 3 ? C.gold : "#ffffff", depth: 0.08, x: (i - 2.5) * 1.35, y: 2.4, z: 0.2 });
  if (i === 3) onCard(tile, text("AD", { size: 0.42, color: C.ink }), 0, 0);
  pop(tile, L[3] + 0.4 + i * 0.08, { t1: L[4] - 0.1 }); float(tile, { phase: i, amp: 0.04 });
}
const point = slide(image(art("marketer_typing"), { h: 6.4, x: -1.5, y: -4.8 }), L[3] + 0.1, [-6, 0, 0]); float(point, { amp: 0.04 }); leave(point, L[4], [-7, 0, 0]);

// 4. 4,700 ads, ~1,700 advertisers, all US: counter
const n = text("0", { size: 1.8, color: C.acc, y: 6.2, z: 0.5 });
anim(t => n.update(Math.round(4697 * Math.min(Math.max((t - L[4] - 0.2) / 1.6, 0), 1)).toLocaleString("en-US")));
pop(n, L[4], { t1: L[5] - 0.1 });
pop(text("ChatGPT ads logged", { size: 0.5, weight: 700, y: 4.8, z: 0.5 }), L[4] + 0.15, { t1: L[5] - 0.1 });
const c1 = chip("1,688 advertisers", { bg: C.ink, size: 0.38, x: -1.9, y: 3.4, z: 0.5 }), c2 = chip("100% US", { bg: C.red, size: 0.38, x: 2.4, y: 3.4, z: 0.5 });
pop(c1, at("seventeen") - 0.2, { t1: L[5] - 0.1 }); pop(c2, at("US", -1) - 0.1, { t1: L[5] - 0.1 });
const gpt = card({ w: 1.6, h: 1.6, r: 0.8, y: 1.6, z: 0.4 }); onCard(gpt, logo("chatgpt", { size: 1.0 })); pop(gpt, L[4] + 0.3, { t1: L[5] - 0.1 }); float(gpt);
const scroll = slide(image(art("ceo_scroll"), { h: 6.4, x: 0, y: -4.8 }), L[4] + 0.1, [0, -6, 0]); float(scroll, { amp: 0.03 }); leave(scroll, L[5], [0, -8, 0]);

// 5. Even OpenAI advertises its Ads Manager inside ChatGPT
pop(text([["EVEN ", C.ink], ["OPENAI", C.acc], [" BUYS ADS", C.ink]], { size: 0.85, y: 6.6, z: 0.5 }), L[5], { t1: L[6] - 0.1 });
const ad2 = ad("OpenAI", "OpenAI Ads Manager", "Launch your first ad campaign today.", L[5] + 0.3, 3.4);
float(ad2, { amp: 0.04, tilt: 0.05 }); leave(ad2, L[6] - 0.1, [0, 9, 0]);
const laugh = slide(image(art("marketer_laugh"), { h: 6.4, x: 1.5, y: -4.8 }), L[5], [6, 0, 0]); float(laugh, { amp: 0.04 }); leave(laugh, L[6], [7, 0, 0]);

// 6. CTA
const cta = card({ w: 7.4, h: 3.6, y: 3.2, z: 0.4 });
onCard(cta, lockup({ size: 0.6 }), 0, 0.8);
onCard(cta, text("Which ads show up next to your brand?", { size: 0.36, weight: 700 }), 0, -0.3);
onCard(cta, logo("chatgpt", { size: 0.8 }), 0, -1.2);
pop(cta, L[6]); float(cta, { tilt: 0.05 });
const back = slide(image(art("marketer_typing"), { h: 6.4, x: -1.4, y: -4.8 }), L[6], [-6, 0, 0]); float(back, { amp: 0.04 });

endcard(VO_END + 0.2, "See which ads show up next to your brand.");
