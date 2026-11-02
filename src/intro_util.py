"""Kleine Hilfen für die Intro-Grafiken (Schreibzeile, Buttons, Fußzeile).

Nur von typing.py, buttons.py und footer.py genutzt.
"""
from __future__ import annotations

EASE = 'cubic-bezier(.2,.8,.2,1)'


def f(v: float, nd: int = 2) -> str:
    """Zahl kompakt formatieren (keine überflüssigen Nullen, kein -0)."""
    s = f'{v:.{nd}f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s


def pct(t: float, period: float) -> str:
    """Zeitpunkt als Keyframe-Prozentwert (4 Nachkommastellen ~ Bruchteil einer ms)."""
    p = max(0.0, min(100.0, t / period * 100))
    s = f'{p:.4f}'.rstrip('0').rstrip('.')
    return (s or '0') + '%'


def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def require_contrast(fg: str, bg: str, minimum: float, what: str) -> float:
    """Bricht den Bau ab, wenn ein Text den Mindestkontrast verfehlt."""
    c = contrast(fg, bg)
    if c < minimum:
        raise SystemExit(f'Kontrast zu gering ({what}): {fg} auf {bg} = {c:.2f} < {minimum}')
    return c
