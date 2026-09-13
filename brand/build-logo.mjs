// Generates every file in brand/ from two shapes (the chat bubble + play mark) and the wordmark set in
// Bricolage Grotesque 800, converted to paths so nothing depends on an installed font.
// Needs: bricolage-800.ttf (instantiated from the Google Fonts variable font with fontTools),
//        `npm i opentype.js`, and sharp (borrowed from ../kleo-mcp/node_modules) for the PNG exports.
//   node build-logo.mjs   → writes dist/, copy it here.
import opentype from "opentype.js";
import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire("/home/madiva/kleo/kleo-mcp/package.json");
const sharp = require("sharp");

const AMBER = "#F3B53F", INK = "#1A1200", BG = "#0F1216", PAPER = "#ECEAE4", LIGHTBG = "#FFFFFF";
const font = opentype.loadSync("bricolage-800.ttf");

// ---------- MARK: chat bubble (squircle, sharp bottom-left) + rounded play ----------
// bubble in a 100x100 box at origin, rx 26, bottom-left corner sharp (the "tail")
function bubblePath(x, y, s, r) {
  const X = v => x + v * s / 100, Y = v => y + v * s / 100, R = r * s / 100;
  return [
    `M${X(0) + R},${Y(0)}`,
    `H${X(100) - R}`, `A${R},${R} 0 0 1 ${X(100)},${Y(0) + R}`,
    `V${Y(100) - R}`, `A${R},${R} 0 0 1 ${X(100) - R},${Y(100)}`,
    `H${X(0)}`,                       // sharp bottom-left corner = the tail
    `V${Y(0) + R}`, `A${R},${R} 0 0 1 ${X(0) + R},${Y(0)}`, `Z`,
  ].join(" ");
}
// rounded play triangle centred (optically) in the same box
function playPath(x, y, s, k = 1) {
  const S = v => v * s / 100;
  // geometry before rounding: triangle 34 wide, 44 tall; stroke adds ~4 each side
  const cx = 53, cy = 50;                       // optical centre nudged right
  const w = 30 * k, h = 40 * k;
  const p = [[cx - w / 2 + 1, cy - h / 2], [cx + w / 2 + 1, cy], [cx - w / 2 + 1, cy + h / 2]];
  return { d: `M${p.map(q => `${x + S(q[0])},${y + S(q[1])}`).join("L")}Z`, sw: S(9 * k) };
}
function mark(x, y, s, { bubble = AMBER, play = INK, playScale = 1 } = {}) {
  const pl = playPath(x, y, s, playScale);
  return `<path d="${bubblePath(x, y, s, 27)}" fill="${bubble}"/>` +
    `<path d="${pl.d}" fill="${play}" stroke="${play}" stroke-width="${pl.sw}" stroke-linejoin="round"/>`;
}

// ---------- WORDMARK ----------
function wordmark(x, baseline, size, color, tracking = -0.018) {
  // manual layout so we can add tracking on top of the font's kerning
  const glyphs = font.stringToGlyphs("Kleo");
  let cx = x, d = "";
  for (let i = 0; i < glyphs.length; i++) {
    const g = glyphs[i];
    d += g.getPath(cx, baseline, size).toPathData(2) + " ";
    let adv = g.advanceWidth * size / font.unitsPerEm;
    if (i < glyphs.length - 1) adv += font.getKerningValue(g, glyphs[i + 1]) * size / font.unitsPerEm + tracking * size;
    cx += adv;
  }
  const capH = font.charToGlyph("K").getBoundingBox().y2 * size / font.unitsPerEm;
  return { svg: `<path d="${d.trim()}" fill="${color}"/>`, width: cx - x, capH };
}

const svg = (w, h, body, bg) =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}">` +
  (bg ? `<rect width="${w}" height="${h}" fill="${bg}"/>` : "") + body + `</svg>`;

// ---------- FILES ----------
const out = "dist"; fs.mkdirSync(out, { recursive: true });
const files = {};

// 1. mark alone (transparent), and app icon (amber bubble on dark tile with margin)
files["kleo-mark.svg"] = svg(120, 120, mark(10, 10, 100));
files["kleo-icon-dark.svg"] = svg(512, 512, `<rect width="512" height="512" rx="112" fill="${BG}"/>` + mark(96, 96, 320));
files["kleo-icon-amber.svg"] = svg(512, 512, `<rect width="512" height="512" rx="112" fill="${AMBER}"/>` + mark(96, 96, 320, { bubble: INK, play: AMBER }));
files["kleo-favicon.svg"] = svg(32, 32, mark(1, 1, 30, { playScale: 1.35 }));

// 2. horizontal lockup: mark + wordmark
function lockup(color, bg, transparent = false) {
  const size = 200;                 // font size
  const wm0 = wordmark(0, 0, size, color);
  const M = wm0.capH * 1.18;        // mark a bit taller than the cap height
  const gap = M * 0.34, pad = 60;
  const W = pad + M + gap + wm0.width + pad, H = M + pad * 2;
  const baseline = pad + M - (M - wm0.capH) / 2 + 0.5;   // wordmark vertically centred on the mark
  const wm = wordmark(pad + M + gap, baseline, size, color);
  return svg(Math.round(W), Math.round(H), mark(pad, pad, M) + wm.svg, transparent ? null : bg);
}
files["kleo-logo-dark.svg"] = lockup(PAPER, BG);
files["kleo-logo-light.svg"] = lockup(BG, LIGHTBG);
files["kleo-logo-on-dark-transparent.svg"] = lockup(PAPER, null, true);
files["kleo-logo-on-light-transparent.svg"] = lockup(BG, null, true);

// 3. stacked lockup (mark above wordmark) for social / og
function stacked(color, bg) {
  const W = 1200, H = 630, size = 150;
  const wm0 = wordmark(0, 0, size, color);
  const M = 210, gap = 52;
  const total = M + gap + wm0.capH;
  const top = (H - total) / 2;
  const wm = wordmark((W - wm0.width) / 2, top + M + gap + wm0.capH, size, color);
  return svg(W, H, mark((W - M) / 2, top, M) + wm.svg, bg);
}
files["kleo-social-1200x630.svg"] = stacked(PAPER, BG);

for (const [name, s] of Object.entries(files)) fs.writeFileSync(`${out}/${name}`, s);

// PNG exports
const png = async (name, w, h) => {
  await sharp(Buffer.from(files[name]), { density: 300 }).resize(w, h).png().toFile(`${out}/${name.replace(".svg", "")}-${w}.png`);
};
await png("kleo-mark.svg", 1024, 1024);
await png("kleo-icon-dark.svg", 1024, 1024);
await png("kleo-icon-amber.svg", 1024, 1024);
await png("kleo-icon-dark.svg", 512, 512);
await png("kleo-icon-dark.svg", 192, 192);
await png("kleo-favicon.svg", 64, 64);
await png("kleo-favicon.svg", 32, 32);
for (const n of ["kleo-logo-dark.svg", "kleo-logo-light.svg", "kleo-logo-on-dark-transparent.svg", "kleo-logo-on-light-transparent.svg"]) {
  const m = files[n].match(/width="(\d+)" height="(\d+)"/);
  await png(n, 2400, Math.round(2400 * m[2] / m[1]));
}
await png("kleo-social-1200x630.svg", 2400, 1260);
console.log(fs.readdirSync(out).join("\n"));
