"""Shared preprocessing: identical for training, evaluation and the API. Model-specific resizing/normalization
is done by each detector's own processor."""
from PIL import Image, ImageOps


def to_rgb(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    if image.mode in ("I;16", "I;16B", "I;16L", "I"):
        image = image.point(lambda v: v / 256).convert("L")
    return image.convert("RGB")
