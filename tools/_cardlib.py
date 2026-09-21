"""Shared config/HTML/vCard/color helpers for tools/sync.py and tools/verify.py.

Dev-only, not part of the deployed site. Keeping this logic in one module
means sync.py (which writes contacts/index.html and the .vcf) and any other
dev tool agree on exactly how card.config.json turns into markup.
"""

import json
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "card.config.json"
INDEX_PATH = ROOT / "contacts" / "index.html"
ASCII_ART_JS = ROOT / "ascii-art.js"
ASCII_PHOTO_JS = ROOT / "ascii-photo.js"

MAX_EXTRAS = 4
BG_HEX = "#0b0710"  # matches --bg in contacts/index.html; not config-managed.


class SyncError(Exception):
    """Raised for config/template problems that should stop sync.py cleanly."""


# --------------------------------------------------------------------------
# Config loading
# --------------------------------------------------------------------------

_REQUIRED_KEYS = [
    "name", "display_name", "initials", "handle", "role", "location", "bio",
    "chips", "wa_number", "wa_message", "linkedin", "github", "email",
    "phone", "vcf_filename", "accent",
]

_ASCII_DEFAULTS = {"cols": 100, "contrast": 1.0, "gamma": 1.0, "invert": False, "crop": None}

_LABEL_DEFAULTS = {
    "whatsapp": "WhatsApp",
    "linkedin": "LinkedIn",
    "add_contact": {"pt": "Adicionar contato", "en": "Add contact"},
    "github": "GitHub",
    "email": {"pt": "E-mail", "en": "Email"},
}


def load_config(path=None):
    path = Path(path) if path else CONFIG_PATH
    if not path.exists():
        raise SyncError(f"config não encontrado: {path}")
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SyncError(f"card.config.json inválido: {exc}") from exc

    missing = [k for k in _REQUIRED_KEYS if k not in cfg]
    if missing:
        raise SyncError(f"campos obrigatórios ausentes em card.config.json: {', '.join(missing)}")

    for field in ("role", "location", "bio"):
        val = cfg[field]
        if not isinstance(val, dict) or "pt" not in val or "en" not in val:
            raise SyncError(f'campo "{field}" precisa ter as chaves "pt" e "en"')

    if not isinstance(cfg["chips"], list):
        raise SyncError('campo "chips" precisa ser uma lista')

    cfg.setdefault("portfolio_url", None)
    cfg.setdefault("site_url", None)
    cfg.setdefault("og_image", None)
    cfg.setdefault("photo", None)
    cfg.setdefault("accent_soft", None)
    cfg.setdefault("extras", [])
    cfg.setdefault("meta_description", None)
    cfg.setdefault("vcf_note", None)

    if cfg["meta_description"] is not None and not isinstance(cfg["meta_description"], str):
        raise SyncError('campo "meta_description" precisa ser string ou null')
    if cfg["vcf_note"] is not None and not isinstance(cfg["vcf_note"], str):
        raise SyncError('campo "vcf_note" precisa ser string ou null')

    labels = cfg.get("labels") or {}
    if not isinstance(labels, dict):
        raise SyncError('campo "labels" precisa ser um objeto')
    merged_labels = {}
    for key, default in _LABEL_DEFAULTS.items():
        value = labels.get(key, default)
        if isinstance(default, dict):
            if not isinstance(value, dict) or "pt" not in value or "en" not in value:
                raise SyncError(f'campo "labels.{key}" precisa ter as chaves "pt" e "en"')
        elif not isinstance(value, str):
            raise SyncError(f'campo "labels.{key}" precisa ser uma string')
        merged_labels[key] = value
    cfg["labels"] = merged_labels

    ascii_cfg = dict(_ASCII_DEFAULTS)
    ascii_cfg.update(cfg.get("ascii") or {})
    cfg["ascii"] = ascii_cfg

    extras = cfg["extras"]
    if not isinstance(extras, list):
        raise SyncError('campo "extras" precisa ser uma lista de {"label": ..., "url": ...}')
    if len(extras) > MAX_EXTRAS:
        raise SyncError(
            f'"extras" tem {len(extras)} itens, o máximo suportado sem quebrar o layout '
            f"(sem scroll) é {MAX_EXTRAS}. Remova algum ou agrupe links relacionados."
        )
    for e in extras:
        if not isinstance(e, dict) or "label" not in e or "url" not in e:
            raise SyncError('cada item de "extras" precisa ter "label" e "url"')

    return cfg


# --------------------------------------------------------------------------
# Text/attribute escaping
# --------------------------------------------------------------------------

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def esc_attr(s):
    return esc(s).replace('"', "&quot;")


def js_encode_uri_component(s):
    """Matches JavaScript's encodeURIComponent exactly (same unreserved set)."""
    return urllib.parse.quote(s, safe="!*'()")


# --------------------------------------------------------------------------
# Color / contrast
# --------------------------------------------------------------------------

def _hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def relative_luminance(hex_color):
    r, g, b = (c / 255 for c in _hex_to_rgb(hex_color))

    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = ch(r), ch(g), ch(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(hex1, hex2):
    l1, l2 = relative_luminance(hex1), relative_luminance(hex2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def mix_hex(hex_a, hex_b, t):
    """t=0 -> hex_b, t=1 -> hex_a."""
    a, b = _hex_to_rgb(hex_a), _hex_to_rgb(hex_b)
    mixed = tuple(bc + (ac - bc) * t for ac, bc in zip(a, b))
    return _rgb_to_hex(mixed)


def derive_accent_soft(accent_hex, bg_hex=BG_HEX):
    return mix_hex(accent_hex, bg_hex, 0.17)


def contrast_warnings(cfg):
    accent = cfg["accent"]
    accent_soft = cfg.get("accent_soft") or derive_accent_soft(accent)
    warnings = []
    checks = [
        (f"--accent {accent} sobre --bg {BG_HEX}", contrast_ratio(accent, BG_HEX), 4.5),
        (f"--accent {accent} sobre --accent-soft {accent_soft} (botão WhatsApp)", contrast_ratio(accent, accent_soft), 4.5),
        (f"--bg {BG_HEX} sobre --accent {accent} (texto do botão \"Adicionar contato\")", contrast_ratio(BG_HEX, accent), 4.5),
    ]
    for label, ratio, threshold in checks:
        if ratio < threshold:
            warnings.append(f"contraste insuficiente: {label} = {ratio:.2f}:1 (mínimo AA {threshold}:1)")
    return warnings


# --------------------------------------------------------------------------
# HTML marker replacement
# --------------------------------------------------------------------------

def _marker_tags(name, style):
    if style == "css":
        return f"/* sync:start:{name} */", f"/* sync:end:{name} */"
    return f"<!-- sync:start:{name} -->", f"<!-- sync:end:{name} -->"


def replace_marker(text, name, new_inner, style="html"):
    start_tag, end_tag = _marker_tags(name, style)
    pattern = re.compile(re.escape(start_tag) + r"(.*?)" + re.escape(end_tag), re.DOTALL)
    if not pattern.search(text):
        raise SyncError(f"marcador sync:start:{name} não encontrado em {INDEX_PATH}")
    full = start_tag + new_inner + end_tag
    return pattern.sub(lambda _m: full, text, count=1)


def get_marker_inner(text, name, style="html"):
    start_tag, end_tag = _marker_tags(name, style)
    pattern = re.compile(re.escape(start_tag) + r"(.*?)" + re.escape(end_tag), re.DOTALL)
    m = pattern.search(text)
    return m.group(1) if m else None


# --------------------------------------------------------------------------
# Derived text helpers
# --------------------------------------------------------------------------

def short_role(cfg):
    role_pt = cfg["role"]["pt"]
    return role_pt.split(" · ", 1)[0].strip() if " · " in role_pt else role_pt


def derive_description(cfg):
    chips_line = ", ".join(cfg["chips"])
    return f"Full Stack: {chips_line}." if chips_line else "Full Stack."


def resolve_og_image_url(cfg):
    val = cfg.get("og_image")
    if not val:
        return None
    if val.startswith("http://") or val.startswith("https://"):
        return val
    if cfg.get("site_url"):
        return cfg["site_url"].rstrip("/") + "/contacts/" + val.lstrip("/")
    return val


def page_url(cfg):
    if not cfg.get("site_url"):
        return None
    return cfg["site_url"].rstrip("/") + "/contacts/"


def is_external_scheme(url):
    return not (url.startswith("mailto:") or url.startswith("tel:"))
