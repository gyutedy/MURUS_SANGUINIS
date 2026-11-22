/**
 * tests/ui_preview1.mjs — la preview 1 est-elle REALLY utilisable ?
 *
 * Ce n'est pas un test d'intention : on lance Chromium sur le site CONSTRUIT,
 * on lit le DOM et on refuse si un panneau manque, si le PNG du watermark n'est
 * pas chargé, ou si la vidéo du clip ne joue pas.
 *
 * Pourquoi ce fichier existe : deux sessions de suite, « c'est corrigé » était
 * faux (curseurs absents, titres absents, écran noir). Une capture et un audit
 * DOM valent mieux qu'une déclaration.
 *
 * Usage (dans une CI) :
 *   npm i puppeteer@23
 *   npx http-server site -p 8099 -s &
 *   node tests/ui_preview1.mjs http://127.0.0.1:8099/ review-preview1.png
 */
import puppeteer from 'puppeteer';

const url = process.argv[2] || 'http://127.0.0.1:8099/';
const shot = process.argv[3] || 'review-preview1.png';

const browser = await puppeteer.launch({
  args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1500, height: 950 });
await page.goto(url, { waitUntil: 'networkidle2', timeout: 90000 });
await new Promise((r) => setTimeout(r, 6000));

const audit = await page.evaluate(() => {
  const labels = [...document.querySelectorAll('label, legend')].map((l) => (l.textContent || '').trim());
  const imgs = [...document.images].map((i) => ({
    src: i.currentSrc || i.src,
    w: i.naturalWidth,
    h: i.naturalHeight,
  }));
  // Le <video> interne est mis a l'echelle par Remotion : sa position ne dit rien de
  // la mise en page. On mesure le CONTENEUR de scene (celui qui porte le double-clic).
  const stageEl = document.querySelector('[title^="Double-cliquez"]');
  const stage = stageEl ? stageEl.getBoundingClientRect() : null;
  const aside = document.querySelector('aside');
  return {
    labels,
    imgs,
    stageTop: stage ? Math.round(stage.top) : null,
    stageHeight: stage ? Math.round(stage.height) : null,
    asideScroll: aside ? aside.scrollHeight > aside.clientHeight : false,
    ranges: document.querySelectorAll('input[type="range"]').length,
    colors: document.querySelectorAll('input[type="color"]').length,
    videos: [...document.querySelectorAll('video')].map((v) => ({
      src: v.currentSrc || v.src,
      w: v.videoWidth,
      h: v.videoHeight,
    })),
  };
});

const has = (frag) => audit.labels.some((l) => l.toLowerCase().includes(frag.toLowerCase()));
const tail = (src) => String(src || '').split('/').pop();
const checks = {
  'couleur du titre': has('couleur du titre'),
  'police du titre': has('police du titre'),
  'position horizontale': has('position horizontale'),
  'position verticale': has('position verticale'),
  'curseur taille du titre': audit.labels.some((l) => /^taille \d+px$/.test(l)),
  'titre du pack present': audit.labels.some((l) => l.startsWith('place ')),
  'input couleur': audit.colors,
  'curseurs': audit.ranges,
  'lecteur colle en haut (px depuis le haut)': audit.stageTop,
  'colonne qui defile': audit.asideScroll,
  'images chargees': audit.imgs.filter((i) => i.w > 0).map((i) => tail(i.src)),
  'videos': audit.videos.filter((v) => v.w > 0).map((v) => `${tail(v.src)} ${v.w}x${v.h}`),
};
console.log(JSON.stringify(checks, null, 2));

// Le watermark n'est plus pose d'office : l'operateur le pose. On ne l'exige donc
// pas, on verifie que le PNG de campagne est joignable (sinon il ne pourra pas le poser).
const wmOk = await page.evaluate(async () => {
  try {
    const r = await fetch('./watermarks/preme.png', { method: 'HEAD' });
    return r.ok;
  } catch {
    return false;
  }
});
if (!wmOk) fails.push('le PNG de campagne watermarks/preme.png est injoignable');

let shotOk = true;
try {
  await page.screenshot({ path: shot, fullPage: true });
} catch (e) {
  shotOk = false;
  console.log('capture impossible :', e.message);
}
await browser.close();

const fails = [];
if (!checks['couleur du titre']) fails.push('panneau titre : couleur absente');
if (!checks['police du titre']) fails.push('panneau titre : police absente');
if (!checks['curseur taille du titre']) fails.push('panneau titre : taille absente');
if (!checks['titre du pack present']) fails.push('aucun titre du pack dans le panneau');
if (!checks['position horizontale']) fails.push('watermark : curseur horizontale absent');
if (!checks['position verticale']) fails.push('watermark : curseur verticale absent');

if (checks['videos'].length === 0) fails.push('aucune video de clip chargee');
if (audit.stageTop === null) fails.push('aucune video trouvee pour mesurer la position');
else if (audit.stageTop > 140) fails.push(`le lecteur n'est pas en haut : ${audit.stageTop}px du haut`);
if (audit.asideScroll !== true) fails.push('la colonne de reglages ne defile pas');

if (fails.length) {
  console.log('::error::' + fails.join(' | '));
  process.exit(1);
}
console.log('[OK] interface verifiee dans Chromium (panneaux, PNG de campagne, video)' + (shotOk ? '' : ' — capture manquante'));
