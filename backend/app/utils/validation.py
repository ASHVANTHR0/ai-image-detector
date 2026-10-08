"""Upload validation: size limit while streaming, extension allow-list, real content sniffing, decode checks."""
from __future__ import annotations

import io
import re
import warnings
from pathlib import PurePath

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config import Settings

CHUNK = 1 << 20


class ValidationError(HTTPException):
    def __init__(self, code: int, detail: str):
        super().__init__(status_code=code, detail=detail)


def safe_filename(name: str | None) -> str:
    base = PurePath((name or "upload").replace("\\", "/")).name
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip() or "upload"
    return base[:200]


async def read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    buf = bytearray()
    while chunk := await upload.read(CHUNK):
        buf.extend(chunk)
        if len(buf) > max_bytes:
            raise ValidationError(status.HTTP_413_CONTENT_TOO_LARGE,
                                  f"File is larger than {max_bytes // (1024 * 1024)} MB")
    if not buf:
        raise ValidationError(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty")
    return bytes(buf)


def validate_image_bytes(data: bytes, filename: str, settings: Settings) -> Image.Image:
    """Return a fully decoded image or raise ValidationError. Never trusts the extension alone."""
    ext = PurePath(filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise ValidationError(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                              f"Unsupported file type '{ext or 'none'}'. Allowed: {', '.join(settings.allowed_extensions)}")

    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(data)) as probe:
                fmt = probe.format
                if probe.width * probe.height > settings.max_image_pixels:  # header only, before decoding
                    raise ValidationError(status.HTTP_400_BAD_REQUEST, "Image has too many pixels")
                probe.verify()
            if fmt not in settings.allowed_formats:
                raise ValidationError(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                      f"File content is {fmt}, which is not an allowed image format")
            image = Image.open(io.BytesIO(data))
            image.load()
        except ValidationError:
            raise
        except (Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise ValidationError(status.HTTP_400_BAD_REQUEST, "Image has too many pixels")
        except UnidentifiedImageError:
            raise ValidationError(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "File is not a valid image")
        except Exception:
            raise ValidationError(status.HTTP_400_BAD_REQUEST, "Image is corrupt or truncated")

    if min(image.size) < settings.min_image_side:
        raise ValidationError(status.HTTP_400_BAD_REQUEST,
                              f"Image is too small (minimum {settings.min_image_side}px per side)")
    return image
