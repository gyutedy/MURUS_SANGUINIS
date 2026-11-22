import { useEffect, useMemo, useRef, useState } from 'react'
import Panels from './Panels.jsx'
import { buildCodexPostprod } from './codex.js'
import ATOM from '../../CODEBASE/lut/profiles/atom_ic_profiles.json'

// Approximation navigateur (option A) : CSS pour le regard, ffmpeg pour la verite.
// Le job exact_frame publie le PNG REELLEMENT rendu avec la meme chaine.
//
// ERREUR PAYEE (ERRATA E-11) : la LUT de l'apercu avait ete tapee a la main depuis le
// bloc `textura` (1.10 / 1.10), alors que le rendu (lut/lut_apply.py) applique le bloc
// `chroma` via eq (contrast/saturation/brightness/gamma). L'apercu montrait donc un
// dixieme de l'effet, dans le mauvais bloc — invisible a l'ecran.
export function lutFilter(profileName, intensity = 1) {
  const prof = (ATOM.profiles || {})[profileName] || {}
  const ch = prof.chroma || prof.textura || {}
  const k = Math.max(0, Math.min(2, Number(intensity) || 0))
  const contrast = 1 + ((Number(ch.contrast) || 1) - 1) * k
  const saturation = 1 + ((Number(ch.saturation) || 1) - 1) * k
  const gamma = 1 + ((Number(ch.gamma) || 1) - 1) * k
  // CSS n'a pas de gamma : on l'approche par la luminance (gamma > 1 = plus clair).
  const brightness = 1 + ((Number(ch.brightness) || 0) * 2 + (gamma - 1) * 0.35) * k
  return `contrast(${contrast.toFixed(3)}) saturate(${saturation.toFixed(3)}) brightness(${brightness.toFixed(3)})`
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
  lut: { enabled: true, profile: 'hdr_imperator', intensity: 1 },
  fade: { mode: 'black', duration_sec: 0.8 },
}

const btn = {
  background: '#1b1b26', color: '#e9e9f2', border: '1px solid #2e2e3a',
  borderRadius: 6, padding: '6px 10px', cursor: 'pointer', fontSize: 13,
}

function Caption({ caption, text, replayKey }) {
  const glow = caption.glow_intensity
  const shadows = [
    `0 0 ${4 + glow * 6}px ${caption.glow_color}`,
    `0 0 ${8 + glow * 14}px ${caption.glow_color}`,
    `0 0 ${14 + glow * 22}px ${caption.glow_color}`,
  ].join(', ')
  const dur = Math.max(0.15, 0.7 / Math.max(0.25, caption.motion_speed))
  return (
    <div
      key={`${replayKey}-${caption.motion}-${caption.motion_speed}`}
      style={{
        position: 'absolute', left: `${caption.x_pct}%`, top: `${caption.y_pct}%`,
        width: '92%', textAlign: 'center',
        fontFamily: `'${caption.font}', Montserrat, Arial Black, sans-serif`,
        fontSize: `${caption.size / 3}px`, lineHeight: 1.15,
        color: caption.color, textShadow: shadows, pointerEvents: 'none',
        WebkitTextStroke: `${caption.outline_width / 3}px ${caption.outline_color}`,
        fontWeight: 900, letterSpacing: 0.5,
        animation: `murus-${caption.motion} ${dur}s ease-out both`,
      }}
    >{text}</div>
  )
}

function Screen({ src, frameSrc, isVideo, state, text, mediaRef, replayKey, captionStart }) {
  const g = state.glow
  const lutCss = state.lut.enabled ? lutFilter(state.lut.profile, state.lut.intensity) : ''
  const mediaStyle = { width: '100%', height: '100%', objectFit: 'contain', display: 'block' }
  // GL2 : la bande des sous-titres (>= 70 %) n'est jamais floutee, avec un fondu
  // progressif pour ne pas couper l'image en deux.
  const glowLayer = {
    position: 'absolute', inset: 0,
    backdropFilter: `blur(${Math.max(1, g.sigma / 2.2)}px)`,
    WebkitBackdropFilter: `blur(${Math.max(1, g.sigma / 2.2)}px)`,
    opacity: g.enabled ? g.opacity : 0,
    mixBlendMode: 'screen',
    maskImage: 'linear-gradient(to bottom, #000 0 70%, transparent 80%)',
    WebkitMaskImage: 'linear-gradient(to bottom, #000 0 70%, transparent 80%)',
    pointerEvents: 'none',
  }

  // Le sous-titre a un SEGMENT : il apparait a `captionStart` et l'animation joue a
  // ce moment-la, a chaque passage (le clip tourne en boucle).
  const [visible, setVisible] = useState(!isVideo)
  const [epoch, setEpoch] = useState(0)
  const wasIn = useRef(false)
  const start = Number(captionStart) || 0

  function onTimeUpdate(e) {
    const t = e.target.currentTime
    const inSeg = t >= start
    if (inSeg !== wasIn.current) {
      wasIn.current = inSeg
      setVisible(inSeg)
      if (inSeg) setEpoch((x) => x + 1)
    }
  }

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', background: '#000', overflow: 'hidden', filter: lutCss }}>
      {isVideo ? (
        <video ref={mediaRef} src={src} style={mediaStyle} muted loop autoPlay playsInline onTimeUpdate={onTimeUpdate} />
      ) : (
        <img src={frameSrc} alt="" style={mediaStyle} />
      )}
      {g.enabled ? <div style={glowLayer} aria-hidden="true" /> : null}
      {visible ? (
        <Caption caption={state.caption} text={text || ''} replayKey={`${epoch}-${replayKey}`} />
      ) : null}
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
  const [replayKey, setReplayKey] = useState(0)
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
        @keyframes murus-pop-in {
          0%   { transform: translate(-50%, -50%) scale(0.55); opacity: 0; }
          65%  { transform: translate(-50%, -50%) scale(1.08); opacity: 1; }
          100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
        }
        @keyframes murus-bounce {
          0%   { transform: translate(-50%, -50%) scale(0.6); opacity: 0; }
          60%  { transform: translate(-50%, -50%) scale(1.14); opacity: 1; }
          100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
        }
        @keyframes murus-slide {
          from { transform: translate(-50%, -20%) translateY(40px); opacity: 0; }
          to   { transform: translate(-50%, -50%); opacity: 1; }
        }
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
                {clip ? <Screen src={clip.file} frameSrc={clip.frame} isVideo state={state} text={clip.text} mediaRef={mediaRef} replayKey={replayKey} captionStart={clip.caption_start} /> : null}
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
                  <Screen src={clip.file} frameSrc={clip.frame} isVideo={false} state={state} text={clip.text} replayKey={replayKey} captionStart={clip.caption_start} />
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
          <Panels state={state} setState={setState} signed={signed} setSigned={setSigned} meta={meta} onExport={exportCodex} codex={codex} codexOut={codexOut} onReplay={() => setReplayKey((k) => k + 1)} />
        </aside>
      </div>
    </>
  )
}
