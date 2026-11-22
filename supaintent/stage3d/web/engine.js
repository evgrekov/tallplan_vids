// 3D layout engine: a lit stage with shadows; every element has a base transform and timeline animators on top.
// Units: 1 world unit = 120 px at z = 0 (frame is 9 x 16 units).
import * as THREE from "three";

export const W = 1080, H = 1920, U = 120;
export const C = { bg: "#eef1f7", ink: "#101828", grey: "#667085", acc: "#2563eb", red: "#ef4444", brand: "#0053db", brandInk: "#10202b", gold: "#f5b301" };

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H); renderer.setPixelRatio(1);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);

export const scene = new THREE.Scene();
scene.background = new THREE.Color(C.bg);
export const camera = new THREE.PerspectiveCamera(30, W / H, 0.1, 200);
const DIST = 8 / Math.tan(THREE.MathUtils.degToRad(15));

scene.add(new THREE.HemisphereLight("#ffffff", "#c9d1e3", 2.2));
const sun = new THREE.DirectionalLight("#ffffff", 1.6);
sun.position.set(-6, 10, 14); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); sun.shadow.radius = 6;
Object.assign(sun.shadow.camera, { left: -12, right: 12, top: 14, bottom: -14, near: 1, far: 60 });
scene.add(sun);
const wall = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.ShadowMaterial({ opacity: 0.12 }));
wall.position.z = -0.6; wall.receiveShadow = true; scene.add(wall);  // invisible backdrop that catches soft shadows

// dot grid on the backdrop
{
  const c = document.createElement("canvas"); c.width = c.height = 64; const g = c.getContext("2d");
  g.fillStyle = "#d6dce8"; g.beginPath(); g.arc(32, 32, 3, 0, 7); g.fill();
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(40, 40);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshBasicMaterial({ map: t, transparent: true }));
  m.position.z = -0.61; scene.add(m);
}

// ---------- timeline ----------
const WORDS = window.WORDS;
/** Start time of the n-th spoken occurrence of a word (n = -1 for the last). */
const norm = w => w.replace(/[.,?!:;'"]/g, "").toLowerCase();
export const at = (w, n = 0) => {
  const hit = WORDS.filter(x => norm(x.w) === norm(w)).at(n);
  if (!hit) throw new Error(`word not spoken: ${w} #${n}`);
  return hit.s;
};
export const LINES = window.SHOTS.map(s => s.start).concat(window.SHOTS.at(-1).end);
export const VO_END = window.SHOTS.at(-1).end;
const items = [], animators = [];
export const ease = x => (x = Math.min(Math.max(x, 0), 1), 1 - (1 - x) ** 3);
export const smooth = x => (x = Math.min(Math.max(x, 0), 1), x * x * (3 - 2 * x));
const back = x => (x = Math.min(Math.max(x, 0), 1), 1 + 2.2 * (x - 1) ** 3 + 1.2 * (x - 1) ** 2);
export const anim = fn => animators.push(fn);

function track(obj, x = 0, y = 0, z = 0) {
  obj.position.set(x, y, z);
  obj.userData.base = { p: obj.position.clone(), r: obj.rotation.clone(), s: obj.scale.clone() };
  items.push(obj); scene.add(obj); return obj;
}

/** Visible from t0 with an overshoot scale-in; optional exit at t1. */
export function pop(o, t0, { dur = 0.35, t1 = Infinity } = {}) {
  anim(t => {
    o.visible &&= t >= t0 && t < t1 + 0.25;
    const k = back((t - t0) / dur) * (t > t1 ? 1 - ease((t - t1) / 0.25) : 1);
    o.scale.multiplyScalar(Math.max(k, 1e-3));
  });
  return o;
}
/** Slide in from an offset (world units) over dur. */
export function slide(o, t0, [dx, dy, dz = 0], { dur = 0.5 } = {}) {
  anim(t => { o.visible &&= t >= t0; const e = 1 - ease((t - t0) / dur); o.position.x += dx * e; o.position.y += dy * e; o.position.z += dz * e; });
  return o;
}
/** Rotate around y by `turns` (e.g. a card flip) during [t0, t0+dur]. */
export function flip(o, t0, { turns = 1, dur = 0.6, axis = "y" } = {}) {
  anim(t => { o.rotation[axis] += 2 * Math.PI * turns * (1 - smooth((t - t0) / dur)); });
  return o;
}
/** Gentle idle float so nothing is ever frozen. */
export function float(o, { amp = 0.06, speed = 1.3, phase = 0, tilt = 0.03 } = {}) {
  anim(t => { o.position.y += amp * Math.sin(t * speed + phase); o.rotation.y += tilt * Math.sin(t * speed * 0.7 + phase); });
  return o;
}
/** Exit: fly away + fade from t1. */
export function leave(o, t1, [dx, dy, dz = 0] = [0, 0, 3], { dur = 0.35 } = {}) {
  anim(t => { if (t < t1) return; const e = ease((t - t1) / dur); o.position.x += dx * e; o.position.y += dy * e; o.position.z += dz * e; o.visible &&= e < 1; });
  return o;
}

// camera: keys [t, [x, y, z], [lx, ly, lz]]; z is relative to the default distance
export function cameraKeys(keys) {
  anim(t => {
    let p = keys[0][1], l = keys[0][2];
    for (const [t0, kp, kl] of keys.slice(1)) {
      if (t < t0) break;
      const e = smooth((t - t0) / 0.7);
      p = p.map((v, i) => v + (kp[i] - v) * e); l = l.map((v, i) => v + (kl[i] - v) * e);
    }
    camera.position.set(p[0] + 0.08 * Math.sin(t * 0.6), p[1] + 0.06 * Math.sin(t * 0.8), DIST + p[2] - 0.04 * t);  // slow push-in + drift
    camera.lookAt(l[0], l[1], l[2]);
  });
}

// ---------- assets ----------
const loader = new THREE.TextureLoader(), pending = [];
function tex(url) {
  const t = loader.load(url); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  pending.push(new Promise(r => { const i = setInterval(() => t.image && t.image.complete && (clearInterval(i), r()), 20); }));
  return t;
}
const font = new FontFace("Brand", "url(/assets/fonts/Brand.ttf)", { weight: "200 800" });
pending.push(font.load().then(f => document.fonts.add(f)));
const texts = [];
export const ready = () => Promise.all(pending).then(() => texts.forEach(g => g.set(g.userData.s)));  // redraw once Manrope is loaded

function roundRect(w, h, r) {
  const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r); s.lineTo(x + w, y + h - r);
  s.quadraticCurveTo(x + w, y + h, x + w - r, y + h); s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r);
  s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y); return s;
}

/** Text plane drawn on a canvas. spans: string or [[text, color], ...] on one line; "\n" splits lines. Returns a Group with .set(text). */
export function text(spans, { size = 0.6, color = C.ink, weight = 800, align = "center", x = 0, y = 0, z = 0, maxW = 8.4 } = {}) {
  const g = new THREE.Group(), cv = document.createElement("canvas"), ctx = cv.getContext("2d");
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ transparent: true, depthWrite: false }));
  g.add(mesh);
  const px = size * U * 2;  // canvas font px (2x supersampling)
  g.set = s => {
    g.userData.s = s;
    // lines of [text, color] spans; "\n" inside any span starts a new line
    const parts = [[]];
    for (const [q, col] of typeof s === "string" ? [[s, color]] : s)
      q.split("\n").forEach((piece, i) => { if (i) parts.push([]); if (piece) parts.at(-1).push([piece, col]); });
    ctx.font = `${weight} ${px}px Brand`;
    const lw = p => p.reduce((a, [q]) => a + ctx.measureText(q).width, 0);
    let w = Math.max(1, ...parts.map(lw));
    const k = Math.min(1, maxW * U * 2 / w); w *= k;
    cv.width = Math.ceil(w + px * 0.2); cv.height = Math.ceil(px * 1.18 * parts.length * k + px * 0.2);
    ctx.font = `${weight} ${px * k}px Brand`; ctx.textBaseline = "middle";
    parts.forEach((p, i) => {
      let cx = align === "center" ? (cv.width - lw(p)) / 2 : px * 0.1;
      for (const [q, col] of p) { ctx.fillStyle = col; ctx.fillText(q, cx, px * 0.1 + px * 1.18 * k * (i + 0.5)); cx += ctx.measureText(q).width; }
    });
    mesh.material.map?.dispose();  // canvas size changed: a fresh texture avoids stretched glyphs
    const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
    mesh.material.map = t; mesh.material.needsUpdate = true;
    mesh.scale.set(cv.width / U / 2, cv.height / U / 2, 1);
    mesh.position.x = align === "center" ? 0 : cv.width / U / 4;
    g.userData.w = cv.width / U / 2;
  };
  let last; g.update = s => s !== last && g.set(last = s);
  g.update(spans); texts.push(g);
  return track(g, x, y, z);
}

/** Transparent illustration cutout that casts a soft shadow on the backdrop. h in units. */
export function image(url, { h = 6, x = 0, y = 0, z = 0.2, shadow = true } = {}) {
  const t = tex(url), g = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ map: t, transparent: true, alphaTest: 0.4, roughness: 1 });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
  m.castShadow = shadow;
  m.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: t, alphaTest: 0.4 });
  g.add(m);
  const fit = () => m.scale.set(h * t.image.width / t.image.height, h, 1);
  pending.at(-1).then(fit);
  return track(g, x, y, z);
}

/** Extruded rounded card (real thickness, casts shadows). */
export function card({ w = 3, h = 2, r = 0.3, color = "#ffffff", depth = 0.12, x = 0, y = 0, z = 0 } = {}) {
  const g = new THREE.Group();
  const geo = new THREE.ExtrudeGeometry(roundRect(w, h, r), { depth, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.03, bevelSegments: 3, curveSegments: 10 });
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, roughness: 0.55 }));
  m.castShadow = true; m.receiveShadow = true; g.add(m);
  g.userData.front = depth + 0.04;
  return track(g, x, y, z);
}

/** Put a child (text/image/logo) on a card's front face at local (x, y). */
export function onCard(cardG, child, x = 0, y = 0) {
  const i = items.indexOf(child); if (i >= 0) items.splice(i, 1); scene.remove(child);
  child.position.set(x, y, cardG.userData.front); cardG.add(child);
  child.traverse(o => o.isMesh && (o.castShadow = false));
  return child;
}

/** Logo plane (PNG from assets/logos). */
export function logo(name, { size = 1, x = 0, y = 0, z = 0 } = {}) {
  return image(`/assets/logos/${name}.png`, { h: size, x, y, z, shadow: false });
}

/** Flat rounded chip with text, for labels and brand badges. */
export function chip(label, { bg = C.ink, fg = "#ffffff", size = 0.36, x = 0, y = 0, z = 0 } = {}) {
  const tx = text(label, { size, color: fg });
  const c = card({ w: tx.userData.w + size * 1.4, h: size * 1.9, r: size * 0.9, color: bg, depth: 0.05, x, y, z });
  return onCard(c, tx), c;
}

/** Gold crown made of an extruded zig-zag. */
export function crown({ s = 0.4, color = C.gold, x = 0, y = 0, z = 0 } = {}) {
  const sh = new THREE.Shape([[-1, -0.6], [-1, 0.4], [-0.5, -0.05], [0, 0.7], [0.5, -0.05], [1, 0.4], [1, -0.6]].map(([a, b]) => new THREE.Vector2(a * s, b * s)));
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.1, bevelEnabled: true, bevelSize: 0.02, bevelThickness: 0.02 }), new THREE.MeshStandardMaterial({ color, metalness: 0.4, roughness: 0.35 }));
  m.castShadow = true; const g = new THREE.Group(); g.add(m); return track(g, x, y, z);
}

/** Extruded five-point star. */
export function star({ s = 0.3, color = C.gold, x = 0, y = 0, z = 0 } = {}) {
  const pts = [...Array(10)].map((_, i) => { const a = Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? s * 0.45 : s; return new THREE.Vector2(r * Math.cos(a), r * Math.sin(a)); });
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(new THREE.Shape(pts), { depth: 0.08, bevelEnabled: true, bevelSize: 0.02, bevelThickness: 0.02 }), new THREE.MeshStandardMaterial({ color, metalness: 0.3, roughness: 0.4 }));
  m.castShadow = true; const g = new THREE.Group(); g.add(m); return track(g, x, y, z);
}

/** 3D bar anchored at its bottom (x, y). Animate with grow(). */
export function bar({ w = 1.2, h = 3, d = 0.8, color = C.acc, x = 0, y = 0, z = 0 } = {}) {
  const geo = new THREE.BoxGeometry(w, h, d); geo.translate(0, h / 2, 0);
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, roughness: 0.5 }));
  m.castShadow = true; const g = new THREE.Group(); g.add(m); return track(g, x, y, z);
}
/** Grow along y from 0 to full height. */
export function grow(o, t0, { dur = 0.8 } = {}) {
  anim(t => { o.visible &&= t >= t0; o.scale.y *= Math.max(ease((t - t0) / dur), 1e-3); });
  return o;
}

/** SupaIntent lockup: logo + "Supa" (brand blue) + "Intent" (brand ink), Manrope. */
export function lockup({ size = 0.7, x = 0, y = 0, z = 0 } = {}) {
  const g = new THREE.Group(), tx = text([["Supa", C.brand], ["Intent", C.brandInk]], { size, weight: 800 });
  const lg = logo("supaintent-logo-512", { size: size * 1.5 });
  for (const o of [tx, lg]) { scene.remove(o); items.splice(items.indexOf(o), 1); g.add(o); }
  const w = tx.userData.w + size * 1.8;
  lg.position.x = -w / 2 + size * 0.75; tx.position.x = -w / 2 + size * 1.8 + tx.userData.w / 2;
  g.userData.w = w;
  return track(g, x, y, z);
}

/** Ending: lockup card + line + url, from t0 to the end. */
export function endcard(t0, line) {
  const c = pop(card({ w: 8, h: 5.2, r: 0.5, y: 0.8, z: 1 }), t0, { dur: 0.45 });
  const l = lockup({ size: 0.75 }); onCard(c, l, 0, 1.2);
  onCard(c, text(line, { size: 0.36, weight: 700, maxW: 7.2 }), 0, -0.2);
  onCard(c, text("supaintent.com", { size: 0.4, weight: 800, color: C.brand }), 0, -1.3);
  float(c, { amp: 0.05, tilt: 0.05 });
  anim(t => { if (t >= t0 + 0.2) for (const o of items) if (o !== c) o.visible = false; });  // registered last: clears the stage behind the card
}

// ---------- render loop hook ----------
window.seek = t => {
  for (const o of items) { const b = o.userData.base; o.position.copy(b.p); o.rotation.copy(b.r); o.scale.copy(b.s); o.visible = true; }
  for (const f of animators) f(t);
  renderer.render(scene, camera);
};
