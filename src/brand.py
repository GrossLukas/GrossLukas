"""Markenbausteine für die Profil-Grafiken: Farben, Logo, Icons, SVG-Gerüst.

Quelle der Formen: brand/brand.json
  - Logo „BW.Tech / Cloud by Design“ aus dem Profilbild (B und W als exakte
    Vektoren des Website-Monogramms, „.Tech“ und Slogan vektorisiert)
  - Lösungs-Icons der Website bw.tech (je ein Pfad, einfarbig)
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, 'assets')

with open(os.path.join(HERE, 'brand', 'brand.json'), encoding='utf-8') as fh:
    _BRAND = json.load(fh)

# Farben: Blau/Türkis (Namen aus dem übernommenen Baukasten)
PURPLE = '#0a2a4a'        # Primär: Hintergrund Profilbild, Überschriften Website
PURPLE_DEEP = '#04141f'   # abgedunkelt für Verläufe
VIOLET = '#0a6fb3'        # Akzent (Website-Akzent, Zitatzeichen)
VIOLET_SOFT = '#38bdf8'   # aufgehellter Akzent für dunkle Flächen
LAVENDER = '#cdeaf7'      # helle Fläche
LAVENDER_LIGHT = '#e6f6fc'
LAVENDER_PALE = '#f0f9fd'
WHITE = '#ffffff'
INK = '#0f1e2e'           # Fließtext auf hell

# GitHub-Seitenhintergründe – für Kontrastprüfungen
GITHUB_LIGHT_BG = '#ffffff'
GITHUB_DARK_BG = '#0d1117'

LOGO_W = _BRAND['logo']['width']    # 379 – Koordinatensystem des Logos
LOGO_H = _BRAND['logo']['height']   # 131


def logo_part(name: str, attrs: str = '') -> str:
    """Ein Logo-Buchstabe: 'B', 'W', 'dot', 'T', 'e', 'c', 'h' (Koordinaten im 379×131-System)."""
    p = _BRAND['logo']['parts'][name]
    a = f' {attrs}' if attrs else ''
    if 'transform' in p:
        return f'<path d="{p["d"]}" transform="{p["transform"]}"{a}/>'
    return f'<path d="{p["d"]}"{a}/>'


def logo_part_box(name: str) -> list[float]:
    return _BRAND['logo']['parts'][name]['box']


def tagline_word(word: str, attrs: str = '') -> str:
    """Slogan-Wort aus dem Profilbild: 'Cloud', 'by', 'Design'."""
    a = f' {attrs}' if attrs else ''
    return f'<path d="{_BRAND["logo"]["tagline"][word]["d"]}"{a}/>'


def tagline_letters(word: str) -> list[dict]:
    """Einzelbuchstaben eines Slogan-Worts: [{'box': [x0,y0,x1,y1], 'd': ...}] von links nach rechts."""
    return _BRAND['logo']['tagline'][word]['letters']


def tagline_box(word: str) -> list[float]:
    return _BRAND['logo']['tagline'][word]['box']


def logo(attrs: str = '', with_tagline: bool = True) -> str:
    """Komplettes Logo als <g> im 379×131-System (Füllfarbe über attrs, z. B. fill="#fff")."""
    parts = ''.join(logo_part(n) for n in ('B', 'W', 'dot', 'T', 'e', 'c', 'h'))
    if with_tagline:
        parts += ''.join(tagline_word(w) for w in ('Cloud', 'by', 'Design'))
    a = f' {attrs}' if attrs else ''
    return f'<g{a}>{parts}</g>'


ICON_NAMES = ('cloud', 'backup', 'software', 'it', 'managed', 'ai')


def icon(name: str, size: float, x: float = 0, y: float = 0, attrs: str = '') -> str:
    """Website-Icon als <g>, auf size×size skaliert und bei (x, y) platziert.

    Die Icons sind einfarbig (Aussparungen per evenodd) – Farbe über attrs (fill=…).
    """
    ic = _BRAND['icons'][name]
    vx, vy, vw, vh = (float(v) for v in ic['viewBox'].split())
    s = size / max(vw, vh)
    ox = x + (size - vw * s) / 2 - vx * s
    oy = y + (size - vh * s) / 2 - vy * s
    rule = ' fill-rule="evenodd"' if ic['evenodd'] else ''
    paths = ''.join(f'<path d="{d}"{rule}/>' for d in ic['paths'])
    a = f' {attrs}' if attrs else ''
    return f'<g transform="translate({ox:.3f} {oy:.3f}) scale({s:.5f})"{a}>{paths}</g>'


REDUCED_MOTION_CSS = (
    '@media (prefers-reduced-motion: reduce){*,*::before,*::after{'
    'animation:none!important;transition:none!important}}'
)


def svg_doc(width: int, height: int, body: str, *, title: str, desc: str = '',
            css: str = '', defs: str = '') -> str:
    """Vollständiges, eigenständiges SVG-Dokument.

    - feste viewBox, width=100 % skaliert auf GitHub sauber mit
    - <title>/<desc> für Screenreader (zusätzlich alt-Text im README)
    - Bewegung wird bei prefers-reduced-motion abgeschaltet; Grundzustand muss
      daher immer der fertige, lesbare Endzustand sein
    """
    style = f'<style>{css}{REDUCED_MOTION_CSS}</style>'
    d = f'<desc>{desc}</desc>' if desc else ''
    df = f'<defs>{defs}</defs>' if defs else ''
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-labelledby="t">'
        f'<title id="t">{title}</title>{d}{style}{df}{body}</svg>'
    )


def write_asset(name: str, svg: str) -> str:
    os.makedirs(ASSETS, exist_ok=True)
    path = os.path.join(ASSETS, name)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(svg)
    return path
