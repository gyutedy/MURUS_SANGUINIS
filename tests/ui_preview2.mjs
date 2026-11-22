// Porte UI de la PREVIEW 2 : on ouvre le site construit dans un vrai Chromium et on
// refuse si l'un des QUATRE panneaux, le lecteur, la frame ou les sous-titres manquent.
// Un « c'est corrige » sans cette preuve ne vaut rien.
import puppeteer from 'puppeteer'
import { writeFileSync } from 'node:fs'

const URL = process.env.P2_URL || 'http://127.0.0.1:8098/'
const fails = []
const browser = await puppeteer.launch({ args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] })
try {
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 950 })
  const errors = []
  page.on('pageerror', (e) => errors.push(String(e.message || e)))
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 })

  try {
    await page.waitForFunction(
      () => document.querySelectorAll('input[type="range"]').length >= 9,
      { timeout: 30000 },
    )
  } catch (e) {
    const diag = await page.evaluate(() => ({
      rootHtml: (document.getElementById('root')?.innerHTML || '').slice(0, 700),
      text: (document.body?.innerText || '').slice(0, 400),
      ranges: document.querySelectorAll('input[type="range"]').length,
    }))
    writeFileSync('preview-2.json', JSON.stringify({ fatal: 'interface non rendue', errors, diag }, null, 2))
    await page.screenshot({ path: 'preview-2.png', fullPage: false })
    console.log('::error::interface non rendue (aucun curseur apres 30s)')
    console.log('erreurs JS :', JSON.stringify(errors.slice(0, 3)))
    console.log('root :', diag.rootHtml)
    console.log('texte :', diag.text)
    await browser.close()
    process.exit(1)
  }

  const audit = await page.evaluate(() => {
    const legends = [...document.querySelectorAll('legend')].map((l) => l.textContent.trim())
    const videos = [...document.querySelectorAll('video')].filter((v) => v.readyState >= 2).map((v) => v.duration || 0)
    const imgs = [...document.querySelectorAll('img')].filter((i) => i.naturalWidth > 0).map((i) => i.getAttribute('src'))
    const stageEl = document.querySelector('main');
    const rect = stageEl ? stageEl.getBoundingClientRect() : null
    const aside = document.querySelector('aside')
    return {
      legends,
      videos,
      imgs,
      ranges: document.querySelectorAll('input[type="range"]').length,
      colors: document.querySelectorAll('input[type="color"]').length,
      selects: document.querySelectorAll('select').length,
      mainTop: rect ? Math.round(rect.top) : null,
      asideScroll: aside ? aside.scrollHeight > aside.clientHeight : false,
      bodyScroll: document.body.scrollHeight > window.innerHeight + 4,
      captionText: (document.body.innerText || '').slice(0, 4000),
    }
  })

  const want = ['GLOW VIDÉO', 'SOUS-TITRES', 'LUT', 'FADE']
  for (const w of want) {
    if (!audit.legends.some((l) => l.toUpperCase().includes(w))) fails.push(`panneau manquant : ${w}`)
  }
  if (audit.ranges < 9) fails.push(`trop peu de curseurs (${audit.ranges}) : la review doit se regler au curseur`)
  if (audit.colors < 3) fails.push(`trop peu de selecteurs de couleur (${audit.colors})`)
  if (audit.selects < 5) fails.push(`trop peu de listes deroulantes (${audit.selects})`)
  if (audit.videos.length === 0) fails.push('aucune video de clip jouee (lecteur vide)')
  if (!audit.imgs.some((s) => s && s.includes('frame_'))) fails.push('aucune frame de reference affichee')
  if (audit.asideScroll !== true) fails.push('la colonne de reglages ne defile pas')
  if (audit.bodyScroll === true) fails.push('la page defile : les panneaux doivent defiler, pas la page')
  if (errors.length) fails.push(`erreur JS dans la page : ${errors[0]}`)

  await page.screenshot({ path: 'preview-2.png', fullPage: false })
  writeFileSync('preview-2.json', JSON.stringify({ url: URL, audit, fails }, null, 2))

  console.log(JSON.stringify({
    panneaux: audit.legends,
    curseurs: audit.ranges,
    couleurs: audit.colors,
    listes: audit.selects,
    videos_jouees: audit.videos.length,
    frames_affichees: audit.imgs.filter((s) => s && s.includes('frame_')),
    colonne_qui_defile: audit.asideScroll,
  }, null, 2))

  if (fails.length) {
    for (const f of fails) console.log(`::error::${f}`)
    console.log('[ECHEC] preview 2 :', fails.length, 'defaut(s)')
    process.exitCode = 1
  } else {
    console.log('[OK] preview 2 verifiee dans Chromium (4 panneaux, lecteur, frame, sous-titres)')
  }
} finally {
  await browser.close()
}
