"""Prüft alle Grafiken in assets/ auf GitHub-Tauglichkeit.

GitHub zeigt die SVGs als <img> an: kein Skript, keine externen Ressourcen,
keine Schriften. Bewegung muss bei prefers-reduced-motion stoppen.

Aufruf: python src/check.py [datei.svg ...]   (ohne Argumente: alle in assets/)
Exit-Code 1 bei Fehlern.
"""
from __future__ import annotations

import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), 'assets')

MAX_BYTES = 150_000
MAX_BYTES_HERO = 220_000
FORBIDDEN_TAGS = {'script', 'foreignObject', 'image', 'iframe', 'animate', 'animateTransform',
                  'animateMotion', 'set'}
NS = '{http://www.w3.org/2000/svg}'
TEXT_ALLOWED = {'ascii-portrait.svg'}
FORBIDDEN_WORDS = [r'\bownCloud\b', r'\bOwnCloud\b']


def check(path: str) -> list[str]:
    errs: list[str] = []
    name = os.path.basename(path)
    raw = open(path, 'rb').read()
    limit = MAX_BYTES_HERO if name.startswith('hero') else MAX_BYTES
    if len(raw) > limit:
        errs.append(f'zu groß: {len(raw)} B > {limit} B')
    text = raw.decode('utf-8')
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return [f'kein gültiges XML: {e}']
    if root.tag != NS + 'svg':
        errs.append('Wurzel ist kein <svg> mit SVG-Namensraum')
    if not root.get('viewBox'):
        errs.append('viewBox fehlt')
    if root.find(NS + 'title') is None or not (root.find(NS + 'title').text or '').strip():
        errs.append('<title> fehlt oder leer')
    ids = []
    for el in root.iter():
        tag = el.tag.replace(NS, '')
        if tag in FORBIDDEN_TAGS:
            errs.append(f'verbotenes Element <{tag}> (SMIL/Skript/Bild – nur CSS-Animationen erlaubt)')
        for k, v in el.attrib.items():
            if k.lower().startswith('on'):
                errs.append(f'Event-Handler {k}')
            if k.endswith('href') and not v.startswith('#'):
                errs.append(f'externer Verweis {k}="{v[:60]}"')
        if el.get('id'):
            ids.append(el.get('id'))
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errs.append(f'doppelte ids: {sorted(dup)[:5]}')
    if re.search(r'url\(\s*["\']?(https?:|//|data:)', text):
        errs.append('url() mit externer/data-Quelle')
    if '@import' in text or '@font-face' in text:
        errs.append('@import/@font-face nicht erlaubt (Texte als Pfade setzen)')
    # ASCII-Kunst nutzt bewusst Systemschriften (monospace) mit festem textLength
    if '<text' in text and name not in TEXT_ALLOWED:
        errs.append('<text> gefunden – Texte müssen als Pfade gesetzt sein (textpath.Font.text)')
    has_anim = '@keyframes' in text
    if has_anim and 'prefers-reduced-motion' not in text:
        errs.append('Animation ohne prefers-reduced-motion-Abschaltung')
    for w in FORBIDDEN_WORDS:
        if re.search(w, text):
            errs.append(f'verbotener Name: {w}')
    return errs


def main(argv: list[str]) -> int:
    files = argv or sorted(glob.glob(os.path.join(ASSETS, '*.svg')))
    bad = 0
    for f in files:
        errs = check(f)
        size = os.path.getsize(f)
        if errs:
            bad += 1
            print(f'FEHLER {os.path.basename(f)} ({size} B)')
            for e in errs:
                print(f'   - {e}')
        else:
            print(f'ok     {os.path.basename(f)} ({size} B)')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
