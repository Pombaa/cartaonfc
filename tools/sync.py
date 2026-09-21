#!/usr/bin/env python3
"""Single source of truth -> static site. Dev-only tool, not part of the
deployed site (contacts/, ascii-art.js, ascii-photo.js and the .vcf are).

Usage:
    python3 tools/sync.py            regenerate contacts/index.html, the .vcf,
                                      and ascii-photo.js (if "photo" is set)
    python3 tools/sync.py --check    print pending setup items (photo,
                                      portfolio_url, site_url, og_image,
                                      extras) in Portuguese. Always exits 0.
    python3 tools/sync.py --og       screenshot the card with Playwright,
                                      compose contacts/og.png (1200x630),
                                      and fill "og_image" in the config.

Requires: Pillow (always). vobject (optional, for .vcf validation).
Playwright (optional, only for --og). See README.md.
"""

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _cardlib import (  # noqa: E402
    ROOT, CONFIG_PATH, INDEX_PATH, ASCII_PHOTO_JS,
    SyncError, load_config, replace_marker, contrast_warnings,
)
import _html_regions as R  # noqa: E402
from _vcf import build_vcf_bytes, validate_vcf  # noqa: E402


def resolve_photo_path(cfg):
    if not cfg.get("photo"):
        return None
    p = Path(cfg["photo"])
    return p if p.is_absolute() else (ROOT / p)


def sync_html(cfg):
    text = INDEX_PATH.read_text(encoding="utf-8")
    original = text

    photo_active = bool(cfg.get("photo"))

    text = replace_marker(text, "title", R.build_title(cfg))
    text = replace_marker(text, "description", R.build_description(cfg))
    text = replace_marker(text, "og", R.build_og(cfg))
    text = replace_marker(text, "theme", R.build_theme(cfg), style="css")
    text = replace_marker(text, "topbar", R.build_topbar(cfg))
    text = replace_marker(text, "portrait", R.build_portrait(cfg))
    text = replace_marker(text, "identity", R.build_identity(cfg))
    text = replace_marker(text, "bio", R.build_bio(cfg))
    text = replace_marker(text, "chips", R.build_chips(cfg))
    text = replace_marker(text, "ctas", R.build_ctas(cfg))
    text = replace_marker(text, "secondary", R.build_secondary(cfg))
    text = replace_marker(text, "ascii-script", R.build_ascii_script(photo_active))

    if text == original:
        print(f"[html] {INDEX_PATH.relative_to(ROOT)} já estava sincronizado (sem mudanças).")
        return False
    INDEX_PATH.write_text(text, encoding="utf-8")
    print(f"[html] {INDEX_PATH.relative_to(ROOT)} atualizado.")
    return True


def sync_vcf(cfg):
    vcf_path = ROOT / "contacts" / cfg["vcf_filename"]
    new_bytes = build_vcf_bytes(cfg)
    old_bytes = vcf_path.read_bytes() if vcf_path.exists() else None
    if old_bytes == new_bytes:
        print(f"[vcf] {vcf_path.relative_to(ROOT)} já estava sincronizado (sem mudanças).")
    else:
        vcf_path.write_bytes(new_bytes)
        print(f"[vcf] {vcf_path.relative_to(ROOT)} atualizado.")

    ok, msg = validate_vcf(new_bytes)
    if ok is False:
        print(f"[vcf][ERRO] {msg}")
        raise SyncError("vCard gerado não passou na validação — corrija card.config.json.")
    prefix = "[vcf]" if ok else "[vcf][aviso]"
    print(f"{prefix} {msg}")


def sync_ascii(cfg):
    photo_path = resolve_photo_path(cfg)
    if not photo_path:
        if ASCII_PHOTO_JS.exists():
            ASCII_PHOTO_JS.unlink()
            print(f"[ascii] {ASCII_PHOTO_JS.relative_to(ROOT)} removido (sem \"photo\" no config; fallback de iniciais ativo).")
        else:
            print("[ascii] sem foto configurada — fallback de iniciais ativo.")
        return

    if not photo_path.exists():
        raise SyncError(f'"photo" aponta para um arquivo que não existe: {photo_path}')

    import _ascii_core

    ascii_cfg = cfg["ascii"]
    ascii_text, warnings = _ascii_core.image_to_ascii(
        str(photo_path),
        cols=ascii_cfg["cols"],
        contrast=ascii_cfg["contrast"],
        gamma=ascii_cfg["gamma"],
        invert=ascii_cfg["invert"],
        crop=ascii_cfg["crop"],
    )
    for w in warnings:
        print(f"[ascii][aviso] {w}")

    import json as _json
    js = "window.ASCII_PHOTO = %s;\n" % _json.dumps(ascii_text)
    old = ASCII_PHOTO_JS.read_text(encoding="utf-8") if ASCII_PHOTO_JS.exists() else None
    if old == js:
        print(f"[ascii] {ASCII_PHOTO_JS.relative_to(ROOT)} já estava sincronizado (sem mudanças).")
    else:
        ASCII_PHOTO_JS.write_text(js, encoding="utf-8")
        rows = ascii_text.count("\n") + 1
        print(f"[ascii] {ASCII_PHOTO_JS.relative_to(ROOT)} gerado ({ascii_cfg['cols']}x{rows}, a partir de {photo_path.name}).")


def cmd_apply(cfg):
    changed_html = sync_html(cfg)
    sync_vcf(cfg)
    sync_ascii(cfg)
    for w in contrast_warnings(cfg):
        print(f"[tema][aviso] {w}")
    print("\nOK — card.config.json sincronizado com contacts/index.html e o .vcf.")
    return changed_html


PENDING_ITEMS = [
    (
        "photo",
        "Foto do retrato",
        'sem foto, o retrato mostra as iniciais "{initials}" (fallback ativo, funciona normalmente).',
        '"photo" em card.config.json, ex.: "assets/foto.jpg"',
        "python3 tools/sync.py",
    ),
    (
        "portfolio_url",
        "Link do portfólio (seta de voltar)",
        "sem portfolio_url, a barra superior não mostra seta de voltar — o handle ocupa o canto esquerdo.",
        '"portfolio_url" em card.config.json',
        "python3 tools/sync.py",
    ),
    (
        "site_url",
        "URL do site (GitHub Pages)",
        "sem site_url, og:url e <link rel=\"canonical\"> não são gerados no <head>.",
        '"site_url" em card.config.json, ex.: "https://pombaa.github.io/meu-repo"',
        "python3 tools/sync.py",
    ),
    (
        "og_image",
        "Imagem de compartilhamento (og:image)",
        "sem og_image, o preview do link em redes sociais não mostra imagem.",
        '"og_image" em card.config.json, ou gere com o comando ao lado',
        "python3 tools/sync.py --og",
    ),
    (
        "extras",
        "Redes extras",
        "nenhuma configurada (opcional, até 4). Hoje só GitHub e E-mail aparecem nos links secundários.",
        '"extras" em card.config.json: lista de {"label": "...", "url": "..."}',
        "python3 tools/sync.py",
    ),
]


def cmd_check(cfg):
    pending = []
    for key, title, effect, field, command in PENDING_ITEMS:
        value = cfg.get(key)
        is_empty = (value is None) or (isinstance(value, (list, str)) and len(value) == 0)
        if is_empty:
            pending.append((title, effect.format(initials=cfg.get("initials", "")), field, command))

    if not pending:
        print("Nenhuma pendência — todos os campos opcionais (foto, portfolio_url, site_url, og_image, extras) estão preenchidos.")
        return

    print("Pendências do cartão:\n")
    for title, effect, field, command in pending:
        print(f"[ ] {title}")
        print(f"    Efeito atual: {effect}")
        print(f"    Campo: {field}")
        print(f"    Comando: {command}")
        print()


def cmd_og(cfg):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SyncError(
            "Playwright (Python) não está instalado. Rode:\n"
            "  pip install playwright && python3 -m playwright install chromium"
        )
    from PIL import Image
    import http.server
    import socketserver
    import threading
    import re

    # Make sure the page reflects the current config before screenshotting it.
    cmd_apply(cfg)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    with socketserver.TCPServer(("127.0.0.1", 0), lambda *a: QuietHandler(*a, directory=str(ROOT))) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 800, "height": 1000})
                page.goto(f"http://127.0.0.1:{port}/contacts/?lang=pt", wait_until="networkidle")
                card_png = ROOT / "contacts" / "_og_card_tmp.png"
                page.locator(".card").screenshot(path=str(card_png))
                browser.close()
        finally:
            httpd.shutdown()

    bg_match = re.search(r"--bg:\s*(#[0-9a-fA-F]{6})", INDEX_PATH.read_text(encoding="utf-8"))
    bg_hex = bg_match.group(1) if bg_match else "#0b0710"

    canvas = Image.new("RGB", (1200, 630), bg_hex)
    card_img = Image.open(card_png)
    max_h = 590
    scale = min(max_h / card_img.height, 480 / card_img.width)
    new_size = (max(1, round(card_img.width * scale)), max(1, round(card_img.height * scale)))
    card_img = card_img.resize(new_size, Image.LANCZOS)
    x = (1200 - new_size[0]) // 2
    y = (630 - new_size[1]) // 2
    canvas.paste(card_img, (x, y))

    og_path = ROOT / "contacts" / "og.png"
    canvas.save(og_path)
    card_png.unlink(missing_ok=True)
    print(f"[og] {og_path.relative_to(ROOT)} gerado (1200x630).")

    cfg["og_image"] = "og.png"
    import json
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print('[og] "og_image" atualizado em card.config.json para "og.png".')

    cmd_apply(cfg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="lista pendências, sempre sai com código 0")
    group.add_argument("--og", action="store_true", help="gera contacts/og.png via Playwright")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="caminho alternativo para card.config.json")
    args = parser.parse_args()

    try:
        cfg = load_config(args.config)
        if args.check:
            cmd_check(cfg)
            return 0
        if args.og:
            cmd_og(cfg)
            return 0
        cmd_apply(cfg)
        return 0
    except SyncError as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
