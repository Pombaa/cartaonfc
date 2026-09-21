"""Shared ASCII-art generation core, used by gen-ascii.py (standalone CLI)
and sync.py (config-driven). Dev-only, not part of the deployed site.
"""

try:
    from PIL import Image, ImageOps, ImageEnhance, ImageStat
except ImportError as exc:  # pragma: no cover
    raise ImportError("Pillow is required: pip install Pillow") from exc

# Sparsest -> densest. Kept short and legible at small font sizes.
RAMP = " .:-=+*#%@"

# Character cells in monospace fonts are roughly twice as tall as they are
# wide, so we sample fewer rows than a naive width-based scale would give,
# to avoid vertically stretching the portrait.
CHAR_ASPECT = 0.5

TARGET_PORTRAIT_RATIO = 3 / 4  # width / height, matches .portrait-slot in CSS
PORTRAIT_RATIO_TOLERANCE = 0.12

LOW_CONTRAST_STDDEV = 20.0
BUSY_BACKGROUND_STDDEV = 25.0
BORDER_FRACTION = 0.06


def _apply_manual_crop(img, crop):
    w, h = img.size
    x0 = max(0.0, min(1.0, crop.get("x", 0.0)))
    y0 = max(0.0, min(1.0, crop.get("y", 0.0)))
    cw = max(0.01, min(1.0 - x0, crop.get("w", 1.0)))
    ch = max(0.01, min(1.0 - y0, crop.get("h", 1.0)))
    box = (round(x0 * w), round(y0 * h), round((x0 + cw) * w), round((y0 + ch) * h))
    return img.crop(box)


def _auto_crop_to_portrait(img, target_ratio=TARGET_PORTRAIT_RATIO):
    w, h = img.size
    ratio = w / h
    if abs(ratio - target_ratio) <= PORTRAIT_RATIO_TOLERANCE:
        return img, False
    if ratio > target_ratio:
        # too wide: crop sides
        new_w = round(h * target_ratio)
        x0 = (w - new_w) // 2
        box = (x0, 0, x0 + new_w, h)
    else:
        # too tall: crop top/bottom (bias slightly upward, faces sit high)
        new_h = round(w / target_ratio)
        y0 = max(0, (h - new_h) // 3)
        box = (0, y0, w, y0 + new_h)
    return img.crop(box), True


def quality_warnings(gray_img):
    warnings = []
    stddev = ImageStat.Stat(gray_img).stddev[0]
    if stddev < LOW_CONTRAST_STDDEV:
        warnings.append(
            "baixo contraste detectado na foto (desvio padrão de luminância "
            f"{stddev:.1f} < {LOW_CONTRAST_STDDEV:.0f}) — considere uma foto com "
            "mais contraste entre sujeito e fundo."
        )

    w, h = gray_img.size
    bw, bh = max(1, round(w * BORDER_FRACTION)), max(1, round(h * BORDER_FRACTION))
    border_regions = [
        gray_img.crop((0, 0, w, bh)),
        gray_img.crop((0, h - bh, w, h)),
        gray_img.crop((0, 0, bw, h)),
        gray_img.crop((w - bw, 0, w, h)),
    ]
    border_stddevs = [ImageStat.Stat(r).stddev[0] for r in border_regions]
    if max(border_stddevs) > BUSY_BACKGROUND_STDDEV:
        warnings.append(
            "fundo pode não estar liso (muita variação perto das bordas) — "
            "considere recortar mais apertado (ascii.crop) ou usar um fundo mais uniforme."
        )
    return warnings


def image_to_ascii(image_path, cols=100, contrast=1.0, gamma=1.0, invert=False, crop=None):
    """Returns (ascii_text, warnings)."""
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    warnings = []
    if crop:
        img = _apply_manual_crop(img, crop)
    else:
        img, was_cropped = _auto_crop_to_portrait(img)
        if was_cropped:
            warnings.append(
                "a foto não estava em proporção retrato (~3:4); recorte automático "
                "central foi aplicado. Para controlar manualmente, defina ascii.crop "
                "no card.config.json."
            )

    gray = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    warnings.extend(quality_warnings(gray))

    if contrast != 1.0:
        gray = ImageEnhance.Contrast(gray).enhance(contrast)

    src_w, src_h = gray.size
    rows = max(1, round((src_h / src_w) * cols * CHAR_ASPECT))
    small = gray.resize((cols, rows), Image.LANCZOS)

    pixels = small.load()
    ramp_last = len(RAMP) - 1
    inv_gamma = 1.0 / gamma if gamma else 1.0
    lines = []
    for y in range(rows):
        row_chars = []
        for x in range(cols):
            luminance = pixels[x, y] / 255.0  # 0 (dark) .. 1 (bright)
            # Light-on-dark theme: bright pixels -> dense glyphs (more
            # accent-colored "ink" visible), dark pixels -> sparse glyphs
            # (background shows through). This is the inverse of the
            # classic dark-ink-on-paper ASCII art mapping. `invert` flips
            # it back to the classic direction when set.
            adjusted = luminance ** inv_gamma
            idx = round(adjusted * ramp_last)
            if invert:
                idx = ramp_last - idx
            row_chars.append(RAMP[idx])
        lines.append("".join(row_chars).rstrip())

    ascii_text = "\n".join(lines)
    if not ascii_text.strip():
        warnings.append("o ASCII gerado ficou vazio — verifique a imagem de origem.")
    return ascii_text, warnings
