"""Generate synthetic screen eval datasets with ground truth.

Synthetic frames stand in for real screenshots (real learner screenshots
would need consent). Each PNG ships with a JSON ground-truth record:
region geometry for code_regions, and text for ocr_screens.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

EVAL_DIR = Path(__file__).resolve().parent.parent / "datasets"

SNIPPET = [
    "def fibonacci(n):",
    "    if n <= 1:",
    "        return n",
    "    return fibonacci(n - 1) + fibonacci(n - 2)",
    "",
    "def main():",
    "    number = 10",
    "    result = fibonacci(number)",
    '    print(f"Fibonacci of {number} is {result}")',
    "",
    'if __name__ == "__main__":',
    "    main()",
]


_FONT_CANDIDATES = [
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/cour.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/Library/Fonts/Menlo.ttc",
]


def _load_font(size: int):
    """Load a real monospace font for OCR-meaningful glyphs; None -> putText fallback."""
    from PIL import ImageFont

    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return None


def _draw_editor_frame(theme: str = "dark", w: int = 1280, h: int = 800, editor_at=(160, 90, 950, 620)):
    """Render an editor-like frame with real text glyphs (OCR-readable)."""
    from PIL import Image, ImageDraw

    bg = (30, 30, 30) if theme == "dark" else (240, 240, 240)
    pane_bg = (24, 24, 24) if theme == "dark" else (250, 250, 250)
    fg = (200, 200, 200) if theme == "dark" else (40, 40, 40)
    x, y, ew, eh = editor_at

    pil = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(pil)
    draw.rectangle([x, y, x + ew, y + eh], fill=pane_bg)

    font_size = 17
    font = _load_font(font_size)
    if font is None:
        raise RuntimeError("No monospace font available for dataset rendering")

    line_h = 24
    i = 0
    ty = y + 14
    drawn_lines: list[str] = []
    while ty + line_h < y + eh - 6:
        text = SNIPPET[i % len(SNIPPET)]
        i += 1
        draw.text((x + 18, ty), text, font=font, fill=fg)
        drawn_lines.append(text)
        ty += line_h

    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    return img, {"x": x, "y": y, "w": ew, "h": eh}, drawn_lines


def generate():
    regions_dir = EVAL_DIR / "code_regions"
    ocr_dir = EVAL_DIR / "ocr_screens"
    regions_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir.mkdir(parents=True, exist_ok=True)

    idx = 0
    for theme in ("dark", "light"):
        for scale in (1.0, 1.25):
            img, gt, drawn_lines = _draw_editor_frame(theme=theme)
            if scale != 1.0:
                img = cv2.resize(img, None, fx=scale, fy=scale)
                gt = {k: int(v * scale) for k, v in gt.items()}
            name = f"editor_{theme}_{int(scale * 100)}"
            cv2.imwrite(str(regions_dir / f"{name}.png"), img)
            (regions_dir / f"{name}.json").write_text(
                json.dumps({"image": f"{name}.png", "ground_truth_region": gt, "theme": theme, "scale": scale}, indent=2)
            )

            # OCR dataset: crop the editor region
            crop = img[gt["y"] : gt["y"] + gt["h"], gt["x"] : gt["x"] + gt["w"]]
            cv2.imwrite(str(ocr_dir / f"{name}.png"), crop)
            (ocr_dir / f"{name}.json").write_text(
                json.dumps({"image": f"{name}.png", "ground_truth_text": "\n".join(drawn_lines)}, indent=2)
            )
            idx += 1
    print(f"Generated {idx} region cases and {idx} OCR cases in {EVAL_DIR}")


if __name__ == "__main__":
    generate()
