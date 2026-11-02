"""ASCII-Porträt im Terminalfenster („./portrait.sh“).

Quelle ist das lokale Foto (wird nicht ins Repo gelegt). Ohne Foto bleibt die
vorhandene assets/ascii-portrait.svg unverändert.

Aufruf: python src/portrait.py [pfad/zum/foto.jpg]
"""
from __future__ import annotations

import os
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps  # noqa: E402

import brand  # noqa: E402
from textpath import Font, GlyphDefs  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\l.gross\Downloads\Lukas.JPG'
CROP = (250, 590, 1030, 1480)          # Kopf, Hals, Schulteransatz (780 x 890)
COLS, ROWS = 59, 36                    # Zellen 7,2 x 13,5 – passt zum Seitenverhältnis des Ausschnitts
RAMP = " .,:;-=+*#%@"                  # dunkel -> hell (helle Stellen = dichte Zeichen)
W, H, R = 600, 600, 16
TEXT_W, TOP, LINE = 425, 64, 13.5
TEXT_X = (600 - TEXT_W) / 2
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
EASE = 'cubic-bezier(.2,.8,.2,1)'
MONO = Font('JetBrainsMono', 500)


def ascii_rows(path: str) -> list[str]:
    im = Image.open(path).convert('L').crop(CROP)
    im = ImageOps.autocontrast(im, cutoff=1)
    im = ImageEnhance.Contrast(im).enhance(1.5).filter(ImageFilter.UnsharpMask(3, 180, 2))
    # Hintergrund (Auto-Innenraum) weich ausblenden, Gesicht bleibt
    mask = Image.new('L', im.size, 0)
    w, h = im.size
    dr = ImageDraw.Draw(mask)
    dr.ellipse((w * .14, h * .0, w * .86, h * .86), fill=255)          # Kopf
    dr.polygon([(w * .3, h * .7), (w * .7, h * .7), (w * 1.0, h), (w * 0, h)], fill=255)  # Hals/Schultern
    mask = mask.filter(ImageFilter.GaussianBlur(w * .035))
    im = Image.composite(im, Image.new('L', im.size, 0), mask)
    im = im.resize((COLS, ROWS), Image.LANCZOS)
    rows = []
    for y in range(ROWS):
        line = ''
        for x in range(COLS):
            v = (im.getpixel((x, y)) / 255) ** 1.35
            line += RAMP[min(int(v * len(RAMP)), len(RAMP) - 1)]
        rows.append(line.rstrip())
    return rows


def build(rows: list[str]) -> str:
    defs = GlyphDefs('p')
    css = [
        f'.row{{animation:row .5s {EASE} var(--d) both}}@keyframes row{{from{{opacity:0;transform:translateX(-8px)}}}}',
        '.scan{transform-box:view-box;animation:scan 2.2s ease-in .1s both}'
        f'@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({H}px);opacity:0}}}}',
        '.fade{animation:fade .4s ease var(--d) both}@keyframes fade{from{opacity:0}}',
        '.cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}',
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
    for i, line in enumerate(rows):
        if not line:
            continue
        # textLength erzwingt dieselbe Breite mit jeder Systemschrift
        n = len(line)
        text.append(f'<text class="row" style="--d:{.15 + i * .04:.3f}s" x="{TEXT_X}" y="{TOP + i * LINE:.1f}" '
                    f'textLength="{TEXT_W * n / COLS:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
                    f'{escape(line)}</text>')
    body.append(f'<g font-family="{FONT}" font-size="12" fill="url(#ag)">{"".join(text)}</g>')
    body.append(f'<rect class="scan" x="1" y="-40" width="{W - 2}" height="40" fill="url(#sg)"/>')
    # Eingabezeile unten
    py = H - 22
    t0 = .15 + ROWS * .04 + .2
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
    d = ('<linearGradient id="ag" x1="0" y1="0" x2="1" y2="1">'
         '<stop offset="0" stop-color="#5eead4"/><stop offset=".55" stop-color="#38bdf8"/>'
         '<stop offset="1" stop-color="#60a5fa"/></linearGradient>'
         '<linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5eead4" stop-opacity="0"/>'
         '<stop offset="1" stop-color="#5eead4" stop-opacity=".22"/></linearGradient>')
    return brand.svg_doc(W, H, ''.join(body), title='ASCII-Porträt von Lukas Gross',
                         desc='Terminalfenster mit einem ASCII-Porträt von Lukas Gross, darunter cat name.txt: Lukas Gross.',
                         css=''.join(css), defs=d + defs.render())


if __name__ == '__main__':
    if not os.path.exists(SRC):
        print(f'übersprungen: Foto {SRC} fehlt, ascii-portrait.svg bleibt unverändert')
        sys.exit(0)
    p = brand.write_asset('ascii-portrait.svg', build(ascii_rows(SRC)))
    print('geschrieben', p, os.path.getsize(p))
