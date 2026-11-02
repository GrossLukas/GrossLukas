"""ASCII-Porträt im Terminalfenster („./portrait.sh“).

Quelle ist das lokale Foto (wird nicht ins Repo gelegt). Der Hintergrund wird per
Personen-Segmentierung (rembg, Modell u2net_human_seg) entfernt, damit nur Kopf und
Schultern als ASCII erscheinen. Ohne Foto bleibt die vorhandene SVG unverändert.

Aufruf: python src/portrait.py [pfad/zum/foto.jpg]
"""
from __future__ import annotations

import os
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from PIL import Image, ImageFilter, ImageOps  # noqa: E402

import brand  # noqa: E402
from textpath import Font, GlyphDefs  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\l.gross\Downloads\Lukas.JPG'
CROP = (245, 620, 1075, 1560)          # Kopf und Hals im Originalfoto (830 x 940)
COLS, ROWS = 96, 57                    # Zellen 4,5 x 8,55 – passt zum Seitenverhältnis des Ausschnitts
RAMP = " .,:;i1tfLCG08@"              # dunkel -> hell
# Helligkeitsstufen -> Türkistöne (dunkle Zeichen gedämpft, helle Zeichen leuchtend)
SHADES = ('#16455a', '#2582a6', '#38bdf8', '#9be2ff', '#ffffff')
W, H, R = 600, 600, 16
TEXT_W, TOP, LINE = 432, 56, 8.55
TEXT_X = (W - TEXT_W) / 2
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
EASE = 'cubic-bezier(.2,.8,.2,1)'
MONO = Font('JetBrainsMono', 500)


def subject(path: str) -> tuple[Image.Image, Image.Image]:
    """Farbausschnitt und Maske der Person (Hintergrund entfernt)."""
    rgb = Image.open(path).convert('RGB')
    cache = os.path.join(brand.ROOT, '.preview', 'portrait-alpha.png')   # .preview ist nicht im Repo
    if os.path.exists(cache) and Image.open(cache).size == rgb.size:
        full = Image.open(cache).convert('L')
    else:
        from rembg import new_session, remove
        full = remove(rgb, session=new_session('u2net_human_seg')).split()[-1]
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        full.save(cache)
    alpha = full.crop(CROP)
    return rgb.crop(CROP), alpha


def ascii_cells(path: str) -> tuple[list[list[tuple[str, int]]], list[str]]:
    color, alpha = subject(path)
    gray = ImageOps.grayscale(color).resize((COLS * 4, ROWS * 4), Image.LANCZOS)
    alpha = alpha.resize((COLS * 4, ROWS * 4), Image.LANCZOS)
    # Helligkeit nur über die Person normieren; Gamma > 1 lässt Brille und Bart dunkel, Haare und Shirt hell
    lum = np.asarray(gray.filter(ImageFilter.UnsharpMask(2, 120, 1)), float) / 255
    inside = lum[np.asarray(alpha) > 128]
    lo, hi = np.percentile(inside, 2), np.percentile(inside, 98)
    tone = ((lum - lo) / (hi - lo)).clip(0, 1) ** 1.5
    g = Image.fromarray((tone * 255).astype('uint8')).resize((COLS, ROWS), Image.BOX)
    a = alpha.resize((COLS, ROWS), Image.BOX)
    rows = []
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            m = a.getpixel((x, y)) / 255
            v = g.getpixel((x, y)) / 255 * m
            if m < .35:
                row.append((' ', 0))
                continue
            ch = RAMP[min(int(v * len(RAMP)), len(RAMP) - 1)]
            row.append((ch, min(int(v * len(SHADES)), len(SHADES) - 1)))
        rows.append(row)
    return rows, list(SHADES)


def row_svg(cells: list[tuple[str, int]]) -> tuple[str, int]:
    """Eine Zeile als tspan-Läufe gleicher Farbe; liefert Markup und Länge ohne Leerzeichen am Ende."""
    while cells and cells[-1][0] == ' ':
        cells = cells[:-1]
    out, run, cur = [], '', None
    for ch, shade in cells:
        s = shade if ch != ' ' else cur
        if s != cur and run:
            out.append(f'<tspan class="s{cur if cur is not None else 0}">{escape(run)}</tspan>')
            run = ''
        cur = s
        run += ch
    if run:
        out.append(f'<tspan class="s{cur if cur is not None else 0}">{escape(run)}</tspan>')
    return ''.join(out), len(cells)


def build(rows: list[list[tuple[str, int]]], palette: list[str]) -> str:
    defs = GlyphDefs('p')
    css = [
        f'.row{{animation:row .5s {EASE} var(--d) both}}@keyframes row{{from{{opacity:0;transform:translateX(-8px)}}}}',
        '.scan{transform-box:view-box;animation:scan 2.4s ease-in .1s both}'
        f'@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({H}px);opacity:0}}}}',
        '.fade{animation:fade .4s ease var(--d) both}@keyframes fade{from{opacity:0}}',
        '.cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}',
        ''.join(f'.s{i}{{fill:{c}}}' for i, c in enumerate(palette)),
    ]
    body = [
        f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{R}" fill="#08131d" '
        f'stroke="{brand.VIOLET_SOFT}" stroke-opacity=".35"/>',
        f'<path d="M1 40h{W - 2}" stroke="#ffffff" stroke-opacity=".08"/>',
        ''.join(f'<circle cx="{22 + k * 18}" cy="20" r="5.5" fill="{c}"/>'
                for k, c in enumerate(('#ff5f57', '#febc2e', '#28c840'))),
        MONO.text('lukas@github: ~$ ./portrait.sh', 13, W / 2, 25, anchor='middle', defs=defs,
                  attrs='fill="#ffffff" fill-opacity=".5"'),
    ]
    text = []
    for i, cells in enumerate(rows):
        markup, n = row_svg(cells)
        if not n:
            continue
        # textLength erzwingt dieselbe Breite mit jeder Systemschrift
        text.append(f'<text class="row" style="--d:{.15 + i * .03:.3f}s" x="{TEXT_X:.1f}" y="{TOP + i * LINE:.1f}" '
                    f'textLength="{TEXT_W * n / COLS:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
                    f'{markup}</text>')
    body.append(f'<g font-family="{FONT}" font-size="8.6" font-weight="700">{"".join(text)}</g>')
    body.append(f'<rect class="scan" x="1" y="-40" width="{W - 2}" height="40" fill="url(#sg)"/>')
    # Eingabezeile unten
    py = H - 22
    t0 = .15 + ROWS * .03 + .2
    prompt = 'lukas@github:~$ cat name.txt'
    body.append(f'<path d="M1 {H - 48}h{W - 2}" stroke="#ffffff" stroke-opacity=".08"/>')
    body.append(MONO.text(prompt, 15, 20, py, defs=defs,
                          attrs=f'class="fade" style="--d:{t0:.2f}s" fill="{brand.VIOLET_SOFT}"'))
    nx = 20 + MONO.measure(prompt + ' ', 15)
    body.append(MONO.text('Lukas Gross', 15, nx, py, defs=defs,
                          attrs=f'class="fade" style="--d:{t0 + .35:.2f}s" fill="#ffffff"'))
    cx = nx + MONO.measure('Lukas Gross ', 15)
    body.append(f'<g class="fade" style="--d:{t0 + .5:.2f}s"><rect class="cur" x="{cx:.1f}" y="{py - 14}" '
                f'width="9" height="18" rx="1.5" fill="{brand.VIOLET_SOFT}"/></g>')
    d = ('<linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5eead4" stop-opacity="0"/>'
         '<stop offset="1" stop-color="#5eead4" stop-opacity=".22"/></linearGradient>')
    return brand.svg_doc(W, H, ''.join(body), title='ASCII-Porträt von Lukas Gross',
                         desc='Terminalfenster mit einem ASCII-Porträt von Lukas Gross, darunter cat name.txt: Lukas Gross.',
                         css=''.join(css), defs=d + defs.render())


if __name__ == '__main__':
    if not os.path.exists(SRC):
        print(f'übersprungen: Foto {SRC} fehlt, ascii-portrait.svg bleibt unverändert')
        sys.exit(0)
    p = brand.write_asset('ascii-portrait.svg', build(*ascii_cells(SRC)))
    print('geschrieben', p, os.path.getsize(p))
