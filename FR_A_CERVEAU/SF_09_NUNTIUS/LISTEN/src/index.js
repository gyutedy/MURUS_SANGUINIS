/**
 * MURUS NUNTIUS — Cloudflare Worker (webhook Telegram)
 *
 * Relais uniquement : verifie le secret Telegram, applique la liste blanche des
 * chats, repond un accuse, puis declenche le workflow GitHub `murus_telegram.yml`.
 * Zero calcul metier ici : le projet n'est pas pilote par un Worker, il est pilote
 * par des actes d'operateur enregistres dans le depot.
 *
 * Miroir de FR_A_CERVEAU/SF_09_NUNTIUS/LISTEN/parse.py — les tests Python font foi.
 *
 * Secrets wrangler (jamais dans git) :
 *   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS (liste separee par des virgules),
 *   TELEGRAM_WEBHOOK_SECRET, GITHUB_DISPATCH_TOKEN
 * Vars wrangler.toml : GH_OWNER, GH_REPO, GH_WORKFLOW, GH_REF
 */

const NOMS = new Set(["etat", "clips", "rapport", "parcours", "verdict", "lancer",
  "campagne", "directive", "rendu", "vive", "publier", "stop", "aide"]);
const AIDE =
  "MURUS — commandes\n" +
  "/etat — ce qui tourne, ce qui a echoue\n" +
  "/clips — les livrables LUTH_A0x_final.mp4\n" +
  "/rapport A01 — synchro mesuree, qa_pass, durees\n" +
  "/rendu — lance les 9 clips\n" +
  "/stop <run> — arrete un run\n" +
  "/publier — donne la phrase de validation complete\n" +
  "/aide — ce message";

// Un acte irreversible exige une phrase tapee en entier, pas un mot recopie.
const PHRASE_PUBLICATION = /^VALIDER\s+PUBLICATION\s+[A-Z0-9_]+\s+[A-Z]\d{2}$/;

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("murus-nuntius", { status: 200 });
    }
    const secret = env.TELEGRAM_WEBHOOK_SECRET;
    if (secret) {
      const got = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
      if (got !== secret) return new Response("forbidden", { status: 403 });
    }
    let update;
    try {
      update = await request.json();
    } catch {
      return json({ ok: false, action: "ignore", reason: "bad_json" });
    }
    const d = analyser(update, env.TELEGRAM_CHAT_IDS || env.TELEGRAM_CHAT_ID);
    if (d.action === "ignore") return json(d);
    if (d.action === "repondre") {
      await dire(env, d.chat_id, d.texte);
      return json({ ok: true, ...d });
    }
    await dire(env, d.chat_id, "Recu " + d.commande + " — execution en cours.");
    const r = await declencher(env, d);
    if (!r.ok) await dire(env, d.chat_id, "Declenchement GitHub echoue : " + r.error);
    return json({ ok: r.ok, ...d, dispatched: r.ok });
  },
};

export function analyser(update, autorises) {
  const msg = (update && (update.message || update.edited_message)) || {};
  const chat = msg.chat || {};
  const chatId = String(chat.id || "");
  if (!chatId) return { action: "ignore", raison: "sans_chat" };

  const liste = String(autorises || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  if (!liste.includes(chatId)) {
    // aucune reponse : on ne confirme pas l'existence du bot a un inconnu
    return { action: "ignore", raison: "chat_etranger", chat_id: chatId };
  }

  const texte = String(msg.text || msg.caption || "");
  const photo = fileIdPhoto(msg);
  if (!texte.trim()) {
    if (photo) {
      return {
        action: "repondre", chat_id: chatId, raison: "photo_sans_commande",
        texte: "Photo recue sans commande. Envoie-la avec la legende /capture.",
      };
    }
    return { action: "ignore", raison: "vide", chat_id: chatId };
  }

  const { nom, arguments: args } = decouper(texte);
  if (!nom) {
    return { action: "repondre", chat_id: chatId, raison: "pas_une_commande",
             texte: "Commande inconnue. /aide pour la liste." };
  }
  if (!NOMS.has(nom)) {
    return { action: "repondre", chat_id: chatId, raison: "inconnue",
             texte: "Commande inconnue : /" + nom + ". /aide pour la liste." };
  }
  if (nom === "aide") {
    return { action: "repondre", chat_id: chatId, raison: "aide", texte: AIDE };
  }
  if ((nom === "rapport" || nom === "verdict" || nom === "lancer") && !args) {
    return { action: "repondre", chat_id: chatId, raison: "argument_manquant",
             texte: "Il manque l'argument : /rapport A01 par exemple." };
  }
  if (nom === "publier" && !PHRASE_PUBLICATION.test(args.trim())) {
    return {
      action: "repondre", chat_id: chatId, raison: "phrase_absente",
      texte: "Publication non declenchee. Ecris la phrase complete, tapee a la main :\n" +
             "VALIDER PUBLICATION PREME A01",
    };
  }
  return {
    action: "dispatch",
    chat_id: chatId,
    commande: "/" + nom,
    arguments: args,
    update_id: update.update_id,
    message_id: msg.message_id,
  };
}

function decouper(texte) {
  // Les lignes suivantes sont conservees : /directive recoit un BLOC.
  const brut = String(texte || "").trim();
  if (!brut.startsWith("/")) return { nom: null, arguments: "" };
  const lignes = brut.split("\n");
  const morceaux = lignes[0].split(/\s+/);
  let nom = morceaux[0].slice(1);
  if (nom.includes("@")) nom = nom.split("@")[0];
  const reste = lignes.slice(1).join("\n").trim();
  const args = morceaux.slice(1).join(" ").trim();
  return { nom: nom.toLowerCase(), arguments: (args + (reste ? "\n" + reste : "")).trim() };
}


function fileIdPhoto(msg) {
  const photos = msg.photo || [];
  if (photos.length) {
    let best = photos[0];
    for (const p of photos) {
      if ((p.file_size || 0) >= (best.file_size || 0)) best = p;
    }
    if (best && best.file_id) return best.file_id;
  }
  const doc = msg.document || {};
  const mime = String(doc.mime_type || "").toLowerCase();
  const nom = String(doc.file_name || "").toLowerCase();
  if (doc.file_id && (mime.indexOf("image/") === 0 || /\.(png|jpe?g|webp)$/.test(nom))) {
    return doc.file_id;
  }
  return null;
}

function json(o) {
  return new Response(JSON.stringify(o), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

async function dire(env, chatId, texte) {
  const token = env.TELEGRAM_BOT_TOKEN;
  if (!token || !chatId || !texte) return;
  await fetch("https://api.telegram.org/bot" + token + "/sendMessage", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: String(texte).slice(0, 3800),
      disable_web_page_preview: true,
    }),
  }).catch(() => {});
}

async function declencher(env, d) {
  const token = env.GITHUB_DISPATCH_TOKEN;
  const owner = env.GH_OWNER;
  const repo = env.GH_REPO;
  const workflow = env.GH_WORKFLOW || "murus_telegram.yml";
  const ref = env.GH_REF || "v2";
  if (!token || !owner || !repo) {
    return { ok: false, error: "GITHUB_DISPATCH_TOKEN / GH_OWNER / GH_REPO absents" };
  }
  const url = "https://api.github.com/repos/" + owner + "/" + repo +
    "/actions/workflows/" + workflow + "/dispatches";
  const res = await fetch(url, {
    method: "POST",
    headers: {
      authorization: "Bearer " + token,
      accept: "application/vnd.github+json",
      "content-type": "application/json",
      "user-agent": "murus-nuntius-worker",
      "x-github-api-version": "2022-11-28",
    },
    body: JSON.stringify({
      ref,
      inputs: {
        cmd: d.commande,
        arguments: d.arguments || "",
        update_id: String(d.update_id || ""),
        chat_id: String(d.chat_id || ""),
      },
    }),
  });
  if (res.status === 204) return { ok: true };
  const t = await res.text();
  return { ok: false, error: "HTTP " + res.status + " " + t.slice(0, 200) };
}
