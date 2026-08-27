from __future__ import annotations

from typing import Any

from backend.app.models import MissionId


MISSION_UI: dict[MissionId, dict[str, Any]] = {
    MissionId.FLOOD: {
        "code": "M01",
        "plain_name": "Flood exposure",
        "question": "Could forecast river and rainfall conditions threaten this agricultural area?",
        "use_when": "Use before field verification, preparedness planning or crop-exposure assessment.",
        "cannot_prove": "It does not predict field-level flood depth or financial loss.",
        "next_actions": [
            "Compare the result with an official local flood warning or inundation map.",
            "Check crop stage, drainage routes and field elevation on the ground.",
            "Repeat the analysis when the river or rainfall forecast changes.",
        ],
    },
    MissionId.CROP_STRESS: {
        "code": "M02",
        "plain_name": "Crop stress",
        "question": "Which fields should be checked first for vegetation, moisture or heat stress?",
        "use_when": "Use to prioritize scouting with recent Sentinel-2 indices, your processed indices, and forecast weather.",
        "cannot_prove": "It cannot diagnose a pest, disease or nutrient deficiency.",
        "next_actions": [
            "Inspect the highest-priority fields and photograph visible symptoms.",
            "Compare NDVI/NDMI with the same crop and growth stage, not a universal threshold.",
            "Confirm moisture stress with a field probe or root-zone assessment.",
        ],
    },
    MissionId.LAND_CHANGE: {
        "code": "M03",
        "plain_name": "Land and wetland change",
        "question": "How did water, cropland and tree-cover shares change between two observations?",
        "use_when": "Use after producing quality-controlled class summaries from two comparable dates.",
        "cannot_prove": "Class percentages alone do not reveal the exact location or cause of change.",
        "next_actions": [
            "Inspect a pixel-level transition map for the largest class changes.",
            "Verify season, sensor, cloud mask and classification method are comparable.",
            "Ground-check locations that may represent wetland or tree-cover loss.",
        ],
    },
    MissionId.IRRIGATION: {
        "code": "M04",
        "plain_name": "Irrigation planning",
        "question": "How much irrigation water and pumping energy may be needed in seven days?",
        "use_when": "Use for preliminary irrigation scheduling and energy budgeting.",
        "cannot_prove": "It does not simulate root-zone storage, irrigation timing or pipe losses in detail.",
        "next_actions": [
            "Compare the estimate with soil-moisture readings before irrigating.",
            "Confirm the crop coefficient for the actual growth stage.",
            "Measure pump head and efficiency if energy cost is important.",
        ],
    },
    MissionId.CARBON: {
        "code": "M05",
        "plain_name": "Farm carbon screening",
        "question": "What is the Tier 1 greenhouse-gas footprint of the supplied farm activities?",
        "use_when": "Use to identify major emission categories and compare management scenarios.",
        "cannot_prove": "It is not an audited product footprint or national greenhouse-gas inventory.",
        "next_actions": [
            "Replace default factors with country- or system-specific factors when available.",
            "Check that the comparison uses the same boundary and time period.",
            "Add excluded sources before making a complete carbon claim.",
        ],
    },
    MissionId.FIRE_HEAT: {
        "code": "M06",
        "plain_name": "Fire and heat",
        "question": "Do heat, dryness, wind and thermal hotspots justify urgent verification?",
        "use_when": "Use to prioritize field checks and occupational heat precautions.",
        "cannot_prove": "A thermal hotspot does not identify cause, ownership or burned crop area.",
        "next_actions": [
            "Follow the responsible local fire and weather authorities.",
            "Verify each hotspot using recent imagery or a safe field observation.",
            "Review worker heat precautions and water availability.",
        ],
    },
}


STATUS_GUIDE = {
    "observed": "Derived from an observation or quality-controlled dataset.",
    "near-real-time": "Recently acquired information that may still be revised.",
    "forecast": "A prediction for future weather or river conditions.",
    "modelled": "Produced by a model or explicit screening assumption.",
    "calculated": "Calculated directly from stated inputs and equations.",
    "user-supplied": "Entered by the user; quality depends on the original measurement.",
    "demonstration": "Fallback or sample value. Do not cite it as an observation.",
    "unavailable": "The expected information could not be obtained.",
}


SAMPLE_STUDIES: dict[MissionId, dict[str, Any]] = {
    MissionId.FLOOD: {
        "name": "Worked example — floodplain crop exposure",
        "location": "Illustrative floodplain target",
        "latitude": 15.4,
        "longitude": 105.8,
        "area_hectares": 25_000.0,
        "parameters": {"crop_stage_sensitivity": 0.80, "drainage_vulnerability": 0.70},
        "ui": {},
    },
    MissionId.CROP_STRESS: {
        "name": "Worked example — vegetation and moisture stress",
        "location": "Illustrative irrigated crop district",
        "latitude": 30.7,
        "longitude": 75.8,
        "area_hectares": 8_000.0,
        "parameters": {"ndvi": 0.41, "ndmi": 0.13},
        "ui": {"index_source": "My processed indices"},
    },
    MissionId.LAND_CHANGE: {
        "name": "Worked example — wetland conversion screening",
        "location": "Illustrative wetland–cropland mosaic",
        "latitude": -18.3,
        "longitude": -57.5,
        "area_hectares": 50_000.0,
        "parameters": {
            "baseline_water_pct": 31.0,
            "current_water_pct": 24.5,
            "baseline_cropland_pct": 38.0,
            "current_cropland_pct": 45.0,
            "baseline_tree_pct": 22.0,
            "current_tree_pct": 18.0,
        },
        "ui": {},
    },
    MissionId.IRRIGATION: {
        "name": "Worked example — seven-day maize irrigation",
        "location": "Illustrative irrigated production area",
        "latitude": 29.9,
        "longitude": 31.2,
        "area_hectares": 120.0,
        "parameters": {
            "crop": "maize",
            "effective_rain_fraction": 0.80,
            "application_efficiency": 0.70,
            "pump_efficiency": 0.55,
            "total_dynamic_head_m": 18.0,
        },
        "ui": {},
    },
    MissionId.CARBON: {
        "name": "Worked example — mixed rice and livestock farm",
        "location": "Illustrative mixed farming system",
        "latitude": 41.8,
        "longitude": 12.4,
        "area_hectares": 500.0,
        "parameters": {
            "fertilizer_n_kg_ha": 110.0,
            "rice_area_hectares": 225.0,
            "rice_cultivation_days": 110.0,
            "rice_water_regime_factor": 1.0,
            "rice_organic_amendment_factor": 1.0,
            "diesel_litres": 32_500.0,
            "electricity_kwh": 25_000.0,
            "grid_kg_co2_per_kwh": 0.45,
            "livestock_head": 80.0,
            "enteric_kg_ch4_head_year": 47.0,
            "inventory_fraction_year": 1.0,
        },
        "ui": {},
    },
    MissionId.FIRE_HEAT: {
        "name": "Worked example — dry-season heat and hotspots",
        "location": "Illustrative dry agricultural landscape",
        "latitude": 37.3,
        "longitude": 23.7,
        "area_hectares": 10_000.0,
        "parameters": {
            "temperature_max_c": 39.0,
            "relative_humidity_pct": 32.0,
            "rain_7d_mm": 3.0,
            "wind_max_kmh": 31.0,
            "hotspot_count": 4,
        },
        "ui": {"use_observations": True},
    },
}
