from __future__ import annotations

from typing import Any

import httpx


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


def search_places(query: str, *, timeout_seconds: float = 8.0) -> list[dict[str, Any]]:
    """Return compact global place matches from Open-Meteo's geocoder."""
    clean_query = " ".join(query.strip().split())
    if len(clean_query) < 2:
        return []
    with httpx.Client(timeout=timeout_seconds, follow_redirects=False) as client:
        response = client.get(
            GEOCODING_URL,
            params={"name": clean_query, "count": 6, "language": "en", "format": "json"},
        )
        response.raise_for_status()
    matches = []
    for item in response.json().get("results", []):
        label_parts = [item.get("name"), item.get("admin1"), item.get("country")]
        label = ", ".join(str(part) for part in label_parts if part)
        matches.append(
            {
                "label": label,
                "latitude": float(item["latitude"]),
                "longitude": float(item["longitude"]),
                "timezone": item.get("timezone"),
                "country_code": item.get("country_code"),
            }
        )
    return matches
