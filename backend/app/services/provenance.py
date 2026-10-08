"""Provenance validator: looks for evidence *inside the file* of how the image was made.

Unlike the detectors (which estimate), this finds explicit records:
  1. C2PA Content Credentials (OpenAI GPT Image / DALL-E 3, Adobe Firefly, Google Imagen/Gemini, Microsoft Designer,
     signed cameras from Leica/Sony/Nikon ...). Signatures are verified with the official c2pa library, so a forged
     or altered manifest is reported as invalid and ignored.
  2. IPTC DigitalSourceType in XMP ("trainedAlgorithmicMedia" = made by generative AI).
  3. Generation parameters written by Stable Diffusion WebUI, ComfyUI, InvokeAI, NovelAI, Fooocus ...
  4. Generator names in EXIF/XMP software fields (weaker: these are unsigned and easy to edit).

Only *presence* of evidence decides anything. Absence proves nothing: screenshots, re-saving and social media strip
metadata, so images without provenance are left to the detectors.
"""
from __future__ import annotations

import io
import json
import re

from PIL import ExifTags, Image

try:
    import c2pa
except ImportError:  # optional dependency
    c2pa = None

AI_SOURCE_TYPES = {"trainedalgorithmicmedia", "compositewithtrainedalgorithmicmedia", "algorithmicmedia",
                   "compositesynthetic"}
CAPTURE_SOURCE_TYPES = {"digitalcapture", "computationalcapture"}
GENERATOR_NAMES = (
    "midjourney", "dall-e", "dall·e", "dalle", "openai", "chatgpt", "gpt-4o", "gpt image", "gpt-image", "sora",
    "stable diffusion", "stablediffusion", "sdxl", "comfyui", "automatic1111", "invokeai", "novelai", "fooocus",
    "firefly", "imagen", "gemini", "nano banana", "nano-banana", "flux", "black forest labs", "ideogram",
    "leonardo.ai", "playground ai", "bing image creator", "microsoft designer", "image creator from designer",
    "runway", "krea", "recraft", "dreamstudio", "nightcafe", "craiyon", "hidream", "seedream", "kling", "hunyuan",
)
MIME = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "BMP": "image/bmp"}
_DST = re.compile(rb"DigitalSourceType[\"'>=\s]+(?:[^\"'<>]*/)?([A-Za-z]+)")


def _generator_in(text: str) -> str | None:
    low = text.lower()
    return next((g for g in GENERATOR_NAMES if g in low), None)


def _source_type(uri: str) -> str:
    return uri.rstrip("/").rsplit("/", 1)[-1].lower()


def _c2pa_signals(data: bytes, fmt: str | None) -> list[dict]:
    if c2pa is None or fmt not in MIME:
        return []
    try:
        with c2pa.Reader(MIME[fmt], io.BytesIO(data)) as reader:
            state = str(reader.get_validation_state() or "")
            store = json.loads(reader.json())
    except Exception as exc:
        if "ManifestNotFound" in type(exc).__name__ or "no JUMBF" in str(exc):
            return []
        return [{"source": "c2pa", "verdict": None, "strength": "invalid",
                 "detail": f"Content Credentials present but unreadable ({type(exc).__name__})"}]

    active = store.get("manifests", {}).get(store.get("active_manifest"), {})
    signer = (active.get("signature_info") or {}).get("issuer") or "unknown signer"
    if state.lower() == "invalid":
        return [{"source": "c2pa", "verdict": None, "strength": "invalid",
                 "detail": f"Content Credentials signed by {signer} failed verification (file altered after signing); ignored"}]

    agents, ai_types, capture_types = set(), set(), set()
    for manifest in store.get("manifests", {}).values():  # active manifest + ingredients' history
        gen = manifest.get("claim_generator") or ""
        for info in manifest.get("claim_generator_info") or []:
            gen += " " + str(info.get("name", ""))
        if gen.strip():
            agents.add(gen.strip())
        for assertion in manifest.get("assertions", []):
            if not assertion.get("label", "").startswith("c2pa.actions"):
                continue
            for action in (assertion.get("data") or {}).get("actions", []):
                kind = _source_type(str(action.get("digitalSourceType", "")))
                agent = action.get("softwareAgent")
                if isinstance(agent, dict):
                    agent = agent.get("name")
                if agent:
                    agents.add(str(agent))
                if kind in AI_SOURCE_TYPES:
                    ai_types.add(kind)
                elif kind in CAPTURE_SOURCE_TYPES:
                    capture_types.add(kind)

    tool = ", ".join(sorted(agents)) or "unknown tool"
    strength = "verified" if state.lower() in ("valid", "trusted") else "strong"
    if ai_types:
        return [{"source": "c2pa", "verdict": "AI_GENERATED", "strength": strength,
                 "detail": f"Content Credentials ({state or 'unverified'}, signed by {signer}) declare "
                           f"{', '.join(sorted(ai_types))} - created with {tool}"}]
    if _generator_in(tool):
        return [{"source": "c2pa", "verdict": "AI_GENERATED", "strength": strength,
                 "detail": f"Content Credentials ({state or 'unverified'}, signed by {signer}) name an AI generator: {tool}"}]
    if capture_types:
        return [{"source": "c2pa", "verdict": "REAL", "strength": strength,
                 "detail": f"Content Credentials ({state or 'unverified'}, signed by {signer}) declare a camera capture "
                           f"({', '.join(sorted(capture_types))}) with {tool}"}]
    return [{"source": "c2pa", "verdict": None, "strength": "info",
             "detail": f"Content Credentials ({state}) from {tool}, signed by {signer}, with no AI or camera declaration"}]


def _xmp_signals(data: bytes, image: Image.Image) -> list[dict]:
    xmp = image.info.get("xmp") or image.info.get("XML:com.adobe.xmp") or b""
    if isinstance(xmp, str):
        xmp = xmp.encode("utf-8", "ignore")
    if not xmp:
        start = data.find(b"<x:xmpmeta")
        xmp = data[start:data.find(b"</x:xmpmeta>", start) + 12] if start >= 0 else b""
    signals = []
    for match in _DST.finditer(xmp):
        kind = match.group(1).decode("ascii", "ignore").lower()
        if kind in AI_SOURCE_TYPES:
            signals.append({"source": "xmp", "verdict": "AI_GENERATED", "strength": "strong",
                            "detail": f"IPTC DigitalSourceType in XMP metadata is '{match.group(1).decode()}' (generative AI)"})
            break
    text = xmp.decode("utf-8", "ignore")
    tool = re.search(r"CreatorTool[\"'>=\s]+([^\"'<]+)", text)
    if tool and (gen := _generator_in(tool.group(1))):
        signals.append({"source": "xmp", "verdict": "AI_GENERATED", "strength": "weak",
                        "detail": f"XMP CreatorTool is '{tool.group(1).strip()}' ({gen})"})
    return signals


def _png_text_signals(image: Image.Image) -> list[dict]:
    info = {str(k).lower(): v for k, v in image.info.items() if isinstance(v, (str, bytes))}

    def text(key):
        v = info.get(key, "")
        return v.decode("utf-8", "ignore") if isinstance(v, bytes) else v

    params = text("parameters")
    if "steps:" in params.lower() and ("sampler" in params.lower() or "cfg scale" in params.lower()):
        return [{"source": "generation_parameters", "verdict": "AI_GENERATED", "strength": "strong",
                 "detail": "Stable Diffusion generation parameters embedded (Steps / Sampler / CFG scale)"}]
    for key in ("prompt", "workflow"):
        if '"class_type"' in text(key) or '"nodes"' in text(key):
            return [{"source": "generation_parameters", "verdict": "AI_GENERATED", "strength": "strong",
                     "detail": f"ComfyUI workflow embedded in the '{key}' field"}]
    for key in ("invokeai_metadata", "sd-metadata", "dream", "fooocus_scheme"):
        if key in info:
            return [{"source": "generation_parameters", "verdict": "AI_GENERATED", "strength": "strong",
                     "detail": f"AI generator metadata field '{key}' embedded"}]
    comment = text("comment")
    if text("software").lower().startswith("novelai") or ('"sampler"' in comment and '"steps"' in comment):
        return [{"source": "generation_parameters", "verdict": "AI_GENERATED", "strength": "strong",
                 "detail": "NovelAI-style generation parameters embedded"}]
    return []


def _exif_signals(image: Image.Image) -> list[dict]:
    exif = image.getexif()
    if not exif:
        return []
    fields = {ExifTags.TAGS.get(k, str(k)): v for k, v in exif.items()}
    try:
        fields.update({ExifTags.TAGS.get(k, str(k)): v for k, v in exif.get_ifd(ExifTags.IFD.Exif).items()})
    except Exception:
        pass
    for name in ("Software", "Artist", "ImageDescription", "Make", "Model", "UserComment", "XPComment"):
        value = fields.get(name)
        if isinstance(value, bytes):
            value = value.decode("utf-8", "ignore").replace("\x00", "")
        if not isinstance(value, str) or not value.strip():
            continue
        if "steps:" in value.lower() and "sampler" in value.lower():
            return [{"source": "exif", "verdict": "AI_GENERATED", "strength": "strong",
                     "detail": f"Stable Diffusion generation parameters in EXIF {name}"}]
        if gen := _generator_in(value):
            return [{"source": "exif", "verdict": "AI_GENERATED", "strength": "weak",
                     "detail": f"EXIF {name} names an AI generator: '{value.strip()[:80]}' ({gen})"}]
    return []


def check(data: bytes, image: Image.Image) -> dict:
    """Return {"verdict": "AI_GENERATED" | "REAL" | None, "strength": ..., "signals": [...]}."""
    signals = (_c2pa_signals(data, image.format) + _xmp_signals(data, image)
               + _png_text_signals(image) + _exif_signals(image))
    rank = {"verified": 3, "strong": 2, "weak": 1}
    ai = [s for s in signals if s["verdict"] == "AI_GENERATED"]
    real = [s for s in signals if s["verdict"] == "REAL"]
    if ai:  # any trustworthy AI declaration wins; a camera claim cannot cancel it
        best = max(ai, key=lambda s: rank[s["strength"]])
        return {"verdict": "AI_GENERATED", "strength": best["strength"], "signals": signals}
    if real and max(rank[s["strength"]] for s in real) >= 2:
        return {"verdict": "REAL", "strength": max(real, key=lambda s: rank[s["strength"]])["strength"], "signals": signals}
    return {"verdict": None, "strength": None, "signals": signals}
