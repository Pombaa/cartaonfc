#!/usr/bin/env python3
"""Runs the acceptance-criteria battery (zero scroll, zero external
requests, zero console issues, correct hrefs, AA contrast, valid .vcf, i18n,
keyboard) across 8 viewports x 2 languages, in 4 scenarios, each on a
throwaway temp copy of the project (never touching this repo):

  (i)   estado atual de card.config.json
  (ii)  com uma foto sintética (retrato ASCII ativo)
  (iii) com portfolio_url + site_url + 4 extras preenchidos
  (iv)  subpath — serve o projeto sob /cartaonfc/, como no GitHub Pages
        de project site, provando que nenhum path quebra com o prefixo

Screenshots dos 3 viewports landscape/baixa-altura (evidência visual, não
usados como critério de pass/fail) vão para verify-output/ (git-ignorado).

Dev-only. Requires Pillow, Playwright (Python) and, optionally, vobject.
    pip install Pillow playwright vobject
    python3 -m playwright install chromium

Usage:
    python3 tools/verify.py
"""

import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _cardlib import js_encode_uri_component, contrast_ratio  # noqa: E402
from _vcf import validate_vcf  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

VIEWPORTS = [
    ("360x640", 360, 640),
    ("390x844", 390, 844),
    ("768x1024", 768, 1024),
    ("1366x768", 1366, 768),
    ("1920x1080", 1920, 1080),
    ("640x360", 640, 360),
    ("844x390", 844, 390),
    ("1024x600", 1024, 600),
]
LANGS = ["pt", "en"]

# Landscape/low-height viewports added for the compaction media query — kept
# separate so run_battery can screenshot just these as visual evidence.
LOW_HEIGHT_VIEWPORTS = {"640x360", "844x390", "1024x600"}

OUT_DIR = ROOT / "verify-output"


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def wait_for_server(port, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def make_synthetic_photo(path):
    from PIL import Image, ImageDraw
    w, h = 400, 500
    img = Image.new("L", (w, h), color=30)
    draw = ImageDraw.Draw(img)
    draw.ellipse((60, 340, 340, 560), fill=90)
    draw.ellipse((120, 80, 280, 280), fill=180)
    draw.ellipse((150, 110, 220, 180), fill=230)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def prepare_scenario(name):
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"cartao-verify-{name}-"))
    project = tmp_dir / "project"
    shutil.copytree(ROOT, project)

    config_path = project / "card.config.json"
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    expect = {"photo": False, "back_link": False, "extras": []}

    if name == "foto-sintetica":
        photo_path = project / "assets" / "test-photo.png"
        make_synthetic_photo(photo_path)
        cfg["photo"] = "assets/test-photo.png"
        expect["photo"] = True

    elif name == "portfolio-site-extras":
        cfg["portfolio_url"] = "https://example.com/portfolio/"
        cfg["site_url"] = "https://pombaa.github.io/exemplo-repo"
        cfg["extras"] = [
            {"label": "Instagram", "url": "https://example.com/instagram"},
            {"label": "X", "url": "https://example.com/x"},
            {"label": "Threads", "url": "https://example.com/threads"},
            {"label": "Discord", "url": "https://example.com/discord"},
        ]
        expect["back_link"] = True
        expect["extras"] = cfg["extras"]

    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "tools/sync.py"], cwd=project, capture_output=True, text=True
    )
    sync_ok = result.returncode == 0
    return tmp_dir, project, cfg, expect, sync_ok, result.stdout + result.stderr


def rel_luminance_from_rgb_string(rgb):
    nums = [int(n) for n in rgb.strip().split(",") if n.strip()]
    return nums


def to_hex(rgb_css):
    # rgb_css like "rgb(168, 117, 255)"
    nums = [int(n) for n in rgb_css[rgb_css.find("(") + 1: rgb_css.find(")")].split(",")[:3]]
    return "#" + "".join(f"{n:02x}" for n in nums)


def run_battery(page, base_url, cfg, expect, failures, console_issues, external_hosts, shot_dir=None):
    def on_console(msg):
        if msg.type in ("error", "warning"):
            console_issues.append(f"{msg.type}: {msg.text}")

    def on_request(req):
        url = req.url
        if not url.startswith(base_url.split("/contacts/")[0]) and not url.startswith("data:"):
            external_hosts.append(f"{req.method} {url}")

    page.on("console", on_console)
    page.on("request", on_request)

    wa_expected = f'https://wa.me/{cfg["wa_number"]}?text={js_encode_uri_component(cfg["wa_message"])}'
    expected_hrefs = {
        ".cta-whatsapp": wa_expected,
        ".cta-linkedin": cfg["linkedin"],
        ".cta-vcf": cfg["vcf_filename"],
        'a[href*="github.com"]': cfg["github"],
        'a[href^="mailto:"]': "mailto:" + cfg["email"],
    }

    for vp_name, w, h in VIEWPORTS:
        for lang in LANGS:
            label = f"{vp_name}/{lang}"
            page.set_viewport_size({"width": w, "height": h})
            page.goto(f"{base_url}?lang={lang}", wait_until="networkidle")
            page.wait_for_timeout(120)

            if shot_dir and vp_name in LOW_HEIGHT_VIEWPORTS:
                shot_dir.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(shot_dir / f"{vp_name}_{lang}.png"))

            dims = page.evaluate(
                "() => ({sh: document.documentElement.scrollHeight, ih: window.innerHeight,"
                " sw: document.documentElement.scrollWidth, iw: window.innerWidth})"
            )
            if dims["sh"] > dims["ih"]:
                failures.append(f"SCROLL(V) {label}: scrollHeight={dims['sh']} > innerHeight={dims['ih']}")
            if dims["sw"] > dims["iw"]:
                failures.append(f"SCROLL(H) {label}: scrollWidth={dims['sw']} > innerWidth={dims['iw']}")

            # document.scrollHeight only catches page-level scroll. .card has
            # overflow:hidden, so content that overflows THE CARD gets silently
            # clipped without ever triggering page scroll — check containment
            # explicitly so a clipped element (e.g. wrapped extras) is caught.
            clipped = page.evaluate(
                """() => {
                    const card = document.querySelector('.card').getBoundingClientRect();
                    const sel = '.secondary a, .cta, .chip, .back-link, .lang-toggle button';
                    const EPS = 1.0;
                    return Array.from(document.querySelectorAll(sel))
                        .map(el => { const r = el.getBoundingClientRect(); return {text: el.textContent.trim().slice(0,20), r}; })
                        .filter(({r}) => r.width > 0 && r.height > 0 &&
                            (r.top < card.top - EPS || r.bottom > card.bottom + EPS ||
                             r.left < card.left - EPS || r.right > card.right + EPS))
                        .map(({text, r}) => `${text} top=${r.top.toFixed(1)} bottom=${r.bottom.toFixed(1)} (card ${card.top.toFixed(1)}-${card.bottom.toFixed(1)})`);
                }"""
            )
            for c in clipped:
                failures.append(f"CLIPPED {label}: {c}")

            html_lang = page.evaluate("() => document.documentElement.lang")
            expected_lang = "pt-BR" if lang == "pt" else "en"
            if html_lang != expected_lang:
                failures.append(f"LANG {label}: html lang={html_lang!r}, expected {expected_lang!r}")

            pt_visible = page.locator('[data-i18n="pt"]').first.is_visible()
            en_visible = page.locator('[data-i18n="en"]').first.is_visible()
            if lang == "pt" and (not pt_visible or en_visible):
                failures.append(f"I18N {label}: pt content not exclusively visible")
            if lang == "en" and (not en_visible or pt_visible):
                failures.append(f"I18N {label}: en content not exclusively visible")

            for sel, expected in expected_hrefs.items():
                href = page.eval_on_selector(sel, "el => el && el.getAttribute('href')")
                if href != expected:
                    failures.append(f"HREF {label}: {sel} = {href!r}, expected {expected!r}")

            rel_info = page.evaluate(
                "() => Array.from(document.querySelectorAll('a[target=\"_blank\"]'))"
                ".map(a => ({href: a.getAttribute('href'), rel: a.getAttribute('rel')}))"
            )
            for a in rel_info:
                rel = a["rel"] or ""
                if "noopener" not in rel or "noreferrer" not in rel:
                    failures.append(f"REL {label}: {a['href']} missing noopener/noreferrer (rel={rel!r})")

            back_count = page.locator(".back-link").count()
            if expect["back_link"] and back_count == 0:
                failures.append(f"BACKLINK {label}: expected a back-link, found none")
            if not expect["back_link"] and back_count > 0:
                failures.append(f"BACKLINK {label}: unexpected back-link present")

            secondary_links = page.locator(".secondary a").count()
            expected_secondary = 2 + len(expect["extras"])
            if secondary_links != expected_secondary:
                failures.append(f"EXTRAS {label}: .secondary has {secondary_links} links, expected {expected_secondary}")

            ascii_state = page.evaluate(
                "() => { const pre = document.getElementById('portrait-ascii');"
                " const fb = document.getElementById('portrait-fallback');"
                " return {preHidden: pre.hidden, fbHidden: fb.hidden,"
                " preDisplay: getComputedStyle(pre).display, fbDisplay: getComputedStyle(fb).display}; }"
            )
            if expect["photo"]:
                if ascii_state["preHidden"] is not False or ascii_state["fbHidden"] is not True:
                    failures.append(f"ASCII {label}: expected photo active, got {ascii_state}")
                if ascii_state["preDisplay"] == "none" or ascii_state["fbDisplay"] != "none":
                    failures.append(f"ASCII-VISUAL {label}: {ascii_state}")
            else:
                if ascii_state["preHidden"] is not True or ascii_state["fbHidden"] is not False:
                    failures.append(f"ASCII {label}: expected fallback active, got {ascii_state}")
                if ascii_state["preDisplay"] != "none" or ascii_state["fbDisplay"] == "none":
                    failures.append(f"ASCII-VISUAL {label}: {ascii_state}")


def run_contrast_checks(page, base_url, failures, evidence):
    page.goto(f"{base_url}?lang=pt", wait_until="networkidle")
    selectors = [
        (".bio", False), (".role", False), (".location", False), (".chip", False),
        (".path", False), (".secondary a", False), (".cta-whatsapp", False),
        (".cta-linkedin", False), (".cta-vcf", False),
        (".lang-toggle button.active", False), ("h1", True),
    ]
    for sel, is_large_hint in selectors:
        info = page.evaluate(
            """(sel) => {
                const el = document.querySelector(sel);
                if (!el) return null;
                const cs = getComputedStyle(el);
                let bgEl = el, bg = getComputedStyle(bgEl).backgroundColor;
                while ((bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') && bgEl.parentElement) {
                    bgEl = bgEl.parentElement;
                    bg = getComputedStyle(bgEl).backgroundColor;
                }
                return {color: cs.color, bg, fontSize: parseFloat(cs.fontSize), fontWeight: cs.fontWeight};
            }""",
            sel,
        )
        if not info:
            failures.append(f"CONTRAST: selector {sel!r} not found")
            continue
        fg_hex, bg_hex = to_hex(info["color"]), to_hex(info["bg"])
        ratio = contrast_ratio(fg_hex, bg_hex)
        is_large = info["fontSize"] >= 24 or (info["fontSize"] >= 18.66 and int(info["fontWeight"]) >= 700)
        threshold = 3.0 if is_large else 4.5
        evidence.append(f"{sel}: fg={fg_hex} bg={bg_hex} ratio={ratio:.2f} threshold={threshold} {'PASS' if ratio >= threshold else 'FAIL'}")
        if ratio < threshold:
            failures.append(f"CONTRAST {sel}: ratio {ratio:.2f} < {threshold} (fg={fg_hex} bg={bg_hex})")


def run_keyboard_check(page, base_url, failures, evidence):
    page.goto(f"{base_url}?lang=pt", wait_until="networkidle")
    ids_seen = []
    for _ in range(8):
        page.keyboard.press("Tab")
        info = page.evaluate(
            "() => { const el = document.activeElement; if (!el || el === document.body) return null;"
            " return {tag: el.tagName, id: el.id}; }"
        )
        if info and info["id"]:
            ids_seen.append(info["id"])
    evidence.append(f"tab order ids: {ids_seen}")
    for required in ("btn-pt", "btn-en"):
        if required not in ids_seen:
            failures.append(f"TABORDER: expected to reach #{required} via Tab, got {ids_seen}")


def run_vcf_download_check(page, base_url, cfg, failures, evidence):
    page.goto(f"{base_url}?lang=pt", wait_until="networkidle")
    with page.expect_download() as dl_info:
        page.click(".cta-vcf")
    download = dl_info.value
    suggested = download.suggested_filename
    evidence.append(f"vcf download filename: {suggested}")
    if suggested != cfg["vcf_filename"]:
        failures.append(f"VCF-DOWNLOAD: filename {suggested!r}, expected {cfg['vcf_filename']!r}")


def validate_vcf_file(project, cfg, failures, evidence):
    vcf_path = project / "contacts" / cfg["vcf_filename"]
    if not vcf_path.exists():
        failures.append(f"VCF-FILE: {vcf_path} não existe")
        return
    data = vcf_path.read_bytes()
    ok, msg = validate_vcf(data)
    evidence.append(f"vcf validate: {msg}")
    if ok is False:
        failures.append(f"VCF-VALIDATE: {msg}")
    lines = data.split(b"\r\n")
    if lines and lines[-1] == b"":
        lines.pop()
    over = [l for l in lines if len(l) > 75]
    if over:
        failures.append(f"VCF-FOLD: {len(over)} linha(s) acima de 75 octetos")
    if b"\n" in data.replace(b"\r\n", b""):
        failures.append("VCF-CRLF: encontrada quebra de linha sem CR")


def start_prefixed_server(directory, prefix):
    """Serves `directory` as if it lived under `prefix` (e.g. "/cartaonfc"),
    the way a GitHub Pages *project* site is mounted — proves relative paths
    in the page resolve correctly regardless of the path the site is served
    under, without needing a real GitHub Pages deploy to check it."""
    import http.server
    import socketserver
    import threading

    class PrefixHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(directory), **kw)

        def translate_path(self, path):
            if path.startswith(prefix):
                path = path[len(prefix):] or "/"
            return super().translate_path(path)

        def log_message(self, *a):
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", 0), PrefixHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, port


def run_scenario(name, playwright, prefix=None):
    print(f"\n=== Cenário: {name} ===")
    tmp_dir, project, cfg, expect, sync_ok, sync_output = prepare_scenario(name)
    failures = []
    console_issues = []
    external_hosts = []
    evidence = []
    shot_dir = OUT_DIR / name

    if not sync_ok:
        failures.append(f"SYNC: tools/sync.py falhou:\n{sync_output}")

    server = None
    httpd = None
    try:
        if prefix:
            httpd, port = start_prefixed_server(project, prefix)
            base_url = f"http://127.0.0.1:{port}{prefix}/contacts/"
        else:
            port = free_port()
            server = subprocess.Popen(
                [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                cwd=project, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            base_url = f"http://127.0.0.1:{port}/contacts/"

        if not wait_for_server(port):
            failures.append("SERVER: não respondeu a tempo")
        else:
            browser = playwright.chromium.launch()
            try:
                context = browser.new_context(accept_downloads=True)
                page = context.new_page()
                run_battery(page, base_url, cfg, expect, failures, console_issues, external_hosts, shot_dir=shot_dir)
                run_contrast_checks(page, base_url, failures, evidence)
                run_keyboard_check(page, base_url, failures, evidence)
                run_vcf_download_check(page, base_url, cfg, failures, evidence)
                context.close()
            finally:
                browser.close()
            validate_vcf_file(project, cfg, failures, evidence)
    finally:
        if server:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
        if httpd:
            httpd.shutdown()
            httpd.server_close()
        shutil.rmtree(tmp_dir, ignore_errors=True)

    passed = not failures and not console_issues and not external_hosts
    print(f"  sync.py: {'OK' if sync_ok else 'FALHOU'}")
    print(f"  console issues: {len(console_issues)}")
    for c in console_issues[:10]:
        print(f"    - {c}")
    print(f"  external requests: {len(external_hosts)}")
    for e in external_hosts[:10]:
        print(f"    - {e}")
    for ev in evidence:
        print(f"  {ev}")
    print(f"  failures: {len(failures)}")
    for f in failures:
        print(f"    FAIL: {f}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Playwright (Python) não está instalado. Rode:\n"
            "  pip install playwright && python3 -m playwright install chromium",
            file=sys.stderr,
        )
        return 1

    shutil.rmtree(OUT_DIR, ignore_errors=True)

    scenario_specs = [
        ("estado-atual", None),
        ("foto-sintetica", None),
        ("portfolio-site-extras", None),
        ("subpath", "/cartaonfc"),
    ]
    results = {}
    with sync_playwright() as p:
        for name, prefix in scenario_specs:
            results[name] = run_scenario(name, p, prefix=prefix)

    print("\n=== RESUMO ===")
    for name, ok in results.items():
        print(f"{name}: {'PASS' if ok else 'FAIL'}")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
