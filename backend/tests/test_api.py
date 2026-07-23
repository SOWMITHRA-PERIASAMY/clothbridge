from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_and_fetch_donation():
    payload = {
        "donor_id": "donor_123",
        "category": "jeans",
        "image_url": "https://firebasestorage.googleapis.com/fake/jeans.jpg",
        "description": "Slightly worn jeans",
    }
    create_resp = client.post("/api/v1/donations", json=payload)
    assert create_resp.status_code == 201
    donation_id = create_resp.json()["donation_id"]

    get_resp = client.get(f"/api/v1/donations/{donation_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["donor_id"] == "donor_123"


def test_predict_returns_503_without_trained_model():
    payload = {
        "donor_id": "donor_456",
        "category": "shirt",
        "image_url": "https://firebasestorage.googleapis.com/fake/shirt.jpg",
    }
    create_resp = client.post("/api/v1/donations", json=payload)
    donation_id = create_resp.json()["donation_id"]

    predict_resp = client.post(f"/api/v1/donations/{donation_id}/predict")
    # No model.tflite exists yet in this environment — must fail loudly,
    # never return a fabricated score.
    assert predict_resp.status_code == 503


def test_recommendations_requires_prediction_first():
    payload = {
        "donor_id": "donor_789",
        "category": "saree",
        "image_url": "https://firebasestorage.googleapis.com/fake/saree.jpg",
    }
    create_resp = client.post("/api/v1/donations", json=payload)
    donation_id = create_resp.json()["donation_id"]

    rec_resp = client.get(f"/api/v1/donations/{donation_id}/recommendations")
    assert rec_resp.status_code == 400


def test_donation_not_found_returns_404():
    resp = client.get("/api/v1/donations/nonexistent-id")
    assert resp.status_code == 404


def test_invalid_image_url_rejected_by_schema():
    payload = {
        "donor_id": "donor_bad",
        "category": "shirt",
        "image_url": "not-a-valid-url",
    }
    resp = client.post("/api/v1/donations", json=payload)
    assert resp.status_code == 422
