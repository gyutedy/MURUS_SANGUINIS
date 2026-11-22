import { useEffect, useMemo, useRef, useState } from 'react'
import Panels from './Panels.jsx'
import { buildCodexPostprod } from './codex.js'

// Approximation navigateur (option A) : CSS pour le regard, ffmpeg pour la verite.
// Le job exact_frame publie le PNG REELLEMENT rendu avec la meme chaine.
const LUT_CSS = {
  cinematic_hyper_detail: 'contrast(1.12) saturate(1.12)',
  hdr_imperator: 'contrast(1.10) saturate(1.10) brightness(1.02)',
  realistic_aurea: 'contrast(1.06) saturate(1.04)',
  old_main_noctis: 'contrast(1.10) saturate(1.02)',
  balanced: 'contrast(1.08) saturate(1.06)',
}

export const DEFAULT_STATE = {
  glow: { enabled: true, mode: 'scene', sigma: 14, opacity: 0.35, preset: 'doux' },
  caption: {
    font: 'Montserrat ExtraBold',
    size: 62,
    x_pct: 50,
    y_pct: 82,
    color: '#FFFFFF',
    outline_width: 3,
    outline_color: '#000000',
    glow_intensity: 1.4,
    glow_color: '#FFD700',
    motion: 'pop-in',
    motion_speed: 1,
  },
  lut: { enabled: true, profile: 'hdr_imperator' },
  fade: { mode: 'black', duration_sec: 0.8 },
}

const btn = {
  background: '#1b1b26', color: '#e9e9f2', border: '1px solid #2e2e3a',
  borderRadius: 6, padding: '6px 10px', cursor: 'pointer', fontSize: 13,
}

function Caption({ caption, text }) {
  const glow = caption.glow_intensity
  const shadows = [
    `0 0 ${4 + glow * 6}px ${caption.glow_color}`,
    `0 0 ${8 + glow * 14}px ${caption.glow_color}`,
    `0 0 ${14 + glow * 22}px ${caption.glow_color}`,
  ].join(', ')
  return (
    <div style={{
      position: 'absolute', left: `${caption.x_pct}%`, top: `${caption.y_pct}%`,
      transform: 'translate(-50%, -50%)', width: '92%', textAlign: 'center',
      fontFamily: `'${caption.font}', Montserrat, Arial Black, sans-serif`,
      fontSize: `${caption.size / 3}px`, lineHeight: 1.15,
      color: caption.color, textShadow: shadows, pointerEvents: 'none',
      WebkitTextStroke: `${caption.outline_width / 3}px ${caption.outline_color}`,
      fontWeight: 900, letterSpacing: 0.5,
    }}>{text}</div>
  )
}

function Screen({ src, frameSrc, isVideo, state, text, mediaRef }) {
  const g = state.glow
  const lutCss = state.lut.enabled ? (LUT_CSS[state.lut.profile] || '') : ''
  const mediaStyle = { width: '100%', height: '100%', objectFit: 'contain', display: 'block' }
  const blurLayer = {
    ...mediaStyle, position: 'absolute', inset: 0,
    filter: `blur(${Math.max(1, g.sigma / 2.2)}px)`,
    opacity: g.enabled ? g.opacity : 0,
    mixBlendMode: 'screen',
    maskImage: 'linear-gradient(to bottom, #000 0 78%, transparent 78%)',
    WebkitMaskImage: 'linear-gradient(to bottom, #000 0 78%, transparent 78%)',
  }
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', background: '#000', overflow: 'hidden', filter: lutCss }}>
      {isVideo ? (
        <>
          <video ref={mediaRef} src={src} style={mediaStyle} muted loop autoPlay playsInline />
          {g.enabled ? (
            <video src={src} style={blurLayer} muted loop autoPlay playsInline aria-hidden="true" />
          ) : null}
        </>
      ) : (
        <>
          <img src={frameSrc} alt="" style={mediaStyle} />
          {g.enabled ? <img src={frameSrc} alt="" style={blurLayer} /> : null}
        </>
      )}
      <Caption caption={state.caption} text={text || ''} />
    </div>
  )
}

export default function App() {
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState('')
  const [entryIndex, setEntryIndex] = useState(0)
  const [state, setState] = useState(DEFAULT_STATE)
  const [signed, setSigned] = useState(false)
  const [showExact, setShowExact] = useState(false)
  const [codexOut, setCodexOut] = useState('')
  const mediaRef = useRef(null)

  useEffect(() => {
    fetch('./manifest.json', { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`manifest ${r.status}`))))
      .then(setMeta)
      .catch((e) => setError(String(e.message || e)))
  }, [])

  const clips = meta?.clips || []
  const clip = clips[entryIndex] || null

  const codex = useMemo(
    () => (meta ? buildCodexPostprod(state, { pack_token: meta.pack_token, clip_id: clip?.id }) : null),
    [state, meta, clip],
  )

  function exportCodex() {
    const json = JSON.stringify(codex, null, 2)
    setCodexOut(json)
    const blob = new Blob([json], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'codex_postprod.json'
    a.click()
    URL.revokeObjectURL(a.href)
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <h2>PREVIEW 2 — manifeste absent</h2>
        <p style={{ color: '#ff8080' }}>{error}</p>
        <p style={{ color: '#9a9aa8' }}>
          Le manifeste est écrit par le workflow <code>murus_preview_2.yml</code> (étape assemble).
        </p>
      </div>
    )
  }
  if (!meta) return <div style={{ padding: 24 }}>chargement du pack…</div>

  return (
    <>
      <style>{`
        aside::-webkit-scrollbar { width: 12px; }
        aside::-webkit-scrollbar-track { background: #0b0b0f; }
        aside::-webkit-scrollbar-thumb { background: #2e2e3a; border-radius: 6px; }
      `}</style>
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 400px', height: '100vh', overflow: 'hidden' }}>
        <main style={{ padding: 16, display: 'flex', flexDirection: 'column', alignItems: 'stretch', justifyContent: 'flex-start', gap: 12, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <strong style={{ fontSize: 13, letterSpacing: 1 }}>PREVIEW 2 — POSTPROD</strong>
            <span style={{ fontSize: 12, color: '#8a8a99' }}>pack {meta.pack_token}</span>
            <span style={{ marginLeft: 'auto' }} />
            <button style={btn} onClick={() => setEntryIndex((i) => (i - 1 + clips.length) % clips.length)}>◀</button>
            <span style={{ fontSize: 12 }}>clip {entryIndex + 1}/{clips.length} — {clip?.id}</span>
            <button style={btn} onClick={() => setEntryIndex((i) => (i + 1) % clips.length)}>▶</button>
            <button style={btn} onClick={() => setShowExact((v) => !v)}>
              {showExact ? 'masquer la frame exacte' : 'frame exacte (ffmpeg)'}
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: showExact ? 'minmax(0,1fr) minmax(0,1fr)' : 'minmax(0,1fr)', gap: 12, minHeight: 0 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 }}>
              <span style={{ fontSize: 11, color: '#8a8a99', textTransform: 'uppercase', letterSpacing: 1 }}>lecteur — vidéo entière (aperçu)</span>
              <div style={{ height: 420, border: '1px solid #232330', borderRadius: 8, overflow: 'hidden' }}>
                {clip ? <Screen src={clip.file} frameSrc={clip.frame} isVideo state={state} text={clip.text} mediaRef={mediaRef} /> : null}
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 }}>
              <span style={{ fontSize: 11, color: '#8a8a99', textTransform: 'uppercase', letterSpacing: 1 }}>
                {showExact ? 'frame — rendu exact (ffmpeg)' : 'frame — aperçu'}
              </span>
              <div style={{ height: 420, border: '1px solid #232330', borderRadius: 8, overflow: 'hidden' }}>
                {showExact && clip?.exact_frame ? (
                  <img src={clip.exact_frame} alt="" style={{ width: '100%', height: '100%', objectFit: 'contain', background: '#000' }} />
                ) : clip ? (
                  <Screen src={clip.file} frameSrc={clip.frame} isVideo={false} state={state} text={clip.text} />
                ) : null}
              </div>
              {showExact && !clip?.exact_frame ? (
                <span style={{ fontSize: 11, color: '#c9a227' }}>
                  pas encore de frame exacte : lance le job <code>exact_frame</code> avec le codex
                </span>
              ) : null}
            </div>
          </div>

          <div style={{ fontSize: 11, color: '#6f6f80' }}>
            ordre gravé PP2 : <b>glow → caption → lut → fade</b> · zone des sous-titres jamais floutée (GL2)
          </div>
        </main>

        <aside style={{ padding: 16, borderLeft: '1px solid #222', overflowY: 'scroll', overflowX: 'hidden', height: '100vh', scrollbarGutter: 'stable' }}>
          <Panels state={state} setState={setState} signed={signed} setSigned={setSigned} meta={meta} onExport={exportCodex} codex={codex} codexOut={codexOut} />
        </aside>
      </div>
    </>
  )
}
