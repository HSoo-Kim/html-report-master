#!/usr/bin/env python3
"""
Convert LaTeX formulas inside HTML reports to static W3C MathML (offline, zero CDN).

Supported tags in HTML:
  <tex-block>\\frac{\\Delta v}{\\Delta t} \\approx 9.807 \\times \\mathrm{longacc}</tex-block>
  <tex-inline>v_{\\mathrm{lead}} > v_{\\mathrm{ego}}</tex-inline>

CLI usage:
  python scripts/render_tex.py report.html --in-place
  python scripts/render_tex.py report.html -o report_rendered.html

Python import usage:
  from render_tex import tex_block, tex_inline
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

try:
    from latex2mathml.converter import convert as _tex2mml
except ImportError as exc:
    raise SystemExit(
        "latex2mathml is required. Install with: pip install latex2mathml"
    ) from exc


def tex_block(expr: str) -> str:
    """Render a display LaTeX expression to a styled MathML block."""
    clean = expr.strip()
    mml = _tex2mml(clean, display="block")
    esc = html.escape(clean, quote=True)
    return f'<div class="eq-formula" data-tex="{esc}" title="TeX: {esc}">{mml}</div>'


def tex_inline(expr: str) -> str:
    """Render an inline LaTeX expression to a styled MathML span."""
    clean = expr.strip()
    mml = _tex2mml(clean, display="inline")
    esc = html.escape(clean, quote=True)
    return f'<span class="eq-inline" data-tex="{esc}" title="TeX: {esc}">{mml}</span>'


_BLOCK_RE = re.compile(r"<tex-block>(.*?)</tex-block>", re.DOTALL | re.IGNORECASE)
_INLINE_RE = re.compile(r"<tex-inline>(.*?)</tex-inline>", re.DOTALL | re.IGNORECASE)


def render_html(source: str) -> tuple[str, int, int]:
    n_block = 0
    n_inline = 0

    def _rep_block(m: re.Match[str]) -> str:
        nonlocal n_block
        n_block += 1
        return tex_block(html.unescape(m.group(1)))

    def _rep_inline(m: re.Match[str]) -> str:
        nonlocal n_inline
        n_inline += 1
        return tex_inline(html.unescape(m.group(1)))

    out = _BLOCK_RE.sub(_rep_block, source)
    out = _INLINE_RE.sub(_rep_inline, out)
    return out, n_block, n_inline


def main() -> int:
    ap = argparse.ArgumentParser(description="Render <tex-block> and <tex-inline> tags to offline W3C MathML.")
    ap.add_argument("input", type=Path, help="Input HTML file")
    ap.add_argument("-o", "--output", type=Path, help="Output HTML file")
    ap.add_argument("--in-place", action="store_true", help="Overwrite input file in place")
    args = ap.parse_args()

    if not args.in_place and not args.output:
        ap.error("Specify either --in-place or -o/--output.")

    src = args.input.read_text(encoding="utf-8")
    rendered, nb, ni = render_html(src)
    dst = args.input if args.in_place else args.output
    dst.write_text(rendered, encoding="utf-8")
    print(f"Rendered TeX -> MathML: {nb} block(s), {ni} inline(s) -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
