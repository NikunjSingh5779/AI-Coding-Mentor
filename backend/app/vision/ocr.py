from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image


@dataclass(frozen=True)
class OCRLine:
    text: str
    left: int
    top: int
    width: int
    height: int
    confidence: float


def decode_image(data: bytes) -> Image.Image:
    image = Image.open(BytesIO(data))
    image.load()
    if image.width > 3840 or image.height > 2160:
        image.thumbnail((3840, 2160))
    return image.convert("RGB")


def extract_lines(image: Image.Image, engine: str = "tesseract") -> list[OCRLine]:
    if engine != "tesseract":
        raise RuntimeError(f"Unsupported OCR engine: {engine}")

    try:
        import pytesseract
        from pytesseract import Output
    except ImportError as exc:
        raise RuntimeError("pytesseract is not installed") from exc

    data = pytesseract.image_to_data(
        image,
        output_type=Output.DICT,
        config="--psm 6",
    )
    buckets: dict[tuple[int, int, int], list[int]] = {}
    for index, text in enumerate(data["text"]):
        value = str(text).strip()
        if not value:
            continue
        key = (
            int(data["block_num"][index]),
            int(data["par_num"][index]),
            int(data["line_num"][index]),
        )
        buckets.setdefault(key, []).append(index)

    lines: list[OCRLine] = []
    for indexes in buckets.values():
        parts = [str(data["text"][i]).strip() for i in indexes if str(data["text"][i]).strip()]
        if not parts:
            continue
        left = min(int(data["left"][i]) for i in indexes)
        top = min(int(data["top"][i]) for i in indexes)
        right = max(int(data["left"][i]) + int(data["width"][i]) for i in indexes)
        bottom = max(int(data["top"][i]) + int(data["height"][i]) for i in indexes)
        confs = [float(data["conf"][i]) for i in indexes if float(data["conf"][i]) >= 0]
        confidence = (sum(confs) / len(confs) / 100.0) if confs else 0.0
        lines.append(
            OCRLine(
                text=" ".join(parts),
                left=left,
                top=top,
                width=max(1, right - left),
                height=max(1, bottom - top),
                confidence=max(0.0, min(1.0, confidence)),
            )
        )

    return sorted(lines, key=lambda line: (line.top, line.left))
