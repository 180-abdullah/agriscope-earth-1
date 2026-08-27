from __future__ import annotations

import html
import math
from typing import Any

import folium
from folium.plugins import Fullscreen, MiniMap

from backend.app.missions.catalog import MISSIONS
from backend.app.models import MissionId
from .content import MISSION_UI


RISK_HEX = {
    "low": "#48e5c2",
    "moderate": "#ffbd59",
    "high": "#ff844b",
    "severe": "#ff495c",
}


def build_research_map(
    mission_id: MissionId,
    latitude: float,
    longitude: float,
    area_hectares: float,
    result: dict[str, Any] | None,
    location_label: str,
) -> folium.Map:
    """Build a Leaflet map that does not require a WebGL context."""
    map_object = folium.Map(
        location=[latitude, longitude],
        zoom_start=5 if result else 4,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )
    folium.TileLayer(
        tiles="CartoDB dark_matter",
        name="Dark terrain",
        control=True,
        show=True,
    ).add_to(map_object)
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        control=True,
        show=False,
    ).add_to(map_object)

    for mission in MISSIONS:
        selected = mission.id == mission_id
        folium.CircleMarker(
            location=[mission.default_latitude, mission.default_longitude],
            radius=6 if selected else 3,
            color="#7fffe0" if selected else "#4f766b",
            fill=True,
            fill_color="#48e5c2" if selected else "#365a50",
            fill_opacity=0.85 if selected else 0.55,
            weight=2 if selected else 1,
            tooltip=f"{MISSION_UI[mission.id]['code']} · {mission.short_name} sample",
        ).add_to(map_object)

    risk = str(result.get("risk_level", "low")) if result else "low"
    color = RISK_HEX.get(risk, RISK_HEX["low"])
    radius_m = max(2_000.0, min(250_000.0, math.sqrt(area_hectares * 10_000.0 / math.pi)))
    score_text = f"Priority index: {float(result['score']):.1f}/100" if result else "Ready for analysis"
    safe_label = html.escape(location_label or "Selected target")
    popup = (
        f"<strong>{safe_label}</strong><br>"
        f"{MISSION_UI[mission_id]['plain_name']}<br>"
        f"{score_text}<br>Area: {area_hectares:,.1f} ha"
    )
    folium.Circle(
        location=[latitude, longitude],
        radius=radius_m,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.18,
        weight=3,
        tooltip=popup,
    ).add_to(map_object)
    folium.CircleMarker(
        location=[latitude, longitude],
        radius=8,
        color="#effff9",
        fill=True,
        fill_color=color,
        fill_opacity=1,
        weight=2,
        popup=folium.Popup(popup, max_width=320),
        tooltip="Selected research target",
    ).add_to(map_object)

    folium.LatLngPopup().add_to(map_object)
    Fullscreen(position="topright", title="Fullscreen map", title_cancel="Exit fullscreen").add_to(map_object)
    MiniMap(toggle_display=True, minimized=True, position="bottomright").add_to(map_object)
    folium.LayerControl(position="topright", collapsed=True).add_to(map_object)
    return map_object
