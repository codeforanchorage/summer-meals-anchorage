// Dev-only asset generator (NOT part of the runtime build).
//
// Generates the PNG/ICO icons and the 1200x630 social-share card from the
// committed SVG source, so the page can ship a trustworthy link preview.
//
// Run:  npm i puppeteer png-to-ico   (in this folder or globally)
//       node tools/make-assets.mjs
//
// Outputs into ../docs: apple-touch-icon.png, icon-512.png, og-image.png,
// favicon.ico. The source of truth for the mark is docs/favicon.svg.
//
// It is fine that this depends on puppeteer/png-to-ico: accessibility/build
// tooling is dev-only. generate.py itself stays standard-library only.

import { readFileSync, writeFileSync, rmSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import puppeteer from 'puppeteer';
import pngToIco from 'png-to-ico';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DOCS = resolve(__dirname, '..', 'docs');
const svg = readFileSync(resolve(DOCS, 'favicon.svg'), 'utf8');
const svgDataUri = 'data:image/svg+xml;base64,' + Buffer.from(svg).toString('base64');

const browser = await puppeteer.launch({ args: ['--no-sandbox'] });

async function rasterize(size, outfile) {
  const page = await browser.newPage();
  await page.setViewport({ width: size, height: size, deviceScaleFactor: 1 });
  await page.setContent(
    `<!doctype html><html><body style="margin:0;width:${size}px;height:${size}px">
     <img src="${svgDataUri}" width="${size}" height="${size}"></body></html>`,
    { waitUntil: 'networkidle0' });
  const buf = await page.screenshot({ omitBackground: true,
    clip: { x: 0, y: 0, width: size, height: size } });
  writeFileSync(resolve(DOCS, outfile), buf);
  await page.close();
  return buf;
}

// Apple touch icon (180) + a 512 for the web manifest.
await rasterize(180, 'apple-touch-icon.png');
await rasterize(512, 'icon-512.png');

// favicon.ico from 16 + 32 + 48 PNGs.
const icoSizes = [16, 32, 48];
const icoBufs = [];
for (const s of icoSizes) icoBufs.push(await rasterize(s, `_fav-${s}.png`));
writeFileSync(resolve(DOCS, 'favicon.ico'), await pngToIco(icoBufs));
for (const s of icoSizes) rmSync(resolve(DOCS, `_fav-${s}.png`));  // intermediates

// Social-share card (1200x630).
const og = `<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0;box-sizing:border-box}
  body{width:1200px;height:630px;display:flex;
    font-family:"Segoe UI",system-ui,-apple-system,Roboto,Helvetica,Arial,sans-serif;
    background:linear-gradient(135deg,#0b6b7a 0%,#06464f 100%);color:#fff}
  .card{padding:78px 80px;display:flex;flex-direction:column;justify-content:center;gap:26px}
  .row{display:flex;align-items:center;gap:30px}
  .mark{width:128px;height:128px;flex:0 0 auto}
  h1{font-family:Georgia,"Times New Roman",serif;font-size:78px;line-height:1.04;letter-spacing:-.5px}
  p.sub{font-size:38px;line-height:1.3;color:#eaf6f8;max-width:980px}
  .pill{align-self:flex-start;background:#15803d;color:#fff;font-size:30px;font-weight:700;
    padding:12px 26px;border-radius:999px}
  .foot{font-size:27px;color:#bfe3e9;margin-top:6px}
</style></head><body><div class="card">
  <div class="row">
    <img class="mark" src="${svgDataUri}">
    <h1>Free Summer Meals<br>in Anchorage</h1>
  </div>
  <p class="sub">Free breakfast, lunch &amp; snacks for anyone 18 and under. No sign-up, no ID, no cost.</p>
  <span class="pill">Open today + the full week</span>
  <div class="foot">summermeals.codeforanchorage.org &middot; Data: USDA Food &amp; Nutrition Service</div>
</div></body></html>`;

const ogPage = await browser.newPage();
await ogPage.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });
await ogPage.setContent(og, { waitUntil: 'networkidle0' });
writeFileSync(resolve(DOCS, 'og-image.png'),
  await ogPage.screenshot({ clip: { x: 0, y: 0, width: 1200, height: 630 } }));
await ogPage.close();

await browser.close();
console.log('Wrote apple-touch-icon.png, icon-512.png, favicon.ico, og-image.png');
