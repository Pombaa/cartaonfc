#!/usr/bin/env python3
"""Standalone dev tool: converts a photo into an ascii-photo.js file, without
touching card.config.json. For the normal workflow (recommended), set
"photo" (and optionally "ascii") in card.config.json and run
`python3 tools/sync.py` instead — this script is for one-off experiments.

Not part of the deployed site.

Usage:
    python3 tools/gen-ascii.py photo.jpg
    python3 tools/gen-ascii.py photo.jpg --columns 120 --output ../ascii-photo.js
    python3 tools/gen-ascii.py photo.jpg --contrast 1.3 --gamma 0.9 --invert
    python3 tools/gen-ascii.py photo.jpg --crop 0.1,0,0.8,1.0   # x,y,w,h (0..1)

Requires Pillow: pip install Pillow
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import _ascii_core
except ImportError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(1)


def parse_crop(value):
    if not value:
        return None
    try:
        x, y, w, h = (float(v) for v in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError('crop deve ser "x,y,w,h" com valores 0..1, ex.: 0.1,0,0.8,1.0') from exc
    return {"x": x, "y": y, "w": w, "h": h}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image", help="Caminho da foto de origem (rosto + ombros, fundo limpo, bom contraste).")
    parser.add_argument("--columns", type=int, default=100, help="Colunas do ASCII (padrão: 100).")
    parser.add_argument("--contrast", type=float, default=1.0, help="Fator de contraste extra, 1.0 = sem alteração (padrão: 1.0).")
    parser.add_argument("--gamma", type=float, default=1.0, help="Correção de gama, 1.0 = sem alteração (padrão: 1.0).")
    parser.add_argument("--invert", action="store_true", help="Inverte o mapeamento (claro->esparso em vez de claro->denso).")
    parser.add_argument("--crop", type=parse_crop, default=None, help='Recorte manual "x,y,w,h" (frações 0..1). Sem isso, recorte automático central para ~3:4 se necessário.')
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent.parent / "ascii-photo.js"),
        help="Caminho de saída para ascii-photo.js (padrão: raiz do repo).",
    )
    args = parser.parse_args()

    ascii_art, warnings = _ascii_core.image_to_ascii(
        args.image,
        cols=args.columns,
        contrast=args.contrast,
        gamma=args.gamma,
        invert=args.invert,
        crop=args.crop,
    )
    for w in warnings:
        print(f"[aviso] {w}", file=sys.stderr)

    if not ascii_art.strip():
        print("ASCII gerado ficou vazio — verifique a imagem de origem.", file=sys.stderr)
        sys.exit(1)

    js = "window.ASCII_PHOTO = %s;\n" % json.dumps(ascii_art)
    Path(args.output).write_text(js, encoding="utf-8")
    rows = ascii_art.count("\n") + 1
    print(f"Escrito {args.output} ({args.columns}x{rows})")


if __name__ == "__main__":
    main()
