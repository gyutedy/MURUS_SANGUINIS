"""Obtient le jeton de rafraichissement OAuth d'une chaine YouTube.

Pourquoi cet outil existe : le `refresh_token` ne se fabrique pas a la main. Il faut
une autorisation dans un navigateur. Cet outil ouvre l'URL, ecoute le retour sur
localhost, echange le code, puis affiche le jeton — sur TON ecran, jamais dans un
fichier du depot, jamais dans un log de CI.

Usage (une fois par chaine) :

    python jetons_youtube.py --client-id XXX.apps.googleusercontent.com --client-secret YYY
    python jetons_youtube.py ... --port 8765     # si le port 8080 est pris

Prerequis dans Google Cloud (compte de la chaine) :
  - YouTube Data API v3 activee ;
  - Ecran de consentement OAuth configure, avec ton compte en « Utilisateurs test » ;
  - Identifiant OAuth de type « Application de bureau » -> client_id + client_secret.

Portees demandees : youtube.upload (deposer une video) et youtube.readonly (lire la
chaine pour ne pas publier deux fois le meme clip).
"""
import argparse
import http.server
import json
import socketserver
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
PORTEES = ("https://www.googleapis.com/auth/youtube.upload "
           "https://www.googleapis.com/auth/youtube.readonly")

_code = {}


class Retour(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (API http.server)
        q = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(q)
        _code["code"] = (params.get("code") or [None])[0]
        _code["erreur"] = (params.get("error") or [None])[0]
        corps = ("<h2>Autorisation recue.</h2><p>Tu peux fermer cet onglet.</p>"
                 if _code.get("code") else
                 "<h2>Refus ou erreur : %s</h2>" % (_code.get("erreur") or "inconnue"))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(corps.encode("utf-8"))

    def log_message(self, *a):  # silence : rien ne doit fuir dans une console partagee
        return


def main(argv=None):
    ap = argparse.ArgumentParser(description="jeton de rafraichissement YouTube")
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret", required=True)
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--chainon", default="YouTube", help="nom lisible, pour l'affichage")
    args = ap.parse_args(argv)

    redirection = "http://localhost:%d/" % args.port
    url = AUTH + "?" + urllib.parse.urlencode({
        "client_id": args.client_id,
        "redirect_uri": redirection,
        "response_type": "code",
        "scope": PORTEES,
        "access_type": "offline",
        "prompt": "consent",          # sinon Google ne redonne pas de refresh_token
        "include_granted_scopes": "true",
    })
    print("\n%s — ouvre cette adresse dans le navigateur du compte de la chaine :\n" % args.chainon)
    print(url + "\n")
    print("En attente du retour sur %s (Ctrl+C pour abandonner)..." % redirection)

    with socketserver.TCPServer(("127.0.0.1", args.port), Retour) as srv:
        srv.timeout = 300
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001 - pas de navigateur : l'URL est deja affichee
            pass
        while not _code:
            t.join(1.0)
        srv.shutdown()

    if not _code.get("code"):
        print("Aucune autorisation : %s" % (_code.get("erreur") or "timeout"))
        return 2

    donnees = urllib.parse.urlencode({
        "code": _code["code"],
        "client_id": args.client_id,
        "client_secret": args.client_secret,
        "redirect_uri": redirection,
        "grant_type": "authorization_code",
    }).encode()
    try:
        with urllib.request.urlopen(TOKEN, data=donnees, timeout=60) as r:
            rep = json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001
        print("Echange du code refuse : %s" % e)
        return 1

    refresh = rep.get("refresh_token")
    if not refresh:
        print("Pas de refresh_token dans la reponse (%s). Reessaie avec prompt=consent."
              % ", ".join(rep.keys()))
        return 1
    print("\nrefresh_token obtenu. A poser comme secret GitHub (nom seulement ici) :\n")
    print("  " + refresh)
    print("\nNe le copie pas dans un fichier du depot. Pose-le par le script de secrets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
