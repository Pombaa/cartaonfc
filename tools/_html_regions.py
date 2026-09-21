"""Builds the exact HTML/CSS snippets that go inside each sync:* marker in
contacts/index.html, from card.config.json. Dev-only.

Every build_* function returns the text that goes *between* the marker
comments, including the leading/trailing newline and the indentation that
matches the end-marker line, so sync.py can drop it straight into the file.
"""

from _cardlib import (
    esc, esc_attr, js_encode_uri_component, short_role, page_url,
    resolve_og_image_url, derive_description,
)

WA_ARROW_SVG = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M7 17 17 7M10 7h7v7"/></svg>'
)
VCF_ICON_SVG = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M9 12.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7ZM3 20.5c0-3.6 2.7-6 6-6s6 2.4 6 6M18 8v6M21 11h-6"/></svg>'
)
GITHUB_ICON_SVG = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="m8 6-5 6 5 6M16 6l5 6-5 6"/></svg>'
)
MAIL_ICON_SVG = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6.5 12 13 20.5 6.5"/></svg>'
)
BACK_ICON_SVG = (
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M17 5 7 12l10 7"/></svg>'
)
EXTRA_ICON_SVG = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M7 17 17 7M10 7h7v7"/></svg>'
)


def build_title(cfg):
    title = f'{cfg["display_name"]} · {short_role(cfg)}'
    return f"\n<title>{esc(title)}</title>\n"


def build_description(cfg):
    text = cfg.get("meta_description") or derive_description(cfg)
    return f'\n<meta name="description" content="{esc_attr(text)}">\n'


def build_og(cfg):
    title = f'{cfg["display_name"]} · {short_role(cfg)}'
    description = derive_description(cfg)

    lines = [
        f'<meta property="og:title" content="{esc_attr(title)}">',
        f'<meta property="og:description" content="{esc_attr(description)}">',
        '<meta property="og:type" content="profile">',
    ]

    url = page_url(cfg)
    if url:
        lines.append(f'<meta property="og:url" content="{esc_attr(url)}">')
        lines.append(f'<link rel="canonical" href="{esc_attr(url)}">')

    img = resolve_og_image_url(cfg)
    if img:
        lines.append(f'<meta property="og:image" content="{esc_attr(img)}">')
        lines.append('<meta name="twitter:card" content="summary_large_image">')

    missing = []
    if not url:
        missing.append("site_url (og:url, canonical)")
    if not img:
        missing.append("og_image (og:image, twitter:card)")
    if missing:
        lines.append(f'<!-- faltando em card.config.json: {", ".join(missing)} — rode tools/sync.py depois de preenchê-los. -->')

    return "\n" + "\n".join(lines) + "\n"


def build_theme(cfg):
    accent = cfg["accent"]
    from _cardlib import derive_accent_soft
    accent_soft = cfg.get("accent_soft") or derive_accent_soft(accent)
    return f"\n    --accent: {accent};\n    --accent-soft: {accent_soft};\n    "


def build_topbar(cfg):
    handle = f'<span class="path">{esc(cfg["handle"])}</span>'
    if cfg.get("portfolio_url"):
        back = (
            f'<a class="back-link" href="{esc_attr(cfg["portfolio_url"])}">\n'
            f"      {BACK_ICON_SVG}\n"
            '      <span data-i18n="pt">portfólio</span><span data-i18n="en" hidden>portfolio</span>\n'
            "    </a>\n"
            f"    {handle}"
        )
        return f"\n    {back}\n    "
    return f"\n    {handle}\n    "


def build_portrait(cfg):
    initials = esc(cfg["initials"])
    name = cfg["display_name"]
    ascii_pt = esc_attr(f"Retrato em arte ASCII de {name}")
    ascii_en = esc_attr(f"ASCII art portrait of {name}")
    fallback_pt = esc_attr(f"Iniciais {cfg['initials']} — retrato de {name}, ainda sem foto")
    fallback_en = esc_attr(f"Initials {cfg['initials']} — portrait of {name}, no photo yet")
    return (
        '\n  <div class="portrait" id="portrait">\n'
        '    <div class="portrait-slot" id="portrait-slot">\n'
        '      <pre class="portrait-ascii portrait-ascii--blur" id="portrait-ascii-blur"\n'
        '        aria-hidden="true" hidden></pre>\n'
        '      <pre class="portrait-ascii" id="portrait-ascii" role="img" hidden\n'
        f'        data-aria-pt="{ascii_pt}"\n'
        f'        data-aria-en="{ascii_en}"></pre>\n'
        '      <div class="portrait-fallback" id="portrait-fallback" role="img"\n'
        f'        aria-label="{fallback_pt}"\n'
        f'        data-aria-pt="{fallback_pt}"\n'
        f'        data-aria-en="{fallback_en}">\n'
        f'        <span class="portrait-initials">{initials}</span>\n'
        "      </div>\n"
        "    </div>\n"
        '    <div class="name-block">\n'
        f"      <h1>{esc(name)}</h1>\n"
        '      <p class="role">\n'
        f'        <span data-i18n="pt">{esc(cfg["role"]["pt"])}</span>'
        f'<span data-i18n="en" hidden>{esc(cfg["role"]["en"])}</span>\n'
        "      </p>\n"
        '      <p class="location">\n'
        f'        <span data-i18n="pt">{esc(cfg["location"]["pt"])}</span>'
        f'<span data-i18n="en" hidden>{esc(cfg["location"]["en"])}</span>\n'
        "      </p>\n"
        "    </div>\n"
        "  </div>\n"
        "  "
    )


def build_identity(cfg):
    # Nome/cargo/local ficam no overlay .name-block dentro de .portrait
    # (mesmo padrão do cartão de referência). Marcador sync permanece vazio.
    return "\n    "



def build_bio(cfg):
    return (
        '\n    <p class="bio">\n'
        f'      <span data-i18n="pt">{esc(cfg["bio"]["pt"])}</span>'
        f'<span data-i18n="en" hidden>{esc(cfg["bio"]["en"])}</span>\n'
        "    </p>\n"
        "    "
    )


def build_chips(cfg):
    chip_lines = "\n".join(f'      <span class="chip">{esc(c)}</span>' for c in cfg["chips"])
    return f'\n    <div class="chips">\n{chip_lines}\n    </div>\n    '


def build_ctas(cfg):
    wa_href = f'https://wa.me/{cfg["wa_number"]}?text={js_encode_uri_component(cfg["wa_message"])}'
    linkedin_href = esc_attr(cfg["linkedin"])
    vcf_filename = esc_attr(cfg["vcf_filename"])
    labels = cfg["labels"]
    return (
        '\n    <div class="ctas">\n'
        '      <div class="cta-row">\n'
        f'        <a class="cta cta-whatsapp" href="{esc_attr(wa_href)}" target="_blank" rel="noopener noreferrer">\n'
        f"          {esc(labels['whatsapp'])}\n"
        f"          {WA_ARROW_SVG}\n"
        "        </a>\n"
        f'        <a class="cta cta-linkedin" href="{linkedin_href}" target="_blank" rel="noopener noreferrer">\n'
        f"          {esc(labels['linkedin'])}\n"
        f"          {WA_ARROW_SVG}\n"
        "        </a>\n"
        "      </div>\n"
        f'      <a class="cta cta-vcf" href="{vcf_filename}" download="{vcf_filename}" type="text/vcard">\n'
        f'        <span data-i18n="pt">{esc(labels["add_contact"]["pt"])}</span>'
        f'<span data-i18n="en" hidden>{esc(labels["add_contact"]["en"])}</span>\n'
        f"        {VCF_ICON_SVG}\n"
        "      </a>\n"
        "    </div>\n"
        "    "
    )


def _extra_link_html(extra):
    url = extra["url"]
    label = esc(extra["label"])
    is_external = not (url.startswith("mailto:") or url.startswith("tel:"))
    attrs = ' target="_blank" rel="noopener noreferrer"' if is_external else ""
    return (
        f'      <a href="{esc_attr(url)}"{attrs}>\n'
        f"        {EXTRA_ICON_SVG}\n"
        f"        {label}\n"
        "      </a>"
    )


def build_secondary(cfg):
    labels = cfg["labels"]
    links = [
        (
            '      <a href="' + esc_attr(cfg["github"]) + '" target="_blank" rel="noopener noreferrer">\n'
            f"        {GITHUB_ICON_SVG}\n"
            f"        {esc(labels['github'])}\n"
            "      </a>"
        ),
        (
            '      <a href="mailto:' + esc_attr(cfg["email"]) + '">\n'
            f"        {MAIL_ICON_SVG}\n"
            f'        <span data-i18n="pt">{esc(labels["email"]["pt"])}</span>'
            f'<span data-i18n="en" hidden>{esc(labels["email"]["en"])}</span>\n'
            "      </a>"
        ),
    ]
    links.extend(_extra_link_html(e) for e in cfg.get("extras", []))
    body = "\n".join(links)
    return f'\n    <div class="secondary">\n{body}\n    </div>\n    '


def build_ascii_script(photo_active):
    tag = (
        '<script src="../ascii-photo.js"></script>'
        if photo_active
        else '<!-- <script src="../ascii-photo.js"></script> -->'
    )
    return (
        "\n"
        '<!-- tools/sync.py descomenta esta linha sozinho quando "photo" existe em card.config.json. -->\n'
        f"{tag}\n"
    )
