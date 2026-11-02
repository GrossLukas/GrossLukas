"""Schreibzeile „Wir sind Ihr Partner für …“ mit Schreibmaschinen-Effekt.

Erzeugt assets/typing-light.svg und assets/typing-dark.svg (viewBox 1200×84, transparent).

Aufbau
  - Vorsatz „Wir sind Ihr Partner für“ steht fest, der wechselnde Begriff beginnt
    linksbündig direkt daneben. Der Gesamtblock ist auf die mittlere Begriffslänge
    zentriert: so springt der Vorsatz nie, und kurze wie lange Begriffe weichen nur
    wenig von der Mitte ab.
  - Jeder Begriff liegt in einem eigenen clipPath-Rechteck, das in diskreten
    Stufen genau an Glyphengrenzen vorrückt (steps) – es erscheint nie ein halbes Zeichen.
  - Ein schmaler Cursor-Balken springt mit und blinkt weich, nur während der Pausen.
  - Der Zyklus beginnt mitten in der Haltephase von „Cloud by Design“ und endet mit
    dem fertig getippten „Cloud by Design“ – dadurch läuft die Schleife ohne Sprung.
  - Grundzustand ohne Animation: „Wir sind Ihr Partner für Cloud by Design“.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fontTools.pens.boundsPen import BoundsPen  # noqa: E402

import brand  # noqa: E402
from intro_util import EASE, f, pct, require_contrast  # noqa: E402
from textpath import Font, GlyphDefs  # noqa: E402

W, H = 1200, 84
SIZE = 36
BASELINE = 55            # Versalmitte liegt so bei ~y 42 = optische Zeilenmitte
PREFIX = 'Ich baue'
TERMS = [
    'Cloud-Plattformen',
    'Web-Apps mit Next.js',
    'iOS- & Android-Apps',
    'Windows-Dienste in .NET',
    'sichere Backends',
    'Tools, die Arbeit sparen',
]

# Zeitverhalten (Sekunden) – ruhig, aber nicht träge
TYPE = 0.082             # je Zeichen tippen
DELETE = 0.038           # je Zeichen löschen
HOLD = 2.6               # fertiger Begriff steht
GAP = 0.45               # leere Zeile vor dem nächsten Begriff
# leichte, feste Unregelmäßigkeit beim Tippen, damit es nicht mechanisch wirkt
JITTER = (1.0, 0.86, 1.12, 0.94, 1.06, 0.9, 1.1, 0.97)

# Cursor-Blinken in Pausen: an – weich aus – aus – weich an
BLINK_FIRST_ON = 0.5
BLINK_FADE = 0.2
BLINK_OFF = 0.35
BLINK_ON = 0.4

THEMES = {
    'light': {
        'bg': brand.GITHUB_LIGHT_BG,
        'prefix': '#4a5d70',          # gedämpftes Lila-Grau
        'term': brand.VIOLET,
    },
    'dark': {
        'bg': brand.GITHUB_DARK_BG,
        'prefix': '#a7bccb',
        'term': '#5cc8f5',
    },
}

regular = Font('Lexend', 400)
semibold = Font('Lexend', 600)


def ink_spans(font: Font, text: str, x: float) -> list[tuple[float, float, float, float] | None]:
    """Je Glyphe: (Stiftposition, Vorschub, Tinte links, Tinte rechts) bzw. None-Tinte bei Leerzeichen."""
    out = []
    for g in font.glyphs(text, SIZE, x, BASELINE):          # ohne defs: gid = Familie-Gewicht-Name
        name = g.gid.split('-', 2)[2]
        bp = BoundsPen(font.glyphset)
        font.glyphset[name].draw(bp)
        if bp.bounds:
            x0, _, x1, _ = bp.bounds
            out.append((g.x, g.advance, g.x + x0 * g.scale, g.x + x1 * g.scale))
        else:
            out.append((g.x, g.advance, None, None))
    return out


def term_geometry(text: str, x: float):
    """Schnittkanten und Cursorpositionen für 0…n getippte Glyphen."""
    spans = ink_spans(semibold, text, x)
    n = len(spans)
    width = semibold.measure(text, SIZE)
    pad = 6
    left, right = x - pad, x + width + pad
    cuts, cursor = [left], [x + 1.5]
    ink_right = x
    for c in range(1, n + 1):
        pen, adv, _, ir = spans[c - 1]
        if ir is not None:
            ink_right = max(ink_right, ir)
        if c == n:
            cuts.append(right)
        else:
            # nächste Glyphe mit Tinte suchen (Leerzeichen haben keine)
            nxt = next((s[2] for s in spans[c:] if s[2] is not None), right)
            if nxt <= ink_right + 0.5:
                # Unterschneidung (z. B. „T-“): kein senkrechter Schnitt möglich, der kein
                # halbes Zeichen zeigt – beide Glyphen erscheinen dann im selben Schritt.
                cuts.append(cuts[-1])
                cursor.append(cursor[-1])
                print(f'  Hinweis: „{text}“ Glyphen {c - 1}+{c} erscheinen gemeinsam (Unterschneidung)')
                continue
            cuts.append((ink_right + nxt) / 2)
        pen_after = pen + adv
        cursor.append(max(pen_after, ink_right) + 4.5)
    return n, width, left, right, cuts, cursor


def build_timeline(lengths: list[int]):
    """Liefert Ereignisse (t, Begriff, Anzahl sichtbarer Glyphen), Ruhephasen und Periode."""
    events: list[tuple[float, int, int]] = []
    rests: list[tuple[float, float]] = []
    t = 0.0
    j = 0

    def tick():
        nonlocal j
        v = JITTER[j % len(JITTER)]
        j += 1
        return TYPE * v

    order = list(range(1, len(lengths))) + [0]
    # Start: Begriff 0 steht fertig da
    n0 = lengths[0]
    events.append((0.0, 0, n0))
    hold_start = 0.0
    t = HOLD
    rests.append((hold_start, t))
    prev = 0
    for k in order:
        # vorherigen Begriff löschen
        n = lengths[prev]
        for m in range(n):
            events.append((t, prev, n - 1 - m))
            if m < n - 1:
                t += DELETE
        gap_start = t
        t += GAP
        rests.append((gap_start, t))
        # neuen Begriff tippen
        n = lengths[k]
        for c in range(1, n + 1):
            events.append((t, k, c))
            if c < n:
                t += tick()
        if k == 0:
            period = t + TYPE   # letzte Glyphe von „Cloud by Design“ steht kurz, dann beginnt der Zyklus neu
            return events, rests, period
        hold_start = t
        t += HOLD
        rests.append((hold_start, t))
        prev = k
    raise AssertionError


def keyframes_steps(name: str, points: list[tuple[float, str]], period: float) -> str:
    """Stufen-Keyframes: Wert gilt ab Zeitpunkt bis zum nächsten (step-end)."""
    seen: dict[str, str] = {}
    for t, v in points:
        seen[pct(t, period)] = v           # gleicher Zeitpunkt -> letzter Wert gewinnt
    # unveränderte Folgewerte weglassen (bei step-end ohnehin wirkungslos), 100 % bleibt
    items = list(seen.items())
    kept = [items[0]] + [items[i] for i in range(1, len(items) - 1) if items[i][1] != items[i - 1][1]]
    seen = dict(kept + [items[-1]])
    body = ''.join(f'{p}{{transform:translateX({v}px)}}' for p, v in seen.items())
    return f'@keyframes {name}{{{body}}}'


def blink_points(rests: list[tuple[float, float]], period: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for a, b in rests:
        pts.append((a, 1.0))
        t = a + BLINK_FIRST_ON
        while True:
            if t + BLINK_FADE + BLINK_OFF + BLINK_FADE > b - 0.05:
                break
            pts += [(t, 1.0), (t + BLINK_FADE, 0.0), (t + BLINK_FADE + BLINK_OFF, 0.0),
                    (t + 2 * BLINK_FADE + BLINK_OFF, 1.0)]
            t += 2 * BLINK_FADE + BLINK_OFF + BLINK_ON
        pts.append((b, 1.0))
    pts.append((period, 1.0))
    pts.sort(key=lambda p: p[0])
    return pts


def build(theme: str) -> tuple[str, float]:
    th = THEMES[theme]
    require_contrast(th['prefix'], th['bg'], 4.5, f'{theme}: Vorsatz')
    require_contrast(th['term'], th['bg'], 4.5, f'{theme}: Begriff')

    defs = GlyphDefs('ty')
    pw = regular.measure(PREFIX, SIZE)
    gap = regular.measure(' ', SIZE) + 1
    widths = [semibold.measure(t, SIZE) for t in TERMS]
    mean_w = sum(widths) / len(widths)
    x0 = (W - (pw + gap + mean_w)) / 2
    tx = x0 + pw + gap
    if tx + max(widths) > W - 40:
        raise SystemExit('längster Begriff ragt zu nah an den Rand')

    geo = [term_geometry(t, tx) for t in TERMS]
    lengths = [g[0] for g in geo]
    events, rests, period = build_timeline(lengths)

    css = []
    clip_defs = []
    terms_svg = []
    for k, (text, (n, width, left, right, cuts, _)) in enumerate(zip(TERMS, geo)):
        full = right - left
        pts = [(t, f(cuts[c] - right)) for t, kk, c in events if kk == k]
        hidden = f(-full)
        if k == 0:
            pts = [(0.0, '0')] + pts + [(period, '0')]
        else:
            pts = [(0.0, hidden)] + pts + [(period, hidden)]
        css.append(keyframes_steps(f'tyc{k}', pts, period))
        base = '' if k == 0 else f'transform:translateX({hidden}px);'
        css.append(f'.tyr{k}{{transform-box:view-box;transform-origin:0 0;{base}'
                   f'animation:tyc{k} {f(period, 3)}s step-end infinite}}')
        clip_defs.append(
            f'<clipPath id="tyk{k}" clipPathUnits="userSpaceOnUse">'
            f'<rect class="tyr{k}" x="{f(left)}" y="0" width="{f(full)}" height="{H}"/></clipPath>'
        )
        terms_svg.append(
            f'<g clip-path="url(#tyk{k})">'
            + semibold.text(text, SIZE, tx, BASELINE, defs=defs) + '</g>'
        )

    # Cursor: Position in Stufen über den ganzen Zyklus, Blinken weich in den Pausen
    cur0 = geo[0][5][lengths[0]]
    cpts = [(t, f(geo[k][5][c] - cur0)) for t, k, c in events]
    cpts.append((period, '0'))
    css.append(keyframes_steps('tyx', cpts, period))
    bl = blink_points(rests, period)
    seen: dict[str, float] = {}
    for t, v in bl:
        seen[pct(t, period)] = v
    css.append('@keyframes tyb{' + ''.join(f'{p}{{opacity:{f(v)}}}' for p, v in seen.items()) + '}')
    css.append(f'.tyx{{transform-box:view-box;transform-origin:0 0;animation:tyx {f(period, 3)}s step-end infinite}}')
    css.append(f'.tyb{{animation:tyb {f(period, 3)}s linear infinite}}')
    # ohne Bewegung kein stehender Cursor – der Satz ist dann einfach fertig
    css.append('@media (prefers-reduced-motion: reduce){.tyb{opacity:0}}')
    # sanfte, einmalige Einblendung der ganzen Zeile
    css.append('@keyframes tyin{from{opacity:0;transform:translateY(6px)}}')
    css.append(f'.tyw{{transform-box:view-box;transform-origin:0 0;animation:tyin .8s {EASE} .1s both}}')

    cap_top = BASELINE - semibold.cap_height / semibold.upem * SIZE
    cursor = (
        f'<g class="tyx"><rect class="tyb" x="{f(cur0)}" y="{f(cap_top - 3)}" width="3" '
        f'height="{f(BASELINE + 7 - (cap_top - 3))}" rx="1.5" fill="{th["term"]}"/></g>'
    )
    body = (
        '<g class="tyw">'
        + regular.text(PREFIX, SIZE, x0, BASELINE, defs=defs, attrs=f'fill="{th["prefix"]}"')
        + f'<g fill="{th["term"]}">' + ''.join(terms_svg) + '</g>'
        + cursor
        + '</g>'
    )
    title = 'Ich baue ' + ', '.join(TERMS[:-1]) + ' und ' + TERMS[-1]
    return brand.svg_doc(
        W, H, body,
        title=title.replace('&', '&amp;'),
        desc='Schreibzeile: Der Begriff nach „Ich baue“ wird nacheinander getippt und wieder gelöscht.',
        css=''.join(css),
        defs=defs.render() + ''.join(clip_defs),
    ), period


def main() -> None:
    sys.stdout.reconfigure(errors='replace')   # Konsolen ohne UTF-8 nicht abbrechen lassen
    for theme in THEMES:
        svg, period = build(theme)
        p = brand.write_asset(f'typing-{theme}.svg', svg)
        print(f'{os.path.relpath(p)}  Zyklus {period:.2f} s  {len(svg.encode())} B')


if __name__ == '__main__':
    main()
