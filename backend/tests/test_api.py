from app.services.prediction import PredictionService
from tests.conftest import image_bytes, make_ensemble, upload


def test_health(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok" and body["model_loaded"] is True
    assert body["model_version"] == "test-ensemble+prov1"
    assert body["thresholds"] == {"t_low": 0.1, "t_high": 0.9}


def test_health_without_model(app, client):
    app.state.prediction_service = None
    app.state.model_error = "boom"
    body = client.get("/api/v1/health").json()
    assert body["model_loaded"] is False and body["error"] == "boom"
    assert upload(client, image_bytes()).status_code == 503


def test_detect_roundtrip(client):
    res = upload(client, image_bytes("JPEG"), "portrait.jpg")
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["prediction"] == "AI_GENERATED"
    assert body["ai_probability"] == 0.97
    assert abs(body["ai_probability"] + body["real_probability"] - 1) < 1e-9
    assert body["confidence"] == "HIGH"
    assert body["model_name"] == "test-ensemble+prov1"
    assert body["filename"] == "portrait.jpg"
    assert set(body["member_scores"]) == {"fake_0", "fake_1"}
    assert body["forensics"]["format"] == "JPEG"
    assert body["recommendation"] is None

    fetched = client.get(f"/api/v1/detections/{body['id']}").json()
    assert fetched["created_at"].endswith(("Z", "+00:00"))  # timezone survives the SQLite round trip
    assert fetched["file_hash"] == body["file_hash"] and fetched["prediction"] == "AI_GENERATED"


def test_uncertain_result_has_recommendation(app, client):
    app.state.prediction_service = PredictionService(make_ensemble(scores=(0.4, 0.6)))
    body = upload(client, image_bytes()).json()
    assert body["prediction"] == "UNCERTAIN" and body["confidence"] == "LOW"
    assert body["recommendation"] == "Result should not be treated as definitive."


def test_same_file_is_served_from_cache(client):
    data = image_bytes(color=(1, 2, 3))
    first, second = upload(client, data).json(), upload(client, data).json()
    assert second["id"] == first["id"] and second["cached"] is True
    assert client.get("/api/v1/detections").json()["total"] == 1


def test_rejections_have_status_codes(client):
    assert upload(client, b"not an image at all", "x.jpg").status_code == 415
    assert upload(client, image_bytes(), "x.svg").status_code == 415
    assert upload(client, image_bytes(size=(10, 10))).status_code == 400
    res = upload(client, b"", "empty.png")
    assert res.status_code == 400 and "empty" in res.json()["detail"]
    assert client.get("/api/v1/detections").json()["total"] == 0


def test_too_large_upload(client, monkeypatch):
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 1000)
    res = upload(client, image_bytes("BMP", size=(200, 200)), "big.bmp")  # ~120 KB uncompressed
    assert res.status_code == 413
    assert client.get("/api/v1/detections").json()["total"] == 0


def test_grayscale_and_transparent_images(client):
    assert upload(client, image_bytes("PNG", mode="L"), "gray.png").status_code == 201
    assert upload(client, image_bytes("PNG", mode="RGBA", color=(9, 9, 9)), "alpha.png").status_code == 201
    assert upload(client, image_bytes("JPEG", mode="CMYK"), "cmyk.jpg").status_code == 201


def test_history_pagination_filter_and_statistics(app, client):
    for i in range(3):
        upload(client, image_bytes(color=(i, 0, 0)))
    app.state.prediction_service = PredictionService(make_ensemble(scores=(0.01, 0.03)))
    upload(client, image_bytes(color=(9, 9, 9)))

    page = client.get("/api/v1/detections", params={"limit": 2}).json()
    assert page["total"] == 4 and len(page["items"]) == 2
    assert page["items"][0]["prediction"] == "REAL"  # newest first
    real = client.get("/api/v1/detections", params={"prediction": "REAL"}).json()
    assert real["total"] == 1
    assert client.get("/api/v1/detections", params={"prediction": "BOGUS"}).status_code == 422
    assert client.get("/api/v1/detections/9999").status_code == 404

    stats = client.get("/api/v1/statistics").json()
    assert (stats["total"], stats["ai_generated"], stats["real"], stats["uncertain"]) == (4, 3, 1, 0)
    assert abs(stats["average_confidence"] - (0.97 * 3 + 0.98) / 4) < 1e-6
    assert sum(stats["confidence_histogram"]) == 4 and stats["confidence_histogram"][9] == 3
    assert len(stats["processing_times_ms"]) == 4


def test_evaluation_endpoint_without_results(client, monkeypatch, tmp_path):
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), "evaluation_summary", tmp_path / "missing.json")
    assert client.get("/api/v1/evaluation").json() == {"available": False}
