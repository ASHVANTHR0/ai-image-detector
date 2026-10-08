import io
from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin

from app.services import provenance
from app.services.prediction import PredictionService
from tests.conftest import image_bytes, make_ensemble, upload

FIXTURES = Path(__file__).parent / "fixtures"


def png_with_text(**chunks) -> bytes:
    info = PngImagePlugin.PngInfo()
    for k, v in chunks.items():
        info.add_text(k, v)
    buf = io.BytesIO()
    Image.new("RGB", (128, 128), (40, 90, 160)).save(buf, format="PNG", pnginfo=info)
    return buf.getvalue()


def jpeg_with_exif(**tags) -> bytes:
    img = Image.new("RGB", (128, 128), (10, 20, 30))
    exif = Image.Exif()
    names = {"Software": 0x0131, "Make": 0x010F, "ImageDescription": 0x010E}
    for k, v in tags.items():
        exif[names[k]] = v
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def check(data: bytes) -> dict:
    return provenance.check(data, Image.open(io.BytesIO(data)))


def test_signed_c2pa_ai_manifest_is_verified():
    data = (FIXTURES / "c2pa_signed_algorithmic.jpg").read_bytes()
    result = check(data)
    assert result["verdict"] == "AI_GENERATED" and result["strength"] == "verified"
    assert "algorithmicmedia" in result["signals"][0]["detail"]


def test_tampered_c2pa_is_ignored():
    data = bytearray((FIXTURES / "c2pa_signed_algorithmic.jpg").read_bytes())
    data[-500] ^= 0xFF  # change image pixels after signing
    result = check(bytes(data))
    assert result["verdict"] is None
    assert result["signals"][0]["strength"] == "invalid"


@pytest.mark.parametrize("chunks", [
    {"parameters": "a cat\nSteps: 30, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 1, Model hash: abc"},
    {"prompt": '{"3": {"class_type": "KSampler", "inputs": {}}}'},
    {"invokeai_metadata": "{}"},
    {"Software": "NovelAI", "Comment": '{"steps": 28, "sampler": "k_euler"}'},
])
def test_generation_parameters_detected(chunks):
    assert check(png_with_text(**chunks))["verdict"] == "AI_GENERATED"


def test_xmp_digital_source_type_detected():
    xmp = ('<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF><rdf:Description Iptc4xmpExt:DigitalSourceType='
           '"http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"/></rdf:RDF></x:xmpmeta>')
    result = check(png_with_text(**{"XML:com.adobe.xmp": xmp}))
    assert result["verdict"] == "AI_GENERATED" and result["strength"] == "strong"


@pytest.mark.parametrize("tags", [{"Software": "Midjourney v6"}, {"ImageDescription": "Created with Adobe Firefly"}])
def test_exif_generator_name_is_weak_ai_evidence(tags):
    result = check(jpeg_with_exif(**tags))
    assert result["verdict"] == "AI_GENERATED" and result["strength"] == "weak"


@pytest.mark.parametrize("data", [
    image_bytes("JPEG"),
    jpeg_with_exif(Make="Canon", Software="Adobe Photoshop 25.0"),   # editing software is not AI evidence
    png_with_text(parameters="just some text without sampler settings"),
])
def test_no_evidence_means_no_verdict(data):
    assert check(data)["verdict"] is None


def test_provenance_overrides_detectors_in_api(app, client):
    app.state.prediction_service = PredictionService(make_ensemble(scores=(0.01, 0.03)))  # detectors say REAL
    data = png_with_text(parameters="Steps: 20, Sampler: Euler a, CFG scale: 7")
    body = upload(client, data, "sd.png").json()
    assert body["prediction"] == "AI_GENERATED" and body["confidence"] == "VERIFIED"
    assert body["decided_by"] == "provenance" and body["ai_probability"] >= 0.99
    assert body["model_ai_probability"] == pytest.approx(0.02)
    assert body["provenance"]["signals"][0]["source"] == "generation_parameters"


def test_without_evidence_detectors_decide(client):
    body = upload(client, image_bytes()).json()
    assert body["decided_by"] == "detectors" and body["provenance"] is None
