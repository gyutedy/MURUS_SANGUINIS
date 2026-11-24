"""Verifie la synchro entre une transcription et l'audio reel d'une fenetre.

Methode (mesure, pas supposition) :
  1. on telecharge la fenetre source (yt-dlp) et on en extrait l'audio mono 16 kHz ;
  2. on calcule une enveloppe d'energie sur des tranches de 20 ms ;
  3. on prend les mots de la transcription qui tombent dans la fenetre ;
  4. on cherche le decalage (entre -2 s et +2 s) qui maximise l'energie sous les
     debuts de mots : si ce decalage est nul, la transcription est a l'heure ;
  5. on mesure aussi la derive : le meme score calcule separement sur la premiere
     et la derniere moitie du clip. Un decalage qui grandit = compression du temps.

Sortie : un rapport JSON + un code de sortie qui refuse au-dela du seuil.
  0 = a l'heure (|decalage| <= seuil et pas de derive)
  1 = decale (le rapport dit de combien et dans quel sens)
  2 = mesure impossible (audio absent, transcription vide)
"""
import argparse
import array
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

SEUIL_DEFAUT = 0.25          # secondes : au-dela, un clip ne doit pas sortir
TRANCHE = 0.02               # 20 ms


def die(code, message):
    print("SYNCHRO : %s" % message, file=sys.stderr)
    sys.exit(code)


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def fenetre_audio(vod, debut, fin, travail):
    """Telecharge la section et rend un WAV mono 16 kHz de la fenetre."""
    if shutil.which("yt-dlp") is None:
        die(2, "yt-dlp absent")
    if shutil.which("ffmpeg") is None:
        die(2, "ffmpeg absent")
    src = travail / "src.%(ext)s"
    run(["yt-dlp", "--no-playlist", "-f", "ba/b",
         "--download-sections", "*%.3f-%.3f" % (debut, fin + 1.0),
         "--force-keyframes-at-cuts", "-o", str(src), vod])
    fichiers = sorted(p for p in travail.glob("src.*") if p.suffix not in (".part", ".ytdl"))
    if not fichiers:
        die(2, "aucune source telechargee")
    wav = travail / "fenetre.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(fichiers[0]),
         "-ac", "1", "-ar", "16000", "-vn", str(wav)])
    return wav


def enveloppe_ech(ech):
    """Enveloppe RMS par tranche de 20 ms, a partir d'echantillons f32 mono 16 kHz."""
    pas = int(16000 * TRANCHE)
    env = []
    for i in range(0, len(ech) - pas, pas):
        somme = 0.0
        for v in ech[i:i + pas]:
            somme += v * v
        env.append(math.sqrt(somme / pas))
    return env


def enveloppe(wav):
    brut = run(["ffmpeg", "-v", "error", "-i", str(wav), "-f", "f32le", "-ac", "1",
                "-ar", "16000", "-"]).stdout
    ech = array.array("f")
    ech.frombytes(brut[: len(brut) - (len(brut) % 4)])
    return enveloppe_ech(ech)


def mots_de(transcript, debut, fin):
    d = json.loads(Path(transcript).read_text(encoding="utf-8"))
    t = d.get("transcript", d)
    mots = []
    for sg in t.get("segments", []):
        for w in sg.get("words", []) or []:
            s = float(w.get("start", sg.get("start", 0)))
            if debut <= s <= fin:
                texte = str(w.get("word") or w.get("text") or "").strip()
                if texte:
                    mots.append((s - debut, texte))
    return mots


def impulsion(n, debuts, sigma=2.0):
    """Train d'impulsions gaussiennes aux debuts de mots (sigma en tranches)."""
    sig = [0.0] * n
    for t in debuts:
        c = t / TRANCHE
        for i in range(max(0, int(c - 3 * sigma)), min(n, int(c + 3 * sigma) + 1)):
            sig[i] += math.exp(-0.5 * ((i - c) / sigma) ** 2)
    return sig


def onsets(env, lissage=2):
    """Pente positive de l'enveloppe : la parole commence ou l'energie monte.

    On ne correle pas les niveaux (une syllabe longue attire le maximum) mais les
    attaques : c'est ce qui rend l'alignement precis a la tranche de 20 ms.
    """
    lisse = []
    for i in range(len(env)):
        a = max(0, i - lissage)
        b = min(len(env), i + lissage + 1)
        lisse.append(sum(env[a:b]) / (b - a))
    return [max(0.0, lisse[i] - lisse[i - 1]) if i else 0.0 for i in range(len(lisse))]


def correlation(env, sig, decalage_tranches):
    """Correlation entre l'energie audio et le train d'impulsions, pour un decalage."""
    n = len(env)
    total, poids = 0.0, 0.0
    for i in range(n):
        j = i - decalage_tranches
        if 0 <= j < n:
            total += env[i] * sig[j]
            poids += sig[j]
    return total / poids if poids else 0.0


def meilleur_decalage(env, debuts, plage_max=2.0):
    """Decalage qui aligne le mieux la parole reelle et les debuts de mots."""
    env = onsets(env)
    sig = impulsion(len(env), [max(0.0, min(t, len(env) * TRANCHE)) for t in debuts])
    pas = 0.02
    meilleur, arg = -1.0, 0.0
    k = -plage_max
    while k <= plage_max + 1e-9:
        s = correlation(env, sig, int(round(k / pas))) - 1e-6 * abs(k)
        if s > meilleur:
            meilleur, arg = s, k
        k += pas
    return round(arg, 3), meilleur


def main(argv=None):
    ap = argparse.ArgumentParser(description="verifie la synchro transcription/audio")
    ap.add_argument("--vod", required=True)
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--report", default=None)
    ap.add_argument("--seuil", type=float, default=SEUIL_DEFAUT)
    ap.add_argument("--travail", default=None)
    ap.add_argument("--autotest", action="store_true",
                    help="verifie l'outil sur un audio synthetique connu (aucun reseau)")
    args = ap.parse_args(argv)

    if args.autotest:
        return autotest()

    travail = Path(args.travail or "/tmp/synchro")
    travail.mkdir(parents=True, exist_ok=True)

    wav = fenetre_audio(args.vod, args.start, args.end, travail)
    env = enveloppe(wav)
    duree = len(env) * TRANCHE
    mots = mots_de(args.transcript, args.start, args.end)
    if not mots:
        die(2, "aucun mot dans la fenetre %.1f-%.1f : rien a mesurer" % (args.start, args.end))

    debuts = [t for t, _ in mots]
    decalage, energie = meilleur_decalage(env, debuts)
    milieu = duree / 2.0
    decalage_debut, _ = meilleur_decalage(env, [t for t in debuts if t <= milieu])
    decalage_fin, _ = meilleur_decalage(env, [t for t in debuts if t > milieu])
    derive = round(decalage_fin - decalage_debut, 3)
    base = correlation(onsets(env), impulsion(len(env), debuts), 0)
    gain = round(energie / base, 2) if base > 0 else None

    rapport = {
        "schema": "murus.synchro.v1",
        "fenetre": {"debut": args.start, "fin": args.end},
        "audio": {"duree_mesuree_s": round(duree, 2), "tranche_s": TRANCHE},
        "mots": len(mots),
        "decalage_optimal_s": decalage,
        "derive_debut_fin_s": derive,
        "energie_debut_de_mot": round(energie, 6),
        "gain_vs_decalage_nul": gain,
        "seuil_s": args.seuil,
        "verdict": ("a_l_heure" if abs(decalage) <= args.seuil and abs(derive) <= args.seuil
                    else "decale"),
        "lecture": (
            "decalage negatif = les mots sont en avance sur la parole (sous-titres "
            "qui filent) ; positif = en retard ; derive = l'ecart entre la premiere "
            "et la seconde moitie du clip"),
    }
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(rapport, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    print(json.dumps(rapport, ensure_ascii=False))
    return 0 if rapport["verdict"] == "a_l_heure" else 1


def autotest():
    """Trois cas connus : a l'heure, en avance de 0,8 s, en retard de 0,4 s."""
    import tempfile
    import wave

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        chemin = f.name
    with wave.open(chemin, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        n = 16000 * 6
        ech = array.array("h", [0] * n)
        for t, dur in ((0.43, 0.25), (1.71, 0.40), (2.34, 0.18), (3.90, 0.55), (5.12, 0.22)):
            i0, i1 = int(t * 16000), int((t + dur) * 16000)
            for i in range(i0, i1):
                ech[i] = int(12000 * math.sin(2 * math.pi * 440 * i / 16000))
        w.writeframes(ech.tobytes())
    with wave.open(chemin, "rb") as w:
        pcm = array.array("h")
        pcm.frombytes(w.readframes(w.getnframes()))
    f32 = array.array("f", [v / 32768.0 for v in pcm])
    env = enveloppe_ech(f32)
    Path(chemin).unlink(missing_ok=True)
    base = [0.43, 1.71, 2.34, 3.90, 5.12]
    cas = (("pile", base, 0.0),
           ("avance", [t + 0.8 for t in base], -0.8),
           ("retard", [t - 0.4 for t in base], 0.4))
    echecs = []
    for nom, mots, attendu in cas:
        mesure, _ = meilleur_decalage(env, mots)
        ok = abs(mesure - attendu) <= 0.05
        print("AUTOTEST %-7s : mesure %+.2f s, attendu %+.2f s -> %s"
              % (nom, mesure, attendu, "ok" if ok else "ECHEC"))
        if not ok:
            echecs.append(nom)
    return 0 if not echecs else 1


if __name__ == "__main__":
    sys.exit(main())
