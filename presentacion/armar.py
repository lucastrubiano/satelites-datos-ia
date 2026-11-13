"""Arma presentacion/index.html: la charla en un solo HTML, sin servidor ni dependencias.

Correr: uv run python presentacion/armar.py
Fuente: slides/*.html (un <section> por slide), deck.css y deck.json (orden). Las imágenes van en img/.
"""
import json
import re
from pathlib import Path

AQUI = Path(__file__).parent
# Id de cada imagen en el deck publicado → archivo local
IMAGENES = {
    "28496c13debd3a3e74c3ca5aaf6adf4d": "01_escena_falso_color.png",
    "81c1d15ec1c450167d66f67e844a07ad": "03_calidad.png",
    "580802803b68af9813e9a4ec68661616": "04_cultivos.png",
    "df62dc73c9dde3f7b46da4af418fff7b": "05_ndvi_limpio.png",
    "6040027fcba8e3d5e40c37e9fa24708c": "06_anomalia.png",
    "ab416b51cda1970460c537151ff3f04e": "error_por_campania.png",
    "4e66da2b2db4b06b12b559bd669e06cd": "ciclo_soja.png",
    "91e4871c60019c8cad746c0edd1d2d7b": "tres_paneles_y_mapa.png",
    "df0442baa384066c296f5a4e62bb4671": "campania_vs_normal.png",
    "337d6f83a3ae94a6b9d6b1d290d46085": "cadena_verdor_toneladas.png",
    "b4f38bc978b9243424d901090e5f6b8d": "cadena_toneladas_precio.png",
    "0528bc53e593bb092aae4577c1967ddc": "cadena_ar_br_precio.png",
    "b75d809d361571e5646d46e5852a7000": "avatar.png",
    "7d067f211679f396ba2ddc415ce19eea": "qr_linkedin.png",
    "ee31b761f88588d0847732164a3b762a": "qr_web.png",
    "95f39c151453e113f193ca18bf1bfc43": "qr_repo.png",
    "d3484a864dd1c4f0866a29afb9259a23": "qr_instagram.png",
    "0f2d371c51ae16759f23b30c8bf52a1d": "qr_youtube.png",
    "c3258cd8558d8ec01aaf42639298b439": "qr_whatsapp.png",
}
BASE = """
* { margin: 0; box-sizing: border-box; }
html, body { height: 100%; background: #0e0d0c; overflow: hidden; }
#escena { position: absolute; left: 50%; top: 50%; width: 1920px; height: 1080px; transform-origin: 0 0; }
section { position: absolute; inset: 0; width: 1920px; height: 1080px; overflow: hidden; visibility: hidden; }
section.activa { visibility: visible; }
aside { display: none; }
ul, ol { padding-left: 1.2em; }
img, svg { display: block; }
img[src*='qr_'] { image-rendering: pixelated; }
#num { position: fixed; right: 16px; bottom: 12px; font: 14px 'Geist Mono', monospace; color: #6b655d; }
@page { size: 1920px 1080px; margin: 0; }
@media print {
  html, body { height: auto; overflow: visible; background: none; }
  #escena { position: static; transform: none !important; width: auto; height: auto; }
  section { position: relative; visibility: visible; break-after: page; }
  .car { animation: none; }
  #num { display: none; }
}
"""
JS = """
const ss = [...document.querySelectorAll('section')], esc = document.getElementById('escena'), num = document.getElementById('num');
let i = Math.min(ss.length, Math.max(1, parseInt(location.hash.slice(1)) || 1)) - 1;
function ir(n) { i = Math.max(0, Math.min(ss.length - 1, n)); ss.forEach((s, k) => s.classList.toggle('activa', k === i)); num.textContent = (i + 1) + ' / ' + ss.length; history.replaceState(null, '', '#' + (i + 1)); }
function escalar() { const k = Math.min(innerWidth / 1920, innerHeight / 1080); esc.style.transform = 'scale(' + k + ') translate(-50%, -50%)'; }
addEventListener('resize', escalar);
addEventListener('keydown', e => { if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(e.key)) ir(i + 1); else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(e.key)) ir(i - 1); else if (e.key === 'Home') ir(0); else if (e.key === 'End') ir(ss.length - 1); else if (e.key === 'f') document.documentElement.requestFullscreen(); });
addEventListener('click', e => { if (!e.target.closest('a')) ir(i + (e.clientX < innerWidth / 3 ? -1 : 1)); });
escalar(); ir(i);
"""

deck = json.loads((AQUI / "deck.json").read_text())
slides = "\n".join((AQUI / "slides" / f"{s}.html").read_text() for s in deck["order"])
slides = re.sub(r"/_blob/([0-9a-f]{32})", lambda m: "img/" + IMAGENES[m[1]], slides)
slides = slides.replace('<a href="', '<a target="_blank" rel="noopener" href="')
fuentes = "".join(f'<link rel="stylesheet" href="{f["href"]}">' for f in deck["faces"].values())
(AQUI / "index.html").write_text(
    f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    f'<title>{deck["title"]}</title>\n{fuentes}\n<style>{BASE}\n{(AQUI / "deck.css").read_text()}</style>\n</head>\n<body>\n'
    f'<div id="escena">\n{slides}</div>\n<div id="num"></div>\n<script>{JS}</script>\n</body>\n</html>\n'
)
print(len(deck["order"]), "slides → presentacion/index.html")
