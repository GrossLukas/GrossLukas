"""Text als SVG-Pfade setzen – ohne eingebettete Schriften.

GitHub liefert Bilder mit restriktiver Content-Security-Policy aus; Schriften
in SVG-Bildern sind dort nicht verlässlich. Darum werden alle Texte hier mit
HarfBuzz gesetzt (Kerning, Ligaturen) und als Glyphenpfade ausgegeben.

Nutzung:
    from textpath import Font
    bold = Font('Lexend', 700)
    defs = GlyphDefs()                         # sammelt Glyphen je Datei genau einmal
    svg  = bold.text('Cloud by Design', size=48, x=600, y=200, anchor='middle', defs=defs)
    ...  '<defs>' + defs.render() + '</defs>' + svg

`text()` liefert eine <g> mit <use>-Verweisen; `glyphs()` liefert die Einzelzeichen
für buchstabenweise Animationen; `measure()` die Laufweite in px.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')

FAMILIES = {
    'Lexend': 'Lexend[wght].ttf',
}


def _fmt(v: float) -> str:
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


@dataclass
class Glyph:
    char: str          # zugehöriger Text (bei Ligaturen mehrere Zeichen)
    gid: str           # id in <defs>
    x: float           # Position in px (Ursprung der Glyphe)
    y: float           # Grundlinie in px
    advance: float     # Vorschub in px
    scale: float       # Skalierung Schrift-Einheiten -> px


class GlyphDefs:
    """Sammelt Glyphenpfade, damit jede Glyphe pro SVG nur einmal enthalten ist."""

    def __init__(self, prefix: str = 'g'):
        self.prefix = prefix
        self._paths: dict[str, str] = {}

    def add(self, key: str, d: str) -> str:
        gid = f'{self.prefix}{len(self._paths)}' if key not in self._paths else None
        if gid is not None:
            self._paths[key] = (gid, d)
        return self._paths[key][0]

    def render(self) -> str:
        return ''.join(f'<path id="{gid}" d="{d}"/>' for gid, d in self._paths.values() if d)


class Font:
    def __init__(self, family: str = 'Lexend', weight: int = 400):
        self.family = family
        self.weight = weight
        path = os.path.join(FONT_DIR, FAMILIES[family])
        self.tt = TTFont(path)
        self.upem = self.tt['head'].unitsPerEm
        blob = hb.Blob.from_file_path(path)
        face = hb.Face(blob)
        self.hbfont = hb.Font(face)
        if 'fvar' in self.tt:
            self.hbfont.set_variations({'wght': weight})
        self.glyphset = self.tt.getGlyphSet(location={'wght': weight} if 'fvar' in self.tt else None)
        self.order = self.tt.getGlyphOrder()
        os2 = self.tt['OS/2']
        self.cap_height = getattr(os2, 'sCapHeight', 0) or int(self.upem * 0.7)
        self.x_height = getattr(os2, 'sxHeight', 0) or int(self.upem * 0.5)

    @lru_cache(maxsize=None)
    def _outline(self, name: str) -> str:
        pen = SVGPathPen(self.glyphset, _fmt)
        self.glyphset[name].draw(pen)
        return pen.getCommands()

    def _shape(self, text: str, features: dict | None = None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, features or {'kern': True, 'liga': True})
        return buf.glyph_infos, buf.glyph_positions

    def measure(self, text: str, size: float, letter_spacing: float = 0.0) -> float:
        infos, pos = self._shape(text)
        s = size / self.upem
        return sum(p.x_advance for p in pos) * s + letter_spacing * max(len(infos) - 1, 0)

    def glyphs(self, text: str, size: float, x: float = 0, y: float = 0, anchor: str = 'start',
               letter_spacing: float = 0.0, defs: GlyphDefs | None = None) -> list[Glyph]:
        infos, pos = self._shape(text)
        s = size / self.upem
        total = self.measure(text, size, letter_spacing)
        if anchor == 'middle':
            x -= total / 2
        elif anchor == 'end':
            x -= total
        out: list[Glyph] = []
        pen_x = x
        clusters = [i.cluster for i in infos] + [len(text)]
        for idx, (info, p) in enumerate(zip(infos, pos)):
            name = self.order[info.codepoint]
            key = f'{self.family}-{self.weight}-{name}'
            gid = defs.add(key, self._outline(name)) if defs is not None else key
            gx = pen_x + p.x_offset * s
            gy = y - p.y_offset * s
            adv = p.x_advance * s
            char = text[clusters[idx]:clusters[idx + 1]] if clusters[idx + 1] > clusters[idx] else ''
            out.append(Glyph(char, gid, gx, gy, adv, s))
            pen_x += adv + letter_spacing
        return out

    def text(self, text: str, size: float, x: float = 0, y: float = 0, anchor: str = 'start',
             letter_spacing: float = 0.0, defs: GlyphDefs | None = None, attrs: str = '',
             glyph_attrs=None) -> str:
        """Liefert eine <g> mit <use>-Verweisen (defs) oder Inline-Pfaden (ohne defs).

        glyph_attrs: optional callable(index, Glyph) -> str für zusätzliche Attribute je Glyphe
        (z. B. class oder style mit --i für gestaffelte Animationen).
        """
        parts = []
        for i, g in enumerate(self.glyphs(text, size, x, y, anchor, letter_spacing, defs)):
            if not g.char.strip():
                continue
            extra = (' ' + glyph_attrs(i, g)) if glyph_attrs else ''
            tr = f'translate({_fmt(g.x)} {_fmt(g.y)}) scale({g.scale:.5f} {-g.scale:.5f})'
            if defs is not None:
                parts.append(f'<use href="#{g.gid}" transform="{tr}"{extra}/>')
            else:
                name = g.gid.split('-', 2)[2]
                parts.append(f'<path d="{self._outline(name)}" transform="{tr}"{extra}/>')
        a = (' ' + attrs) if attrs else ''
        return f'<g{a}>{"".join(parts)}</g>'

    def bounds(self, text: str, size: float) -> tuple[float, float, float, float]:
        """Tatsächliche Tintenbox (x0, y0, x1, y1) relativ zu Ursprung/Grundlinie, y nach unten."""
        infos, pos = self._shape(text)
        s = size / self.upem
        x = 0.0
        bx0 = by0 = float('inf')
        bx1 = by1 = float('-inf')
        for info, p in zip(infos, pos):
            name = self.order[info.codepoint]
            bp = BoundsPen(self.glyphset)
            self.glyphset[name].draw(bp)
            if bp.bounds:
                gx0, gy0, gx1, gy1 = bp.bounds
                bx0 = min(bx0, x + gx0 * s); bx1 = max(bx1, x + gx1 * s)
                by0 = min(by0, -gy1 * s); by1 = max(by1, -gy0 * s)
            x += p.x_advance * s
        return bx0, by0, bx1, by1
