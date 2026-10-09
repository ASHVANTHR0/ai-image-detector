import io

import pytest
from PIL import Image

from app.config import Settings
from app.models.detector import find_ai_indices
from app.models.ensemble import combine, decide
from app.services import forensic
from app.services.preprocessing import to_rgb
from app.utils.hashing import sha256_bytes
from app.utils.validation import ValidationError, safe_filename, validate_image_bytes
from tests.conftest import image_bytes

SETTINGS = Settings(load_models=False)


@pytest.mark.parametrize("p, expected", [
    (0.95, ("AI_GENERATED", "HIGH")),
    (0.9, ("AI_GENERATED", "HIGH")),   # exactly t_high is decided
    (0.1, ("REAL", "HIGH")),           # exactly t_low is decided
    (0.02, ("REAL", "HIGH")),
    (0.5, ("UNCERTAIN", "LOW")),
    (0.899, ("UNCERTAIN", "LOW")),
])
def test_decide_thresholds(p, expected):
    assert decide(p, 0.1, 0.9) == expected


def test_decide_medium_confidence_with_narrow_band():
    assert decide(0.75, 0.3, 0.7) == ("AI_GENERATED", "MEDIUM")
    assert decide(0.25, 0.3, 0.7) == ("REAL", "MEDIUM")


def test_combine_logit_stack():
    # sigmoid(0.5 + 2*logit(0.8) + 1*logit(0.3)) computed by hand
    import math
    z = 0.5 + 2 * math.log(0.8 / 0.2) + math.log(0.3 / 0.7)
    expected = 1 / (1 + math.exp(-z))
    assert combine({"a": 0.8, "b": 0.3}, {"a": 2, "b": 1}, "logit_stack", intercept=0.5) == pytest.approx(expected)
    assert 0 < combine({"a": 0.0, "b": 1.0}, {"a": 1, "b": 1}, "logit_stack") < 1  # extreme scores are clipped


def test_combine_weighted_and_vote():
    assert combine({"a": 1.0, "b": 0.0}, {"a": 3, "b": 1}) == pytest.approx(0.75)
    assert combine({"a": 0.9, "b": 0.2, "c": 0.7}, {"a": 1, "b": 1, "c": 1}, "majority_vote") == pytest.approx(2 / 3)


@pytest.mark.parametrize("id2label, idx", [
    ({0: "artificial", 1: "human"}, [0]),
    ({0: "human", 1: "artificial"}, [1]),
    ({0: "REAL", 1: "FAKE"}, [1]),
    ({0: "ai", 1: "hum"}, [0]),
    ({0: "human", 1: "AI-generated"}, [1]),
    ({0: "dalle", 1: "real", 2: "sd"}, [0, 2]),          # multi-class: everything that is not real
    ({0: "AI", 1: "Deepfake", 2: "Real"}, [0, 1]),
    ({"0": "Realism", "1": "Deepfake"}, None),
])
def test_find_ai_indices(id2label, idx):
    if idx is None:
        with pytest.raises(ValueError):
            find_ai_indices(id2label)
    else:
        assert find_ai_indices(id2label) == idx


def test_find_ai_indices_override():
    assert find_ai_indices({0: "Realism", 1: "Deepfake"}, "deepfake") == [1]
    assert find_ai_indices({0: "a", 1: "b", 2: "c"}, "a, c") == [0, 2]


def test_hash_is_sha256():
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


@pytest.mark.parametrize("raw, clean", [
    ("../../etc/passwd.png", "passwd.png"),
    ("C:\\Users\\x\\pic.jpg", "pic.jpg"),
    ("bad\x00name.png", "badname.png"),
    (None, "upload"),
    ("a" * 300 + ".png", "a" * 200),
])
def test_safe_filename(raw, clean):
    assert safe_filename(raw) == clean


@pytest.mark.parametrize("mode, fmt", [("RGB", "JPEG"), ("RGBA", "PNG"), ("L", "PNG"), ("CMYK", "JPEG"), ("P", "PNG")])
def test_to_rgb_handles_modes(mode, fmt):
    data = image_bytes(fmt, mode=mode) if mode != "P" else _palette_png()
    out = to_rgb(Image.open(io.BytesIO(data)))
    assert out.mode == "RGB" and out.size == (128, 128)


def _palette_png():
    buf = io.BytesIO()
    Image.new("RGB", (128, 128), (1, 2, 3)).convert("P").save(buf, format="PNG", transparency=0)
    return buf.getvalue()


def test_transparent_png_flattened_on_white():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    assert to_rgb(img).getpixel((0, 0)) == (255, 255, 255)


def test_validation_accepts_good_image():
    img = validate_image_bytes(image_bytes("JPEG"), "x.jpg", SETTINGS)
    assert img.size == (128, 128)


@pytest.mark.parametrize("data, name, code", [
    (b"MZ\x90\x00 definitely not an image", "evil.jpg", 415),
    (image_bytes("PNG"), "photo.exe", 415),
    (image_bytes("GIF"), "anim.png", 415),            # content is GIF, not allowed
    (image_bytes("PNG", size=(16, 16)), "tiny.png", 400),
    (image_bytes("JPEG")[:300], "truncated.jpg", 400),
])
def test_validation_rejects(data, name, code):
    with pytest.raises(ValidationError) as err:
        validate_image_bytes(data, name, SETTINGS)
    assert err.value.status_code == code


def test_validation_rejects_decompression_bomb():
    settings = Settings(load_models=False, max_image_pixels=10_000)
    with pytest.raises(ValidationError) as err:
        validate_image_bytes(image_bytes("PNG", size=(200, 200)), "big.png", settings)
    assert err.value.status_code == 400


def test_forensics_extracts_jpeg_quality():
    img = Image.open(io.BytesIO(image_bytes("JPEG", quality=75)))
    features = forensic.extract(img, to_rgb(img))
    assert features["format"] == "JPEG"
    assert 65 <= features["jpeg_quality_estimate"] <= 85
    assert features["has_exif"] is False
