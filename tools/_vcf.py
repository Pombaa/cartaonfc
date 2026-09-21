"""vCard 3.0 builder, driven by card.config.json. Dev-only."""

from _cardlib import short_role

_CONNECTORS = {"de", "da", "das", "dos", "do"}


def split_name(full_name, given_override=None, family_override=None):
    if given_override and family_override:
        return given_override, family_override
    tokens = full_name.split()
    if len(tokens) <= 1:
        return "", full_name
    family_start = len(tokens) - 1
    for i in range(1, len(tokens)):
        if tokens[i].lower() in _CONNECTORS:
            family_start = max(1, i - 1)
            break
    given = " ".join(tokens[:family_start])
    family = " ".join(tokens[family_start:])
    return given, family


def escape_value(v):
    return (
        str(v)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def fold_line(line, limit=75):
    b = line.encode("utf-8")
    if len(b) <= limit:
        return line
    parts = []
    start = 0
    first = True
    while start < len(b):
        lim = limit if first else limit - 1  # continuation lines carry a leading space (1 octet)
        end = min(start + lim, len(b))
        while end < len(b) and (b[end] & 0xC0) == 0x80:  # don't split a UTF-8 sequence
            end -= 1
        chunk = b[start:end].decode("utf-8")
        parts.append(chunk if first else " " + chunk)
        start = end
        first = False
    return "\r\n".join(parts)


def _vcf_type_token(label):
    token = "".join(ch for ch in str(label) if ch.isalnum())
    return token or "Link"


def _location_parts(location_pt):
    parts = [p.strip() for p in location_pt.split(",")]
    city = parts[0] if len(parts) > 0 else ""
    region = parts[1] if len(parts) > 1 else ""
    country = parts[2] if len(parts) > 2 else ""
    return city, region, country


def build_vcf_bytes(cfg):
    given, family = split_name(cfg["name"], cfg.get("name_given"), cfg.get("name_family"))
    city, region, country = _location_parts(cfg["location"]["pt"])
    role = short_role(cfg)

    fields = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        "N:" + escape_value(family) + ";" + escape_value(given) + ";;;",
        "FN:" + escape_value(cfg["name"]),
        "TITLE:" + escape_value(role),
        "TEL;TYPE=CELL,VOICE:" + cfg["phone"],
        "EMAIL;TYPE=INTERNET:" + cfg["email"],
        "URL;TYPE=LinkedIn:" + cfg["linkedin"],
        "URL;TYPE=GitHub:" + cfg["github"],
        "ADR;TYPE=HOME:;;" + escape_value(city) + ";" + escape_value(region) + ";;" + escape_value(country),
    ]

    if cfg.get("portfolio_url"):
        fields.append("URL;TYPE=Portfolio:" + cfg["portfolio_url"])

    for extra in cfg.get("extras", []):
        url = extra["url"]
        token = _vcf_type_token(extra["label"])
        if url.startswith("mailto:"):
            fields.append(f"EMAIL;TYPE=INTERNET,{token}:{url[len('mailto:'):]}")
        elif url.startswith("tel:"):
            fields.append(f"TEL;TYPE=VOICE,{token}:{url[len('tel:'):]}")
        else:
            fields.append(f"URL;TYPE={token}:{url}")

    note = cfg.get("vcf_note") or (f"{role} · " + ", ".join(cfg["chips"]))
    fields.append("NOTE:" + escape_value(note))
    fields.append("END:VCARD")

    lines = [fold_line(f) for f in fields]
    content = "\r\n".join(lines) + "\r\n"
    return content.encode("utf-8")


def validate_vcf(vcf_bytes):
    """Best-effort parse check with vobject, if installed. Returns (ok, message)."""
    try:
        import vobject
    except ImportError:
        return None, "vobject não instalado — pulei a validação (pip install vobject para habilitar)."
    try:
        card = vobject.readOne(vcf_bytes.decode("utf-8"))
        _ = card.fn.value  # touch a required field to force parsing
        return True, "vCard parseado com sucesso pela lib vobject."
    except Exception as exc:  # noqa: BLE001 - want a friendly message for any parse failure
        return False, f"vCard NÃO parseou com vobject: {exc}"
