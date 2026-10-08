"""Optional forensic features. Supporting information only: they never decide the prediction (metadata can be
removed or forged)."""
from __future__ import annotations

import numpy as np
from PIL import ExifTags, Image

GENERATOR_HINTS = ("stable diffusion", "midjourney", "dall", "comfyui", "automatic1111", "novelai", "firefly", "flux")


def estimate_jpeg_quality(image: Image.Image) -> int | None:
    """Rough libjpeg quality estimate from the luminance quantization table."""
    tables = getattr(image, "quantization", None)
    if not tables or 0 not in tables:
        return None
    mean_q = float(np.mean(tables[0]))
    # Standard libjpeg luminance table has mean ~57.6 at quality 50.
    scale = mean_q / 57.625 * 100
    quality = (200 - scale) / 2 if scale <= 100 else 5000 / scale
    return int(np.clip(round(quality), 1, 100))


def extract(original: Image.Image, rgb: Image.Image) -> dict:
    exif = original.getexif()
    tags = {ExifTags.TAGS.get(k, str(k)): v for k, v in exif.items()} if exif else {}
    text_meta = " ".join(str(v) for v in list(tags.values()) + list(original.info.values()) if isinstance(v, (str, bytes)))
    hints = sorted({h for h in GENERATOR_HINTS if h in text_meta.lower()})

    gray = np.asarray(rgb.convert("L").resize((512, 512)), dtype=np.float32)
    lap = gray[1:-1, 1:-1] * 4 - gray[:-2, 1:-1] - gray[2:, 1:-1] - gray[1:-1, :-2] - gray[1:-1, 2:]
    spectrum = np.abs(np.fft.fftshift(np.fft.fft2(gray - gray.mean())))
    yy, xx = np.ogrid[-256:256, -256:256]
    high = np.sqrt(yy ** 2 + xx ** 2) > 128

    return {
        "format": original.format,
        "width": original.width,
        "height": original.height,
        "mode": original.mode,
        "has_exif": bool(tags),
        "camera": " ".join(str(tags[k]) for k in ("Make", "Model") if k in tags) or None,
        "software": str(tags["Software"]) if "Software" in tags else None,
        "generator_metadata_hints": hints,
        "jpeg_quality_estimate": estimate_jpeg_quality(original),
        "noise_level": round(float(lap.std()), 3),
        "high_frequency_ratio": round(float(spectrum[high].sum() / total), 4) if (total := spectrum.sum()) > 0 else 0.0,
    }
