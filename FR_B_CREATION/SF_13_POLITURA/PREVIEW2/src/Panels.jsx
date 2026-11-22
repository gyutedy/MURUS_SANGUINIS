import { GLOW_PRESETS, CAPTION_FONTS, MOTIONS } from './codex.js'

const field = { display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }
const label = { fontSize: 11, color: '#9a9aa8', textTransform: 'uppercase', letterSpacing: 0.8 }
const btn = {
  background: '#1b1b26', color: '#e9e9f2', border: '1px solid #2e2e3a',
  borderRadius: 6, padding: '6px 10px', cursor: 'pointer', fontSize: 13,
}
const fs = { border: '1px solid #232330', borderRadius: 8, padding: 12, marginBottom: 14 }

function Slider({ id, text, min, max, step, value, onChange, suffix }) {
  return (
    <div style={field}>
      <label htmlFor={id} style={label}>{text} — {typeof value === 'number' ? value.toFixed(step < 1 ? 2 : 0) : value}{suffix || ''}</label>
      <input id={id} type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} />
    </div>
  )
}

export default function Panels({ state, setState, signed, setSigned, meta, onExport, codex, codexOut, onReplay }) {
  const patch = (key, partial) => setState((s) => ({ ...s, [key]: { ...s[key], ...partial } }))
  const { glow, caption, lut, fade } = state
  const profiles = meta?.lut_profiles || []

  return (
    <>
      <fieldset style={fs}>
        <legend>GLOW VIDÉO</legend>
        <div style={field}>
          <label style={label}>sorte de glow (préréglages réels)</label>
          <select
            id="glow-kind"
            value={glow.preset}
            onChange={(e) => {
              const p = GLOW_PRESETS.find((x) => x.id === e.target.value)
              if (p) patch('glow', { preset: p.id, mode: p.mode, sigma: p.sigma, opacity: p.opacity })
            }}
          >
            {GLOW_PRESETS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
          </select>
        </div>
        <div style={field}>
          <label htmlFor="glow-mode" style={label}>mode (masque)</label>
          <select id="glow-mode" value={glow.mode} onChange={(e) => patch('glow', { mode: e.target.value, preset: 'custom' })}>
            <option value="scene">scene — toute l'image</option>
            <option value="subject">subject — le sujet seul</option>
          </select>
        </div>
        <Slider id="glow-sigma" text="sigma (largeur du glow)" min={4} max={30} step={0.5} value={glow.sigma} onChange={(v) => patch('glow', { sigma: v, preset: 'custom' })} />
        <Slider id="glow-opacity" text="opacité (force du glow)" min={0} max={0.6} step={0.01} value={glow.opacity} onChange={(v) => patch('glow', { opacity: v, preset: 'custom' })} />
        <label style={{ fontSize: 12 }}>
          <input type="checkbox" checked={glow.enabled} onChange={(e) => patch('glow', { enabled: e.target.checked })} /> glow activé
        </label>
      </fieldset>

      <fieldset style={fs}>
        <legend>SOUS-TITRES</legend>
        <div style={field}>
          <label htmlFor="cap-font" style={label}>police</label>
          <select id="cap-font" value={caption.font} onChange={(e) => patch('caption', { font: e.target.value })}>
            {CAPTION_FONTS.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>
        <Slider id="cap-size" text="taille du texte" min={12} max={240} step={1} value={caption.size} onChange={(v) => patch('caption', { size: v })} suffix=" px" />
        <Slider id="cap-x" text="position horizontale" min={0} max={100} step={1} value={caption.x_pct} onChange={(v) => patch('caption', { x_pct: v })} suffix=" %" />
        <Slider id="cap-y" text="position verticale" min={0} max={100} step={1} value={caption.y_pct} onChange={(v) => patch('caption', { y_pct: v })} suffix=" %" />
        <div style={field}>
          <label htmlFor="cap-color" style={label}>couleur du texte</label>
          <input id="cap-color" type="color" value={caption.color} onChange={(e) => patch('caption', { color: e.target.value })} />
        </div>
        <Slider id="cap-outline" text="contour (épaisseur)" min={0} max={24} step={0.5} value={caption.outline_width} onChange={(v) => patch('caption', { outline_width: v })} suffix=" px" />
        <div style={field}>
          <label htmlFor="cap-outline-color" style={label}>couleur du contour</label>
          <input id="cap-outline-color" type="color" value={caption.outline_color} onChange={(e) => patch('caption', { outline_color: e.target.value })} />
        </div>
        <hr style={{ border: 0, borderTop: '1px solid #232330', margin: '10px 0' }} />
        <Slider id="cap-glow" text="glow des sous-titres (intensité)" min={0} max={5} step={0.1} value={caption.glow_intensity} onChange={(v) => patch('caption', { glow_intensity: v })} />
        <div style={field}>
          <label htmlFor="cap-glow-color" style={label}>couleur du glow des sous-titres</label>
          <input id="cap-glow-color" type="color" value={caption.glow_color} onChange={(e) => patch('caption', { glow_color: e.target.value })} />
        </div>
        <div style={field}>
          <label htmlFor="cap-motion" style={label}>motion d'apparition</label>
          <select id="cap-motion" value={caption.motion} onChange={(e) => patch('caption', { motion: e.target.value })}>
            {MOTIONS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <Slider id="cap-motion-speed" text="vitesse de la motion" min={0.25} max={3} step={0.05} value={caption.motion_speed} onChange={(v) => patch('caption', { motion_speed: v })} />
        <button id="cap-replay" style={btn} onClick={() => onReplay && onReplay()}>rejouer la motion</button>
        <p style={{ fontSize: 10, color: '#6f6f80', marginTop: 6 }}>
          l'animation se joue a chaque changement de texte ou de motion ; ce bouton la rejoue.
        </p>
      </fieldset>

      <fieldset style={fs}>
        <legend>LUT</legend>
        <div style={field}>
          <label htmlFor="lut-profile" style={label}>profil (atom_ic_profiles.json)</label>
          <select id="lut-profile" value={lut.profile} onChange={(e) => patch('lut', { profile: e.target.value })}>
            {(profiles.length ? profiles : [lut.profile]).map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <label style={{ fontSize: 12 }}>
          <input type="checkbox" checked={lut.enabled} onChange={(e) => patch('lut', { enabled: e.target.checked })} /> lut activée
        </label>
      </fieldset>

      <fieldset style={fs}>
        <legend>FADE</legend>
        <div style={field}>
          <label htmlFor="fade-mode" style={label}>mode</label>
          <select id="fade-mode" value={fade.mode} onChange={(e) => patch('fade', { mode: e.target.value })}>
            <option value="black">black — vers le noir</option>
            <option value="darken">darken — assombrit</option>
          </select>
        </div>
        <Slider id="fade-sec" text="durée du fade" min={0.1} max={10} step={0.1} value={fade.duration_sec} onChange={(v) => patch('fade', { duration_sec: v })} suffix=" s" />
      </fieldset>

      <fieldset style={fs}>
        <legend>SIGNATURE</legend>
        <label style={{ fontSize: 12, display: 'block', marginBottom: 10 }}>
          <input type="checkbox" checked={signed} onChange={(e) => setSigned(e.target.checked)} /> je signe ce codex (validated_by_magos)
        </label>
        <button style={btn} onClick={onExport}>Exporter codex_postprod.json</button>
        {codexOut ? (
          <>
            <p style={{ fontSize: 11, color: '#7fdc9a', marginTop: 10 }}>
              codex écrit ({codexOut.length} o). Commite-le dans <code>REVIEW/codex_postprod.json</code> :
            </p>
            <pre style={{ fontSize: 10, maxHeight: 220, overflow: 'auto', background: '#0d0d14', padding: 8, borderRadius: 6 }}>{codexOut}</pre>
          </>
        ) : (
          <p style={{ fontSize: 11, color: '#6f6f80', marginTop: 10 }}>
            sans signature, <code>validated_by_magos</code> reste false et le rendu est refusé (PP1).
          </p>
        )}
      </fieldset>
    </>
  )
}
