"""Laufband „Technologien“: zwei Reihen Text-Pillen, endlos und gegenläufig.

Reihe 1: Programmiersprachen, Reihe 2: Plattform und Standards – beides ermittelt
aus den Repositorys von BWTECH-github (Sprachstatistik, Repo-Namen, READMEs).

Erzeugt assets/tech-light.svg und assets/tech-dark.svg (viewBox 1200×150).
Aufruf: python src/tech.py
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brand  # noqa: E402
from textpath import Font, GlyphDefs  # noqa: E402

W, H = 1200, 150

# Reihe 1 – Sprachen laut GitHub-Sprachstatistik der Repos (owncloud.online, client,
# Android, IOS-App, Plugins, Outlook-Add-in, Bau-Blueprints)
LANGUAGES = [
    'TypeScript', 'React', 'Next.js', 'React Native', 'Expo', 'Svelte', 'Vue', 'Node.js',
    'PHP 8.4', 'C# / .NET 8', 'Blazor', 'Python', 'Swift', 'Kotlin', 'C++',
]

# Reihe 2 – Werkzeuge und Betrieb
STANDARDS = [
    'Prisma', 'MariaDB', 'SQLite', 'Redis', 'Tailwind CSS', 'Docker', 'nginx', 'Linux',
    'Playwright', 'Vitest', 'Stripe', 'OpenID Connect', 'LDAP', 'Yjs (Echtzeit)',
    'GitHub Actions', 'CheckMK', 'PostgreSQL', 'Supabase', 'Socket.IO',
    'KI-gestützte Entwicklung', 'LLM-Integration', 'MCP',
]

# Geometrie (viewBox-Einheiten; GitHub verkleinert ca. 0,7-fach)
PILL_H = 50
PILL_R = PILL_H / 2
FONT_SIZE = 24
GAP = 14
ROW_Y = (17, 83)            # Oberkante der Pillen je Reihe
PAD_DOT_L, DOT_R, DOT_GAP, PAD_R = 20, 5, 12, 22
PAD_PLAIN = 24
FADE = 0.11                 # Breite der weichen Ränder (Anteil der Breite)
SPEED = 26                  # px/s im viewBox – ruhig; Periode ≥ 40 s wird erzwungen
MIN_PERIOD = 40.0
EASE = 'cubic-bezier(.2,.8,.2,1)'

THEMES = {
    'light': {
        'r1_fill': brand.LAVENDER_PALE, 'r1_stroke': brand.LAVENDER, 'r1_text': brand.PURPLE,
        'dot': brand.VIOLET,
        'r2_fill': '#ffffff', 'r2_stroke': brand.LAVENDER, 'r2_text': '#173a55',
        'bg': brand.GITHUB_LIGHT_BG,
    },
    'dark': {
        'r1_fill': '#0c2236', 'r1_stroke': '#1e4a6e', 'r1_text': brand.LAVENDER_LIGHT,
        'dot': '#5cc8f5',
        'r2_fill': '#08131d', 'r2_stroke': '#123150', 'r2_text': '#b9dcf2',
        'bg': brand.GITHUB_DARK_BG,
    },
}


# ---------------------------------------------------------------- Kontrast (WCAG)
def _lum(hex_color: str) -> float:
    h = hex_color.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = out
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _f(v: float) -> str:
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


# ---------------------------------------------------------------- Aufbau
def build_row(items: list[str], font: Font, defs: GlyphDefs, theme: dict, row: int,
              y: float) -> tuple[str, float]:
    """Eine Inhaltsfolge der Reihe (einmal) – liefert Markup und exakte Inhaltsbreite."""
    parts = []
    x = 0.0
    cy = y + PILL_H / 2
    baseline = cy + font.cap_height * FONT_SIZE / font.upem / 2
    for label in items:
        tw = font.measure(label, FONT_SIZE)
        if row == 1:
            w = PAD_DOT_L + 2 * DOT_R + DOT_GAP + tw + PAD_R
            tx = x + PAD_DOT_L + 2 * DOT_R + DOT_GAP
            fill, stroke, col = theme['r1_fill'], theme['r1_stroke'], theme['r1_text']
        else:
            w = PAD_PLAIN * 2 + tw
            tx = x + PAD_PLAIN
            fill, stroke, col = theme['r2_fill'], theme['r2_stroke'], theme['r2_text']
        parts.append(
            f'<rect x="{_f(x + .75)}" y="{_f(y + .75)}" width="{_f(w - 1.5)}" height="{_f(PILL_H - 1.5)}" '
            f'rx="{_f(PILL_R - .75)}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        if row == 1:
            parts.append(f'<circle cx="{_f(x + PAD_DOT_L + DOT_R)}" cy="{_f(cy)}" r="{DOT_R}" '
                         f'fill="{theme["dot"]}"/>')
        parts.append(font.text(label, FONT_SIZE, tx, baseline, defs=defs, attrs=f'fill="{col}"'))
        x += w + GAP
    return ''.join(parts), x   # x = Inhaltsbreite inkl. abschließendem Abstand → exakte Periode


def build(theme_name: str) -> str:
    theme = THEMES[theme_name]
    defs = GlyphDefs('t')
    f1 = Font('Lexend', 500)
    f2 = Font('Lexend', 400)

    # Kontrast der Pillen-Texte gegen ihre Fläche prüfen (Text 22 → normale Schrift, ≥ 4,5:1)
    for key_t, key_f in (('r1_text', 'r1_fill'), ('r2_text', 'r2_fill')):
        c = contrast(theme[key_t], theme[key_f])
        assert c >= 4.5, f'{theme_name}: Kontrast {key_t}/{key_f} = {c:.2f}'

    row1, w1 = build_row(LANGUAGES, f1, defs, theme, 1, ROW_Y[0])
    row2, w2 = build_row(STANDARDS, f2, defs, theme, 2, ROW_Y[1])

    # Gleiches Tempo in beiden Reihen; Periode je Reihe = Inhaltsbreite / Tempo (≥ 40 s)
    speed = min(SPEED, min(w1, w2) / MIN_PERIOD)
    p1, p2 = w1 / speed, w2 / speed

    # Start der Inhalte gleich hinter dem weichen Rand: im Grundzustand (reduzierte Bewegung)
    # steht die erste Pille jeder Reihe vollständig lesbar links
    start = round(W * FADE) + 8

    def copy_range(w: float) -> range:
        # dargestellt: x = Inhalt + start + t, t ∈ [-w, 0] → Inhalt muss [-start, w + W - start] füllen
        kmin = math.floor(-start / w)
        kmax = math.ceil((W - start) / w)
        return range(kmin, kmax + 1)

    def copies(w: float) -> int:
        return len(copy_range(w))

    def track(gid: str, w: float) -> str:
        return ''.join(f'<use href="#{gid}" x="{_f(i * w)}"/>' for i in copy_range(w) if i != 0)

    css = (
        '.mq{transform-box:view-box;transform-origin:0 0}'
        f'.m1{{animation:mq1 {p1:.2f}s linear infinite}}'
        f'.m2{{animation:mq2 {p2:.2f}s linear infinite}}'
        f'@keyframes mq1{{from{{transform:translateX(0)}}to{{transform:translateX(-{w1:.2f}px)}}}}'
        # gegenläufig: von -w nach 0 – Startbild = Grundzustand (Inhalt ist w-periodisch)
        f'@keyframes mq2{{from{{transform:translateX(-{w2:.2f}px)}}to{{transform:translateX(0)}}}}'
        '.in{transform-box:view-box;transform-origin:600px 75px;'
        f'animation:rin .9s {EASE} both}}'
        '.in2{animation-delay:.18s}'
        '@keyframes rin{from{opacity:0;transform:translateY(8px)}}'
    )

    fade_defs = (
        '<linearGradient id="tfg" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset="{FADE}" stop-color="#fff" stop-opacity="1"/>'
        f'<stop offset="{1 - FADE}" stop-color="#fff" stop-opacity="1"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/>'
        '</linearGradient>'
        f'<mask id="tfm" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
        f'<rect width="{W}" height="{H}" fill="url(#tfg)"/></mask>'
    )
    sets = f'<g id="ts1">{row1}</g><g id="ts2">{row2}</g>'

    body = (
        '<g mask="url(#tfm)">'
        f'<g class="in"><g transform="translate({start} 0)">'
        f'<g class="mq m1"><use href="#ts1"/>{track("ts1", w1)}</g></g></g>'
        f'<g class="in in2"><g transform="translate({start} 0)">'
        f'<g class="mq m2"><use href="#ts2"/>{track("ts2", w2)}</g></g></g>'
        '</g>'
    )

    title = 'Mein Stack'
    desc = ('Sprachen: ' + ', '.join(LANGUAGES) + '. Plattform und Standards: '
            + ', '.join(STANDARDS) + '.')
    svg = brand.svg_doc(W, H, body, title=title, desc=desc, css=css,
                        defs=defs.render() + fade_defs + sets)
    print(f'{theme_name}: Reihe 1 {w1:.3f}px/{p1:.4f}s ×{copies(w1)}, '
          f'Reihe 2 {w2:.3f}px/{p2:.4f}s ×{copies(w2)}, Tempo {speed:.1f}px/s')
    return svg


def main() -> None:
    for name in THEMES:
        path = brand.write_asset(f'tech-{name}.svg', build(name))
        print('geschrieben', os.path.relpath(path, brand.ROOT), os.path.getsize(path), 'B')


if __name__ == '__main__':
    main()
