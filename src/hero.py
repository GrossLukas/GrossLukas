"""Kopfgrafik: Name, Rolle, Terminal mit getippten Befehlen."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brand  # noqa: E402
from textpath import Font, GlyphDefs  # noqa: E402

W, H, R = 1200, 340, 24
EASE = 'cubic-bezier(.2,.8,.2,1)'
F700, F500, F400 = Font('Lexend', 700), Font('Lexend', 500), Font('Lexend', 400)

PILLS = ('Web & Mobile', 'Cloud & Backend', 'Windows & .NET')
# Terminal: (Prompt-Zeile, Ausgabe)
LINES = [
    ('whoami', 'lukas – Entwickler bei BW.Tech'),
    ('ls ~/projekte', 'owncloud.online   workspace   tourneo'),
    ('git push origin main', 'fertig – live'),
]


def build() -> str:
    defs = GlyphDefs('h')
    css = [f'.fu{{animation:fu .8s {EASE} var(--d) both}}'
           '@keyframes fu{from{opacity:0;transform:translateY(14px)}}'
           '.fade{animation:fade .5s ease var(--d) both}@keyframes fade{from{opacity:0}}'
           '.glow{transform-box:view-box;transform-origin:900px 120px;animation:glow 18s ease-in-out infinite alternate}'
           '@keyframes glow{to{transform:translate(-120px,40px) scale(1.15)}}'
           '.cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}']
    body = [
        f'<rect width="{W}" height="{H}" rx="{R}" fill="url(#bg)"/>',
        f'<g clip-path="url(#clip)"><circle class="glow" cx="900" cy="120" r="320" fill="url(#gl)"/>'
        f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity=".5"/></g>',
        f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{R}" fill="none" stroke="#ffffff" stroke-opacity=".08"/>',
    ]
    # Links: Name, Rolle, Pillen
    body.append(F500.text('Hallo, ich bin', 26, 64, 92, defs=defs,
                          attrs=f'class="fu" style="--d:.05s" fill="{brand.LAVENDER}"'))
    body.append(F700.text('Lukas Gross', 76, 60, 170, defs=defs, letter_spacing=-1,
                          attrs='class="fu" style="--d:.2s" fill="#fff"'))
    body.append(F400.text('Full-Stack-Entwickler bei BW.Tech GmbH', 26, 64, 214, defs=defs,
                          attrs=f'class="fu" style="--d:.4s" fill="{brand.LAVENDER}"'))
    x = 64
    for i, p in enumerate(PILLS):
        w = F500.measure(p, 20) + 36
        body.append(f'<g class="fu" style="--d:{.6 + i * .1:.2f}s">'
                    f'<rect x="{x}" y="250" width="{w:.1f}" height="38" rx="19" fill="#ffffff" fill-opacity=".06" '
                    f'stroke="#ffffff" stroke-opacity=".28"/>'
                    + F500.text(p, 20, x + 18, 276, defs=defs, attrs=f'fill="{brand.LAVENDER_LIGHT}"') + '</g>')
        x += w + 12

    # Rechts: Terminal
    tx, ty, tw, th = 700, 52, 448, 236
    body.append(f'<g class="fu" style="--d:.3s">'
                f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="16" fill="#12051d" fill-opacity=".86" '
                f'stroke="{brand.VIOLET_SOFT}" stroke-opacity=".35"/>'
                f'<path d="M{tx} {ty + 40}h{tw}" stroke="#ffffff" stroke-opacity=".08"/>'
                + ''.join(f'<circle cx="{tx + 24 + k * 20}" cy="{ty + 20}" r="6" fill="{c}"/>'
                          for k, c in enumerate(('#ff5f57', '#febc2e', '#28c840')))
                + F400.text('~/bw.tech', 16, tx + tw / 2, ty + 26, anchor='middle', defs=defs,
                            attrs='fill="#ffffff" fill-opacity=".45"') + '</g>')
    t = 1.0
    y = ty + 78
    for i, (cmd, out) in enumerate(LINES):
        line = '$ ' + cmd
        lw = F400.measure(line, 21)
        dur = 0.05 * len(line)
        css.append(f'.ty{i}{{transform-box:fill-box;transform-origin:left;animation:ty{i} {dur:.2f}s steps({len(line)}) {t:.2f}s both}}'
                   f'@keyframes ty{i}{{from{{transform:scaleX(0)}}}}')
        body.append(f'<clipPath id="c{i}"><rect class="ty{i}" x="{tx + 24}" y="{y - 22}" width="{lw + 4:.1f}" height="30"/></clipPath>')
        body.append(f'<g clip-path="url(#c{i})">'
                    + F400.text('$', 21, tx + 24, y, defs=defs, attrs=f'fill="{brand.VIOLET_SOFT}"')
                    + F400.text(cmd, 21, tx + 24 + F400.measure('$ ', 21), y, defs=defs, attrs='fill="#ffffff"')
                    + '</g>')
        t += dur + 0.25
        color = '#5eead4' if out.endswith('live') else '#cdbbe9'
        body.append(F400.text(out, 19, tx + 24, y + 28, defs=defs,
                              attrs=f'class="fade" style="--d:{t:.2f}s" fill="{color}"'))
        t += 0.45
        last_out = (out, y + 28)
        y += 58
    # Cursor hinter der letzten Ausgabe
    out, oy = last_out
    cx = tx + 24 + F400.measure(out, 19) + 8
    css.append(f'.curw{{animation:fade .3s ease {t:.2f}s both}}')
    body.append(f'<g class="curw"><rect class="cur" x="{cx:.1f}" y="{oy - 18}" width="10" height="22" rx="2" '
                f'fill="{brand.VIOLET_SOFT}"/></g>')

    d = (f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{brand.PURPLE}"/>'
         f'<stop offset="1" stop-color="#14001f"/></linearGradient>'
         f'<radialGradient id="gl"><stop offset="0" stop-color="{brand.VIOLET}" stop-opacity=".45"/>'
         f'<stop offset="1" stop-color="{brand.VIOLET}" stop-opacity="0"/></radialGradient>'
         f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">'
         f'<circle cx="2" cy="2" r="1.2" fill="#fff" fill-opacity=".14"/></pattern>'
         f'<clipPath id="clip"><rect width="{W}" height="{H}" rx="{R}"/></clipPath>')
    return brand.svg_doc(W, H, ''.join(body), title='Lukas Gross – Full-Stack-Entwickler bei BW.Tech GmbH',
                         desc='Hallo, ich bin Lukas Gross, Full-Stack-Entwickler bei BW.Tech GmbH. Web &amp; Mobile, '
                              'Cloud &amp; Backend, Windows &amp; .NET. Daneben ein Terminal mit whoami, ls ~/projekte '
                              '(owncloud.online, workspace, tourneo) und git push.',
                         css=''.join(css), defs=d + defs.render())


if __name__ == '__main__':
    p = brand.write_asset('hero.svg', build())
    print('geschrieben', p, os.path.getsize(p))
