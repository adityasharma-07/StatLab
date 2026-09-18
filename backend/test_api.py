"""API smoke tests: the endpoints return the engine's results as valid typed JSON."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_datasets_endpoint():
    response = client.get("/api/datasets")
    assert response.status_code == 200
    assert response.json() == {"datasets": ["penguins", "tips"]}


def test_columns_endpoint():
    response = client.get("/api/columns", params={"dataset": "penguins"})
    assert response.status_code == 200
    body = response.json()
    assert "body_mass_g" in body["numeric"]
    assert "species" in body["categorical"]
    assert body["row_count"] == 344


def test_unknown_dataset_is_404():
    response = client.get("/api/columns", params={"dataset": "nope"})
    assert response.status_code == 404


def test_analyze_group_comparison():
    response = client.post("/api/analyze", json={"dataset": "penguins", "col_a": "body_mass_g", "col_b": "species"})
    assert response.status_code == 200
    body = response.json()
    assert body["analysis"] == "group_comparison"
    assert body["significant"] is True
    assert len(body["groups"]) == 3


def test_analyze_bad_column_is_a_clean_message_not_a_500():
    response = client.post("/api/analyze", json={"dataset": "penguins", "col_a": "nope", "col_b": "species"})
    assert response.status_code == 200
    assert response.json()["status"] == "invalid_columns"


def test_analyze_dispatches_by_column_type():
    chi = client.post("/api/analyze", json={"dataset": "tips", "col_a": "day", "col_b": "time"}).json()
    assert chi["analysis"] == "chi_square"
    assert chi["dof"] == 3

    correlation = client.post(
        "/api/analyze", json={"dataset": "penguins", "col_a": "flipper_length_mm", "col_b": "body_mass_g"}
    ).json()
    assert correlation["analysis"] == "correlation"
    assert correlation["r_squared"] > 0.7


def test_upload_then_analyze_round_trip():
    red_rows = [f"{10 + i},red" for i in range(12)]
    blue_rows = [f"{50 + i},blue" for i in range(12)]
    csv = "score,team\n" + "\n".join(red_rows + blue_rows)
    upload = client.post("/api/upload", files={"file": ("scores.csv", csv, "text/csv")})
    assert upload.status_code == 200
    body = upload.json()
    assert body["filename"] == "scores.csv"
    assert body["row_count"] == 24

    session = body["session_id"]
    columns = client.get("/api/columns", params={"session": session}).json()
    assert columns["categorical"] == ["team"]

    result = client.post("/api/analyze", json={"session": session, "col_a": "team", "col_b": "score"}).json()
    assert result["analysis"] == "group_comparison"
    assert result["significant"] is True


def test_upload_rejects_a_non_csv():
    response = client.post("/api/upload", files={"file": ("image.png", b"\x89PNG\x00\x00\xff\xfe", "image/png")})
    assert response.status_code == 400


def test_unknown_session_is_404():
    response = client.get("/api/columns", params={"session": "does-not-exist"})
    assert response.status_code == 404
