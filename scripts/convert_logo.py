"""
convert_logo.py — One-time: TIFF CMYK → 2 PNG RGB con sfondo trasparente.
  assets/logo.png       → wordmark pieno (max 400px wide)
  assets/logo_icon.png  → solo la "B" iniziale (max 100px tall)
"""

from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

TIFF_PATH = Path(r"C:\Users\Pietro\Desktop\05_Bellevue.tif")


def cmyk_to_rgb(img: Image.Image) -> Image.Image:
    """Converte CMYK → RGB manualmente via NumPy."""
    arr = np.array(img, dtype=np.float32) / 255.0
    c, m, y, k = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    r = 255 * (1 - c) * (1 - k)
    g = 255 * (1 - m) * (1 - k)
    b = 255 * (1 - y) * (1 - k)
    rgb = np.stack([r, g, b], axis=-1).astype(np.uint8)
    return Image.fromarray(rgb, "RGB")


def remove_white_bg(img: Image.Image, threshold: int = 245) -> Image.Image:
    """Rende trasparenti i pixel quasi-bianchi."""
    arr = np.array(img.convert("RGBA"))
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    white_mask = (r > threshold) & (g > threshold) & (b > threshold)
    arr[white_mask, 3] = 0
    return Image.fromarray(arr, "RGBA")


def crop_to_content(img: Image.Image) -> Image.Image:
    """Crop ai pixel non-trasparenti."""
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def extract_icon(img: Image.Image) -> Image.Image:
    """Estrae la lettera 'B' — primo ~30% della larghezza."""
    w, h = img.size
    # Cerca il gap tra la B e il resto del testo
    arr = np.array(img)
    alpha = arr[..., 3]
    # Somma alpha per colonna
    col_sums = alpha.sum(axis=0)
    # Cerca il primo gap (colonne vuote) dopo il primo blocco di contenuto
    in_content = False
    gap_start = None
    for x in range(w):
        if col_sums[x] > 0:
            in_content = True
        elif in_content and col_sums[x] == 0:
            gap_start = x
            break

    if gap_start and gap_start < w * 0.5:
        icon = img.crop((0, 0, gap_start, h))
    else:
        # Fallback: primo 25%
        icon = img.crop((0, 0, int(w * 0.25), h))

    return crop_to_content(icon)


def main():
    print(f"Input: {TIFF_PATH}")
    img = Image.open(TIFF_PATH)
    print(f"  Modo: {img.mode}, Size: {img.size}")

    # CMYK → RGB
    if img.mode == "CMYK":
        img = cmyk_to_rgb(img)
        print("  Convertito CMYK -> RGB")

    # Rimuovi sfondo bianco
    img = remove_white_bg(img)
    print("  Sfondo bianco rimosso")

    # Crop
    img = crop_to_content(img)
    print(f"  Cropped: {img.size}")

    # ── Logo pieno ──
    max_w = 400
    if img.width > max_w:
        ratio = max_w / img.width
        new_h = int(img.height * ratio)
        logo = img.resize((max_w, new_h), Image.LANCZOS)
    else:
        logo = img.copy()

    logo_path = ASSETS / "logo.png"
    logo.save(logo_path, "PNG")
    print(f"  Salvato: {logo_path} ({logo.size})")

    # ── Icona "B" ──
    icon = extract_icon(img)
    max_h = 100
    if icon.height > max_h:
        ratio = max_h / icon.height
        new_w = int(icon.width * ratio)
        icon = icon.resize((new_w, max_h), Image.LANCZOS)

    icon_path = ASSETS / "logo_icon.png"
    icon.save(icon_path, "PNG")
    print(f"  Salvato: {icon_path} ({icon.size})")

    print("Done!")


if __name__ == "__main__":
    main()
