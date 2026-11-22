// Renders /videos/<id>/scene.js frame by frame in headless Chrome → videos/<id>/out/visual.mp4 (no audio).
// Usage: bun render.ts <id> [t1 t2 ...]   (with times: writes a contact sheet out/peek.jpg instead)
import puppeteer from "puppeteer-core";
import { spawn } from "child_process";

const [id, ...peek] = process.argv.slice(2), FPS = 30, ROOT = import.meta.dir;
const server = Bun.serve({ port: 0, fetch: async req => { const f = Bun.file(ROOT + decodeURIComponent(new URL(req.url).pathname)); return await f.exists() ? new Response(f) : new Response("", { status: 404 }); } });
const browser = await puppeteer.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true, args: ["--use-angle=metal", "--enable-gpu"] });
const page = await browser.newPage();
page.on("pageerror", e => console.error("💥", e.message));
await page.setViewport({ width: 1080, height: 1920 });
await page.goto(`http://localhost:${server.port}/web/index.html?v=${id}`);
await page.waitForFunction("window.isReady === true", { timeout: 60000 });
const length = await page.evaluate("window.LENGTH");
const out = `${ROOT}/videos/${id}/out`;
const shot = async (t: number) => { await page.evaluate(`window.seek(${t})`); return page.screenshot({ type: "jpeg", quality: 92 }); };

if (peek.length) {
  const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-i", "-", "-vf", `scale=270:480,tile=${Math.min(peek.length, 6)}x${Math.ceil(peek.length / 6)}`, "-frames:v", "1", `${out}/peek.jpg`]);
  for (const t of peek) ff.stdin.write(await shot(+t));
  ff.stdin.end(); await new Promise(r => ff.on("close", r)); console.log(`👀 ${out}/peek.jpg`);
} else {
  const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", `${out}/visual.mp4`]);
  const n = Math.round(length * FPS);
  for (let i = 0; i < n; i++) {
    if (!ff.stdin.write(await shot(i / FPS))) await new Promise(r => ff.stdin.once("drain", r));
    if (i % FPS === 0) process.stdout.write(`\r🎬 ${(i / FPS).toFixed(0)}s / ${length}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on("close", r)); console.log(`\n✅ ${out}/visual.mp4`);
}
await browser.close(); server.stop();
