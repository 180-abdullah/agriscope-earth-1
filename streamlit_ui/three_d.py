from __future__ import annotations

import math
from typing import Any

import pydeck as pdk

from backend.app.missions.catalog import MISSIONS
from backend.app.models import MissionId
from .content import MISSION_UI


RISK_RGB = {
    "low": [72, 229, 194],
    "moderate": [255, 189, 89],
    "high": [255, 132, 75],
    "severe": [255, 73, 92],
}


def build_operations_deck(
    mission_id: MissionId,
    latitude: float,
    longitude: float,
    area_hectares: float,
    result: dict[str, Any] | None,
) -> pdk.Deck:
    """Build a tactical 3D deck.gl view without copied project assets."""
    risk = str(result.get("risk_level", "low")) if result else "low"
    color = RISK_RGB.get(risk, RISK_RGB["low"])
    score = float(result.get("score", 12.0)) if result else 12.0
    radius_m = max(1_200.0, min(180_000.0, math.sqrt(area_hectares * 10_000.0 / math.pi)))
    target = [{
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius_m,
        "elevation": max(2_000.0, score * 1_900.0),
        "color": color,
        "color4": color + [185],
        "label": f"{MISSION_UI[mission_id]['code']} · {MISSION_UI[mission_id]['plain_name']}",
        "score": score,
    }]
    mission_hubs = [
        {
            "latitude": item.default_latitude,
            "longitude": item.default_longitude,
            "label": f"{MISSION_UI[item.id]['code']} · {item.short_name}",
            "selected": item.id == mission_id,
            "score": "mission hub",
        }
        for item in MISSIONS
    ]
    rings = [
        {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius_m * multiplier,
            "color": color + [max(35, 150 - index * 35)],
        }
        for index, multiplier in enumerate((1.0, 1.65, 2.35))
    ]
    arcs = [
        {
            "source": [item.default_longitude, item.default_latitude],
            "target": [longitude, latitude],
            "selected": item.id == mission_id,
        }
        for item in MISSIONS
        if item.id != mission_id
    ]

    layers = [
        pdk.Layer(
            "ArcLayer",
            arcs,
            get_source_position="source",
            get_target_position="target",
            get_source_color=[38, 118, 100, 90],
            get_target_color=color + [165],
            get_width=1.2,
            great_circle=True,
            pickable=False,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            rings,
            get_position="[longitude, latitude]",
            get_radius="radius",
            get_fill_color=[0, 0, 0, 0],
            get_line_color="color",
            stroked=True,
            filled=False,
            line_width_min_pixels=1,
            pickable=False,
        ),
        pdk.Layer(
            "ColumnLayer",
            target,
            get_position="[longitude, latitude]",
            get_elevation="elevation",
            get_fill_color="color4",
            radius=max(650.0, radius_m * 0.16),
            disk_resolution=48,
            elevation_scale=1,
            extruded=True,
            pickable=True,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            mission_hubs,
            get_position="[longitude, latitude]",
            get_radius="selected ? 70000 : 35000",
            get_fill_color="selected ? [127,255,224,220] : [45,114,95,145]",
            get_line_color=[225, 255, 247, 180],
            line_width_min_pixels=1,
            stroked=True,
            pickable=True,
        ),
    ]
    view = pdk.ViewState(
        latitude=latitude,
        longitude=longitude,
        zoom=4.2,
        pitch=52,
        bearing=-18,
    )
    return pdk.Deck(
        layers=layers,
        initial_view_state=view,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={
            "html": "<b>{label}</b><br/>Priority index: {score}",
            "style": {"backgroundColor": "#061a14", "color": "#eafff8", "border": "1px solid #58efc9"},
        },
    )
