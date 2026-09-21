#!/usr/bin/env python3
"""Folha A4 de adesivos NFC 85,5 × 54 mm (CR80).

Gera print/nfc-adesivo.pdf — imprimir em 100% em papel adesivo.
Frente e verso iguais; QR e NFC apontam para o mesmo URL.

    .venv/bin/python tools/gen-sticker.py
"""

from io import BytesIO
from pathlib import Path

import segno
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "print"
OUT_PDF = OUT_DIR / "nfc-adesivo.pdf"
OUT_JOAO = OUT_DIR / "nfc-adesivo-joao.pdf"
OUT_LOTE = OUT_DIR / "nfc-adesivos-lote.pdf"
ORIG_LOTE = OUT_DIR / "nfc-adesivos-lote-original.pdf"

CARD_W = 85.5 * mm
CARD_H = 54.0 * mm

URL = "https://joaovitorferreira.com.br/contato"
HANDLE = "~/pomba"
NAME = "João V. Ferreira"
ROLE = "Full-Stack · cartão de contato"
DOMAIN = "joaovitorferreira.com.br"
PATH = "/contato/"
LABEL = "JOÃO"

BG = HexColor("#0b0710")
ACCENT = HexColor("#a875ff")
TEXT = HexColor("#f2eef9")
MUTED = HexColor("#9c8fb8")
DIM = HexColor("#8f83ab")
CROP = Color(0.15, 0.15, 0.15)

FONT_REG = "/usr/share/fonts/TTF/JetBrainsMono-Regular.ttf"
FONT_MED = "/usr/share/fonts/TTF/JetBrainsMono-Medium.ttf"
FONT_BOLD = "/usr/share/fonts/TTF/JetBrainsMono-Bold.ttf"


def register_fonts():
    pdfmetrics.registerFont(TTFont("JB", FONT_REG))
    pdfmetrics.registerFont(TTFont("JB-Med", FONT_MED))
    pdfmetrics.registerFont(TTFont("JB-Bold", FONT_BOLD))


def qr_image():
    buf = BytesIO()
    segno.make(URL, error="m").save(
        buf, kind="png", scale=16, border=2, dark="#0b0710", light="#ffffff"
    )
    buf.seek(0)
    return ImageReader(buf)


def crop_marks(c, x, y):
    tick, gap = 4.2 * mm, 1.6 * mm
    c.setStrokeColor(CROP)
    c.setLineWidth(0.35)
    c.setLineCap(0)
    corners = (
        (x, y + CARD_H, -1, 1),
        (x + CARD_W, y + CARD_H, 1, 1),
        (x, y, -1, -1),
        (x + CARD_W, y, 1, -1),
    )
    for cx, cy, dx, dy in corners:
        c.line(cx + dx * gap, cy, cx + dx * (gap + tick), cy)
        c.line(cx, cy + dy * gap, cx, cy + dy * (gap + tick))


def draw_card(c, x, y, qr):
    c.setFillColor(BG)
    c.rect(x, y, CARD_W, CARD_H, stroke=0, fill=1)

    bar = 2.1 * mm
    c.setFillColor(ACCENT)
    c.rect(x, y + CARD_H - bar, CARD_W, bar, stroke=0, fill=1)

    pad = 5.4 * mm
    qr_pad = 32.0 * mm
    qr_box = 28.4 * mm
    qr_x = x + CARD_W - pad - qr_pad
    qr_y = y + (CARD_H - bar - qr_pad) / 2

    c.setFillColor(white)
    c.roundRect(qr_x, qr_y, qr_pad, qr_pad, 1.1 * mm, stroke=0, fill=1)
    inset = (qr_pad - qr_box) / 2
    c.drawImage(
        qr, qr_x + inset, qr_y + inset, qr_box, qr_box, mask="auto", preserveAspectRatio=True
    )

    left = x + pad
    text_max = qr_x - left - 3.2 * mm
    top = y + CARD_H - bar - 5.2 * mm

    def fit(font, size, text, min_size=5.2):
        while size > min_size and c.stringWidth(text, font, size) > text_max:
            size -= 0.2
        return size

    c.setFillColor(ACCENT)
    c.setFont("JB-Med", 7.4)
    c.drawString(left, top - 7.4, HANDLE)

    name_size = fit("JB-Bold", 11.0, NAME)
    c.setFillColor(TEXT)
    c.setFont("JB-Bold", name_size)
    c.drawString(left, top - 7.4 - 5.2 * mm, NAME)

    role_size = fit("JB", 6.0, ROLE)
    c.setFillColor(MUTED)
    c.setFont("JB", role_size)
    c.drawString(left, top - 7.4 - 8.6 * mm, ROLE)

    cap_y = y + pad + 6.6 * mm
    c.setFillColor(TEXT)
    c.setFont("JB-Med", 6.4)
    c.drawString(left, cap_y, "Aponte a câmera aqui")
    c.setFillColor(DIM)
    c.setFont("JB", 5.5)
    c.drawString(left, cap_y - 3.3 * mm, DOMAIN)
    c.drawString(left, cap_y - 6.0 * mm, PATH)


def draw_label(c, x, y, face):
    c.setFillColor(ACCENT)
    c.setFont("JB-Med", 7.2)
    c.drawString(x, y, f"{LABEL}   ·   {face}")


def build():
    register_fonts()
    qr = qr_image()
    OUT_DIR.mkdir(exist_ok=True)

    c = canvas.Canvas(str(OUT_PDF), pagesize=A4)
    c.setTitle("Adesivo NFC — João V. Ferreira")
    c.setAuthor("João V. Ferreira")
    page_w, page_h = A4

    gap_x = 12.0 * mm
    origin_x = (page_w - 2 * CARD_W - gap_x) / 2
    row_pitch = CARD_H + 16.0 * mm
    first_bottom = page_h - 38.0 * mm - CARD_H

    c.setFillColor(HexColor("#1a1a1a"))
    c.setFont("JB-Med", 9)
    title = "Imprimir em tamanho real (100%) em papel adesivo. Recortar nas marcas."
    c.drawCentredString(page_w / 2, page_h - 16 * mm, title)
    c.setFont("JB", 7.5)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(
        page_w / 2,
        page_h - 21.5 * mm,
        "Cartão NFC  ·  85,5 × 54 mm  ·  duas faces iguais (frente e verso).",
    )

    faces = ("FRENTE", "VERSO")
    for row in range(3):
        y = first_bottom - row * row_pitch
        for col, face in enumerate(faces):
            x = origin_x + col * (CARD_W + gap_x)
            crop_marks(c, x, y)
            draw_label(c, x, y + CARD_H + 3.4 * mm, face)
            draw_card(c, x, y, qr)

    c.setFillColor(HexColor("#888888"))
    c.setFont("JB", 7.4)
    c.drawCentredString(
        page_w / 2,
        16 * mm,
        "Cola uma face de cada lado do cartão NFC. QR e NFC levam ao mesmo link.",
    )

    c.save()
    OUT_JOAO.write_bytes(OUT_PDF.read_bytes())
    print(f"[ok] {OUT_PDF.relative_to(ROOT)}")
    print(f"[ok] {OUT_JOAO.relative_to(ROOT)}")


def build_lote():
    """Carimba o João como 4ª fileira no lote original (1 A4, 4 pessoas)."""
    register_fonts()
    qr = qr_image()
    overlay = BytesIO()
    c = canvas.Canvas(overlay, pagesize=A4)
    page_w, page_h = A4

    # mesma coluna do lote original (medido no PDF do André)
    x0 = 14.56 * mm
    gap_x = 10.08 * mm
    x1 = x0 + CARD_W + gap_x

    # cobre rodapé e o vão sob o Projecon; 3ª fileira termina ~222 mm do topo
    wipe_top = 71.0 * mm
    c.setFillColor(white)
    c.rect(0, 0, page_w, wipe_top, stroke=0, fill=1)

    # cobre a linha "Três cartões NFC..."
    c.rect(20 * mm, page_h - 17.4 * mm, page_w - 40 * mm, 4.2 * mm, stroke=0, fill=1)
    c.setFillColor(HexColor("#555555"))
    c.setFont("JB", 7.5)
    c.drawCentredString(
        page_w / 2,
        page_h - 16.3 * mm,
        "Quatro cartões NFC  ·  85,5 × 54 mm  ·  duas faces iguais de cada um (frente e verso).",
    )

    y = 13.2 * mm
    for x, face in ((x0, "FRENTE"), (x1, "VERSO")):
        crop_marks(c, x, y)
        draw_label(c, x, y + CARD_H + 3.0 * mm, face)
        draw_card(c, x, y, qr)

    c.setFillColor(HexColor("#888888"))
    c.setFont("JB", 7.0)
    c.drawCentredString(
        page_w / 2,
        5.2 * mm,
        "Cola uma face de cada lado do cartão NFC. QR e NFC levam ao mesmo link.",
    )
    c.save()
    overlay.seek(0)

    src = ORIG_LOTE if ORIG_LOTE.exists() else OUT_LOTE
    base = PdfReader(str(src))
    stamp = PdfReader(overlay)
    page = base.pages[0]
    page.merge_page(stamp.pages[0])
    w = PdfWriter()
    w.add_page(page)
    w.add_metadata({
        "/Title": "Adesivos NFC — André, Helena, Projecon, João",
        "/Author": "João V. Ferreira",
    })
    OUT_DIR.mkdir(exist_ok=True)
    with OUT_LOTE.open("wb") as f:
        w.write(f)
    print(f"[ok] {OUT_LOTE.relative_to(ROOT)}  (1 página, 4 pessoas)")


if __name__ == "__main__":
    build()
    build_lote()
