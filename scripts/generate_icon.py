"""
Generate icon assets for J.A.R.V.I.S desktop app.

Run this script once before building with PyInstaller:
    python scripts/generate_icon.py

Outputs:
    jarvis/assets/icon.png        — 512x512 PNG (Linux tray + source)
    jarvis/assets/icon_active.png — 512x512 PNG (green, listening state)
    jarvis/assets/icon.ico        — Windows multi-size .ico
    jarvis/assets/icon.icns       — macOS .icns (requires Pillow + macOS)
"""
from __future__ import annotations

import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Instalá Pillow primero: pip install Pillow")
    sys.exit(1)

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "jarvis", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)


def _draw_icon(size: int = 512, active: bool = False) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = int(size * 0.04)
    circle_fill = (0, 200, 80, 255) if active else (0, 120, 220, 255)
    draw.ellipse((pad, pad, size - pad, size - pad), fill=circle_fill)

    # Microphone body
    mx1 = int(size * 0.34)
    mx2 = int(size * 0.66)
    my1 = int(size * 0.16)
    my2 = int(size * 0.56)
    radius = int(size * 0.13)
    draw.rounded_rectangle((mx1, my1, mx2, my2), radius=radius, fill=(255, 255, 255, 230))

    # Microphone arc (stand)
    arc_pad = int(size * 0.24)
    arc_top = int(size * 0.40)
    arc_bot = int(size * 0.70)
    stroke = max(3, int(size * 0.04))
    draw.arc((arc_pad, arc_top, size - arc_pad, arc_bot), start=0, end=180,
             fill=(255, 255, 255, 230), width=stroke)

    # Stand line + base
    cx = size // 2
    line_top = int(size * 0.70)
    line_bot = int(size * 0.82)
    base_w = int(size * 0.24)
    draw.line((cx, line_top, cx, line_bot), fill=(255, 255, 255, 230), width=stroke)
    draw.line((cx - base_w // 2, line_bot, cx + base_w // 2, line_bot),
              fill=(255, 255, 255, 230), width=stroke)

    # Activity dot when active
    if active:
        dot = int(size * 0.10)
        dot_x = int(size * 0.68)
        dot_y = int(size * 0.68)
        draw.ellipse((dot_x, dot_y, dot_x + dot, dot_y + dot), fill=(255, 220, 50, 255))

    return img


def _save_png(img: Image.Image, name: str) -> None:
    path = os.path.join(ASSETS_DIR, name)
    img.save(path, format="PNG")
    print(f"  ✓ {path}")


def _save_ico(img: Image.Image) -> None:
    path = os.path.join(ASSETS_DIR, "icon.ico")
    sizes = [16, 32, 48, 64, 128, 256]
    imgs = [img.resize((s, s), Image.LANCZOS) for s in sizes]
    imgs[0].save(path, format="ICO", sizes=[(s, s) for s in sizes], append_images=imgs[1:])
    print(f"  ✓ {path}")


def _save_icns(img: Image.Image) -> None:
    """Save .icns using macOS iconutil (macOS only)."""
    import subprocess
    import tempfile
    import shutil

    if sys.platform != "darwin":
        print("  ⚠ .icns solo se puede generar en macOS. Saltando.")
        return
    if not shutil.which("iconutil"):
        print("  ⚠ iconutil no encontrado. Saltando .icns.")
        return

    sizes = [16, 32, 64, 128, 256, 512, 1024]
    with tempfile.TemporaryDirectory(suffix=".iconset") as iconset:
        for s in sizes:
            resized = img.resize((s, s), Image.LANCZOS)
            resized.save(os.path.join(iconset, f"icon_{s}x{s}.png"))
            # Retina
            retina = img.resize((s * 2, s * 2), Image.LANCZOS)
            retina.save(os.path.join(iconset, f"icon_{s}x{s}@2x.png"))

        out_path = os.path.join(ASSETS_DIR, "icon.icns")
        result = subprocess.run(["iconutil", "-c", "icns", iconset, "-o", out_path],
                                capture_output=True)
        if result.returncode == 0:
            print(f"  ✓ {out_path}")
        else:
            print(f"  ✗ Error generando .icns: {result.stderr.decode()}")


def main() -> None:
    print("Generando íconos de J.A.R.V.I.S...")

    base = _draw_icon(size=512, active=False)
    active = _draw_icon(size=512, active=True)

    _save_png(base, "icon.png")
    _save_png(active, "icon_active.png")
    _save_ico(base)
    _save_icns(base)

    print("\n¡Listo! Íconos generados en jarvis/assets/")


if __name__ == "__main__":
    main()
