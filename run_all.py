#!/usr/bin/env python3
"""run_all.py — adaptateur MURUS SANGUINIS.

Le pattern run_all.py de LACRIMAE-FULL (s'arrête à la première porte en échec)
est porté par murus.py à l'échelle des 16 sous-frégates. Ce fichier reste le
point d'entrée historique attendu par les CLIs pillées :

  python run_all.py --pack ARCHIVUM/campaign/campaign_directive.json [--profile vod|direct]

Il délègue intégralement à murus.py — aucune logique dupliquée.
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    args = [sys.executable, str(ROOT / "murus.py")] + sys.argv[1:]
    if "--profile" not in sys.argv:
        args += ["--profile", "vod"]
    sys.exit(subprocess.run(args).returncode)
