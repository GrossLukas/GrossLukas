"""Steckbrief im neofetch-Stil („~$ neofetch“) – gleiche Höhe wie das ASCII-Porträt."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brand  # noqa: E402
from textpath import Font, GlyphDefs  # noqa: E402

W, H, R = 600, 600, 16
EASE = 'cubic-bezier(.2,.8,.2,1)'
MONO, MONO_B = Font('JetBrainsMono', 500), Font('JetBrainsMono', 700)
SIZE = 17
LABEL_X, VALUE_X = 28, 28 + 10 * 10.2   # Werte starten nach 10 Zeichen
# (Bezeichnung, Wert) – neue Zeile einfach anhängen; max. ~40 Zeichen je Wert
ROWS = [
    ('Rolle', 'Full-Stack-Entwickler'),
    ('Frontend', 'TypeScript · React · Next.js'),
    ('Mobile', 'React Native · Expo · Swift · Kotlin'),
    ('Backend', 'Node.js · PHP · C# / .NET'),
    ('Daten', 'MariaDB · PostgreSQL · SQLite'),
    ('Infra', 'Docker · nginx · Linux'),
    ('CI/CD', 'GitHub Actions · Playwright'),
    ('KI', 'Claude · Codex · LLMs'),
    ('Editor', 'VS Code'),
]
PALETTE = ('#0f2a40', '#155e75', '#0e7490', '#0891b2', '#06b6d4', '#22d3ee', '#67e8f9', '#cffafe')


def build() -> str:
    defs = GlyphDefs('n')
    css = [f'.ln{{animation:ln .45s {EASE} var(--d) both}}@keyframes ln{{from{{opacity:0;transform:translateX(-10px)}}}}',
           '.fade{animation:fade .4s ease var(--d) both}@keyframes fade{from{opacity:0}}',
           '.cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}']
    body = [
        f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{R}" fill="#08131d" '
        f'stroke="{brand.VIOLET_SOFT}" stroke-opacity=".35"/>',
        f'<path d="M1 40h{W - 2}" stroke="#ffffff" stroke-opacity=".08"/>',
        ''.join(f'<circle cx="{22 + k * 18}" cy="20" r="5.5" fill="{c}"/>'
                for k, c in enumerate(('#ff5f57', '#febc2e', '#28c840'))),
        MONO.text('lukas@github: ~$ neofetch', 13, W / 2, 25, anchor='middle', defs=defs,
                  attrs='fill="#ffffff" fill-opacity=".5"'),
    ]
    y = 92
    head_w = MONO_B.measure('lukas@github', 20)
    body.append(f'<g class="ln" style="--d:.15s">'
                + MONO_B.text('lukas', 20, LABEL_X, y, defs=defs, attrs='fill="#5eead4"')
                + MONO_B.text('@github', 20, LABEL_X + MONO_B.measure('lukas', 20), y, defs=defs,
                              attrs=f'fill="{brand.VIOLET_SOFT}"') + '</g>')
    body.append(f'<path class="ln" style="--d:.25s" d="M{LABEL_X} {y + 16}h{W - 2 * LABEL_X}" '
                f'stroke="{brand.VIOLET_SOFT}" stroke-opacity=".35"/>')
    y += 56
    for i, (label, value) in enumerate(ROWS):
        d = .35 + i * .11
        body.append(f'<g class="ln" style="--d:{d:.2f}s">'
                    + MONO_B.text(label, SIZE, LABEL_X, y, defs=defs, attrs='fill="#5eead4"')
                    + MONO.text(value, SIZE, VALUE_X, y, defs=defs, attrs='fill="#d6eaf5"') + '</g>')
        y += 34
    # Farbblöcke wie bei neofetch
    y += 8
    t = .35 + len(ROWS) * .11
    bw = (W - 2 * LABEL_X) / len(PALETTE)
    body.append(f'<g class="ln" style="--d:{t:.2f}s">'
                + ''.join(f'<rect x="{LABEL_X + k * bw:.1f}" y="{y}" width="{bw - 6:.1f}" height="22" rx="4" fill="{c}"/>'
                          for k, c in enumerate(PALETTE)) + '</g>')
    # Eingabezeile unten
    py = H - 22
    body.append(f'<path d="M1 {H - 48}h{W - 2}" stroke="#ffffff" stroke-opacity=".08"/>')
    prompt = 'lukas@github:~$'
    body.append(MONO.text(prompt, 15, 20, py, defs=defs,
                          attrs=f'class="fade" style="--d:{t + .3:.2f}s" fill="{brand.VIOLET_SOFT}"'))
    cx = 20 + MONO.measure(prompt + ' ', 15)
    body.append(f'<g class="fade" style="--d:{t + .45:.2f}s"><rect class="cur" x="{cx:.1f}" y="{py - 14}" '
                f'width="9" height="18" rx="1.5" fill="{brand.VIOLET_SOFT}"/></g>')
    desc = 'Steckbrief im Stil von neofetch: ' + '; '.join(f'{a}: {b}' for a, b in ROWS) + '.'
    return brand.svg_doc(W, H, ''.join(body), title='lukas@github – Steckbrief', desc=desc.replace('&', '&amp;'),
                         css=''.join(css), defs=defs.render())


if __name__ == '__main__':
    p = brand.write_asset('neofetch.svg', build())
    print('geschrieben', p, os.path.getsize(p))
