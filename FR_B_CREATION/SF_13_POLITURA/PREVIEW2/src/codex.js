// Construction du codex POSTPROD — la seule sortie signable de la preview 2.
// L'ordre PP2 (glow -> caption -> lut -> fade) est grave : jamais permute ici.

export const GLOW_PRESETS = [
  { id: 'doux',            label: 'Doux (scène, faible)',        mode: 'scene',   sigma: 8,  opacity: 0.25 },
  { id: 'large_bloom',     label: 'Large bloom (scène, large)',  mode: 'scene',   sigma: 26, opacity: 0.5 },
  { id: 'halation_serree', label: 'Halation serrée (bord net)',  mode: 'scene',   sigma: 5,  opacity: 0.45 },
  { id: 'sujet_seul',      label: 'Sujet seul (le visage)',      mode: 'subject', sigma: 14, opacity: 0.4 },
]

export const CAPTION_FONTS = [
  'Montserrat ExtraBold',
  'Arial Black',
  'Impact',
  'Verdana',
  'Georgia',
]

export const MOTIONS = ['pop-in', 'bounce', 'slide']

export function buildCodexPostprod(state, meta) {
  const { glow, caption, lut, fade, signed } = state
  return {
    schema_version: 'sanguinala.postprod.codex.v1',
    pack_token: meta.pack_token || '',
    order: ['glow', 'caption', 'lut', 'fade'],
    caption: {
      schema_version: 'dev11.caption.style.v1',
      id: `preme_${String(meta.clip_id || 'A01')}`,
      font: caption.font,
      position: { x_pct: caption.x_pct, y_pct: caption.y_pct },
      size: caption.size,
      color: caption.color,
      outline: { width: caption.outline_width, color: caption.outline_color },
      glow: { intensity: caption.glow_intensity, color: caption.glow_color },
      motion: caption.motion,
      motion_speed: caption.motion_speed,
      canvas: '9:16',
    },
    glow: { enabled: glow.enabled, mode: glow.mode, sigma: glow.sigma, opacity: glow.opacity },
    // `intensity` est un reglage d'APERCU : le schema du codex ne l'accepte pas
    // (additionalProperties: false) et le rendu applique le profil a 100 %.
    lut: { enabled: lut.enabled, profile: lut.profile },
    fade_out: { mode: fade.mode, duration_sec: fade.duration_sec },
    validated_by_magos: signed === true,
  }
}
