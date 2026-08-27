from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_and_catalog_expose_six_missions():
    assert client.get("/api/v1/health").json()["status"] == "ok"
    missions = client.get("/api/v1/missions").json()
    assert len(missions) == 6
    assert {item["id"] for item in missions} == {
        "flood-watch", "crop-stress", "land-change", "irrigation", "carbon", "fire-heat"
    }


def test_land_change_api_returns_provenance_and_statuses():
    response = client.post(
        "/api/v1/analyze",
        json={
            "mission": "land-change",
            "latitude": 0,
            "longitude": 0,
            "area_hectares": 100,
            "parameters": {
                "baseline_water_pct": 30,
                "current_water_pct": 25,
                "baseline_cropland_pct": 40,
                "current_cropland_pct": 44,
                "baseline_tree_pct": 20,
                "current_tree_pct": 18,
                "class_data_confirmed": True,
            },
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["methodology_version"] == "ASE-0.2"
    assert "user-supplied" in result["data_status"]
    assert result["sources"]
    assert result["caveats"]


def test_invalid_coordinates_are_rejected():
    response = client.post(
        "/api/v1/analyze",
        json={"mission": "carbon", "latitude": 100, "longitude": 0, "area_hectares": 1},
    )
    assert response.status_code == 422
