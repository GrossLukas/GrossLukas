"""Baut alle Profil-Grafiken neu und prüft sie.

Aufruf (im Repo-Wurzelverzeichnis): python src/build.py
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Reihenfolge = Reihenfolge im README
GENERATORS = ['hero', 'typeline', 'portrait', 'neofetch', 'tech']


def main() -> int:
    for name in GENERATORS:
        script = os.path.join(HERE, f'{name}.py')
        if not os.path.exists(script):
            print(f'übersprungen: {name}.py fehlt')
            continue
        print(f'baue {name} …')
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)
    return subprocess.run([sys.executable, os.path.join(HERE, 'check.py')], cwd=ROOT).returncode


if __name__ == '__main__':
    sys.exit(main())
