# Changelog

## 2026-11-22
- **Cloud AI (optional, off by default):** use Groq, OpenRouter, Gemini, OpenAI or LM Studio for moment scoring, titles and hooks on a slow PC. Only clip text is sent; the key stays in `data/llm.json`. Test connection button included.
- **Heading looks:** new default **Impact** (big bold text, one accent word, pop-in, pink underline), plus **Neon glow**, **Banner bar** and the classic box. Boxes now have rounded corners.
- **Sharper hooks and titles:** the local model is asked for scroll-stopping formulas (curiosity gap, hot take, mistake warning, secret, reaction), still grounded in what is really said in the clip; the no-model fallback is punchier.
- **Cover image** for every clip (`Cover image` link, also inside the clips ZIP).
- **System check line** at the top: FFmpeg, encoder, YouTube runtime, AI model, disk, each with a fix when red.
- **Fixes:** macOS caption filter, blocked PyAV (Windows Smart App Control), bad caption times no longer fail a clip, clearer "app closed" message.
- **New:** YouTube browser-login setting for the bot check, optional From/To part import, 480p/360p data-saver qualities, Facecam look sliders, fade in/out, AMD/Intel GPU encoders, opening-heading on/off.

## 2026-11-21
- 1080p default with a 4K option beside Get preview (no more silent 720p), videos over 2 hours are imported by part, in-app updater, donate bar and supporters list, Report a problem, stuck-job watchdog, PyAV 19 fix, portable FFmpeg fallback, Windows installer uses Python 3.10 to 3.13.
