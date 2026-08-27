from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from backend.app.missions import run_mission
from backend.app.missions.catalog import MISSIONS, MISSION_BY_ID
from backend.app.models import AnalysisRequest, MissionId
from streamlit_ui.content import MISSION_UI, SAMPLE_STUDIES, STATUS_GUIDE
from streamlit_ui.exports import build_research_package, research_note, result_csv
from streamlit_ui.geocoding import search_places
from streamlit_ui.maps import build_research_map
from streamlit_ui.three_d import build_operations_deck


st.set_page_config(
    page_title="AgriScope Earth — Research Screening",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_styles() -> None:
    style_path = Path(__file__).parent / ".streamlit" / "style.css"
    st.markdown(f"<style>{style_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def configure_optional_secrets() -> None:
    try:
        firms_key = str(st.secrets.get("FIRMS_MAP_KEY", "")).strip()
    except (FileNotFoundError, KeyError):
        firms_key = ""
    if firms_key:
        os.environ["FIRMS_MAP_KEY"] = firms_key


@st.cache_data(ttl=600, show_spinner=False)
def execute_analysis(payload_json: str) -> dict[str, Any]:
    request = AnalysisRequest.model_validate_json(payload_json)
    return asyncio.run(run_mission(request)).model_dump(mode="json")


@st.cache_data(ttl=86_400, show_spinner=False)
def cached_place_search(query: str) -> list[dict[str, Any]]:
    return search_places(query)


def pkey(mission_id: MissionId, name: str) -> str:
    return f"p_{mission_id.value}_{name}"


def set_target(mission_id: MissionId, latitude: float, longitude: float, label: str) -> None:
    st.session_state[f"lat_{mission_id.value}"] = float(latitude)
    st.session_state[f"lon_{mission_id.value}"] = float(longitude)
    st.session_state[f"location_{mission_id.value}"] = label


def load_worked_example(mission_id: MissionId) -> None:
    example = SAMPLE_STUDIES[mission_id]
    set_target(mission_id, example["latitude"], example["longitude"], example["location"])
    st.session_state[f"area_{mission_id.value}"] = float(example["area_hectares"])
    st.session_state[f"name_{mission_id.value}"] = example["name"]
    for key, value in example["parameters"].items():
        st.session_state[pkey(mission_id, key)] = value
    for key, value in example.get("ui", {}).items():
        st.session_state[pkey(mission_id, key)] = value
    st.session_state["auto_run_mission"] = mission_id.value


def optional_override(
    mission_id: MissionId,
    label: str,
    parameter: str,
    default: float,
    **kwargs: Any,
) -> dict[str, float]:
    enabled = st.checkbox(
        f"Use my {label.lower()}",
        key=pkey(mission_id, f"use_{parameter}"),
        help="Turn this on only when you have a measured or independently prepared value.",
    )
    if not enabled:
        return {}
    value = st.number_input(
        label,
        value=float(default),
        key=pkey(mission_id, parameter),
        **kwargs,
    )
    return {parameter: float(value)}


def mission_inputs(mission_id: MissionId, area_hectares: float, research_mode: bool) -> dict[str, Any]:
    parameters: dict[str, Any] = {}
    title = "RESEARCH PARAMETERS" if research_mode else "GUIDED INPUTS"
    with st.sidebar.expander(title, expanded=True):
        if mission_id == MissionId.FLOOD:
            st.caption("Describe how sensitive the selected farming area is if high water occurs.")
            parameters["crop_stage_sensitivity"] = st.slider(
                "Crop-stage sensitivity",
                0.0,
                1.0,
                0.75,
                0.05,
                key=pkey(mission_id, "crop_stage_sensitivity"),
                help="0 = relatively tolerant stage; 1 = highly sensitive stage such as establishment or flowering.",
            )
            parameters["drainage_vulnerability"] = st.slider(
                "Drainage vulnerability",
                0.0,
                1.0,
                0.55,
                0.05,
                key=pkey(mission_id, "drainage_vulnerability"),
                help="0 = rapid drainage; 1 = prolonged waterlogging is likely.",
            )
            if research_mode:
                parameters |= optional_override(
                    mission_id, "Discharge ratio", "discharge_ratio", 1.2,
                    min_value=0.0, max_value=10.0, step=0.1,
                )
                parameters |= optional_override(
                    mission_id, "7-day rainfall (mm)", "rain_7d_mm", 45.0,
                    min_value=0.0, max_value=2_000.0, step=1.0,
                )

        elif mission_id == MissionId.CROP_STRESS:
            st.caption("Choose where the vegetation evidence should come from. No source is silently substituted.")
            index_source = st.radio(
                "Vegetation evidence",
                ["Live Sentinel-2", "My processed indices", "Demonstration only"],
                key=pkey(mission_id, "index_source"),
                help="Live mode searches recent Sentinel-2 Level-2A scenes and applies the documented quality mask.",
            )
            if index_source == "Live Sentinel-2":
                parameters["use_live_sentinel"] = True
                st.info("The run may take 10–40 seconds while a bounded satellite sample is read. Acquisition metadata will appear in the result.")
                if research_mode:
                    parameters["sentinel_lookback_days"] = st.slider(
                        "Satellite lookback (days)", 30, 365, 120, 15,
                        key=pkey(mission_id, "sentinel_lookback_days"),
                    )
                    parameters["sentinel_max_cloud_pct"] = st.slider(
                        "Maximum scene cloud metadata (%)", 0, 80, 35, 5,
                        key=pkey(mission_id, "sentinel_max_cloud_pct"),
                        help="This filter uses whole-scene metadata. The engine separately reports the valid fraction over the target sample.",
                    )
            elif index_source == "My processed indices":
                parameters["use_live_sentinel"] = False
                parameters["ndvi"] = st.slider(
                    "NDVI", -1.0, 1.0, 0.55, 0.01, key=pkey(mission_id, "ndvi"),
                    help="Vegetation greenness index. Interpret against the same crop and growth stage.",
                )
                parameters["ndmi"] = st.slider(
                    "NDMI", -1.0, 1.0, 0.22, 0.01, key=pkey(mission_id, "ndmi"),
                    help="Canopy moisture proxy from processed imagery.",
                )
            else:
                parameters["use_live_sentinel"] = False
                st.warning("Demonstration values teach the workflow only. The result will be blocked from observational interpretation.")
            if research_mode:
                parameters |= optional_override(
                    mission_id, "Surface soil moisture (m³/m³)", "soil_moisture_m3_m3", 0.24,
                    min_value=0.0, max_value=0.7, step=0.01,
                )
                parameters |= optional_override(
                    mission_id, "Maximum temperature (°C)", "temperature_max_c", 33.0,
                    min_value=-40.0, max_value=65.0, step=0.5,
                )
                parameters |= optional_override(
                    mission_id, "7-day rainfall (mm)", "rain_7d_mm", 18.0,
                    min_value=0.0, max_value=2_000.0, step=1.0,
                )

        elif mission_id == MissionId.LAND_CHANGE:
            st.caption("Use comparable, quality-controlled classified summaries. Values are percent of the analysis area.")
            entry_method = st.radio(
                "Class-summary entry",
                ["Form", "Upload two-period CSV"],
                horizontal=True,
                key=pkey(mission_id, "entry_method"),
            )
            template_csv = "period,water_pct,cropland_pct,tree_pct\nbaseline,28,42,24\ncurrent,23,48,19\n"
            st.download_button(
                "DOWNLOAD CSV TEMPLATE",
                template_csv,
                file_name="agriscope-land-change-template.csv",
                mime="text/csv",
                width="stretch",
            )
            if entry_method == "Upload two-period CSV":
                uploaded = st.file_uploader(
                    "Upload completed CSV",
                    type=["csv"],
                    key=pkey(mission_id, "class_csv"),
                    help="Required rows: baseline and current. Required columns: period, water_pct, cropland_pct, tree_pct.",
                )
                if uploaded is None:
                    st.info("Download the template, complete both rows, then upload it here.")
                else:
                    try:
                        frame = pd.read_csv(uploaded)
                        required = {"period", "water_pct", "cropland_pct", "tree_pct"}
                        if not required.issubset(frame.columns):
                            raise ValueError(f"Missing columns: {', '.join(sorted(required - set(frame.columns)))}")
                        normalized = frame.assign(period=frame["period"].astype(str).str.strip().str.lower()).set_index("period")
                        if not {"baseline", "current"}.issubset(normalized.index):
                            raise ValueError("The period column must contain baseline and current rows.")
                        for period in ("baseline", "current"):
                            for source_name, parameter_name in (
                                ("water_pct", "water_pct"),
                                ("cropland_pct", "cropland_pct"),
                                ("tree_pct", "tree_pct"),
                            ):
                                value = float(normalized.loc[period, source_name])
                                if not 0 <= value <= 100:
                                    raise ValueError(f"{period} {source_name} must be between 0 and 100.")
                                parameters[f"{period}_{parameter_name}"] = value
                        parameters["class_data_confirmed"] = True
                        st.success("Two-period class summary validated and loaded.")
                        st.dataframe(normalized.reset_index(), hide_index=True, width="stretch")
                    except Exception as exc:
                        st.error(f"The CSV could not be used: {exc}")
            else:
                left, right = st.columns(2)
                with left:
                    parameters["baseline_water_pct"] = st.number_input(
                        "Baseline water %", 0.0, 100.0, 28.0, 0.5, key=pkey(mission_id, "baseline_water_pct")
                    )
                    parameters["baseline_cropland_pct"] = st.number_input(
                        "Baseline crop %", 0.0, 100.0, 42.0, 0.5, key=pkey(mission_id, "baseline_cropland_pct")
                    )
                    parameters["baseline_tree_pct"] = st.number_input(
                        "Baseline tree %", 0.0, 100.0, 24.0, 0.5, key=pkey(mission_id, "baseline_tree_pct")
                    )
                with right:
                    parameters["current_water_pct"] = st.number_input(
                        "Current water %", 0.0, 100.0, 23.0, 0.5, key=pkey(mission_id, "current_water_pct")
                    )
                    parameters["current_cropland_pct"] = st.number_input(
                        "Current crop %", 0.0, 100.0, 48.0, 0.5, key=pkey(mission_id, "current_cropland_pct")
                    )
                    parameters["current_tree_pct"] = st.number_input(
                        "Current tree %", 0.0, 100.0, 19.0, 0.5, key=pkey(mission_id, "current_tree_pct")
                    )
                parameters["class_data_confirmed"] = st.checkbox(
                    "I confirm these values come from comparable classified observations",
                    key=pkey(mission_id, "class_data_confirmed"),
                    help="Leave this off when exploring the interface. Confirm only when you can document the products, dates, masks and classification accuracy.",
                )
            class_keys = {
                "baseline_water_pct", "baseline_cropland_pct", "baseline_tree_pct",
                "current_water_pct", "current_cropland_pct", "current_tree_pct",
            }
            if class_keys.issubset(parameters):
                baseline_total = parameters["baseline_water_pct"] + parameters["baseline_cropland_pct"] + parameters["baseline_tree_pct"]
                current_total = parameters["current_water_pct"] + parameters["current_cropland_pct"] + parameters["current_tree_pct"]
                if baseline_total > 100 or current_total > 100:
                    st.warning("Water + cropland + tree shares exceed 100%. Check whether the classes overlap.")

        elif mission_id == MissionId.IRRIGATION:
            st.caption("The engine combines forecast ET₀ and rainfall with crop and system assumptions.")
            parameters["crop"] = st.selectbox(
                "Crop",
                ["maize", "rice", "wheat", "soybean", "cotton", "potato", "vegetables", "orchard"],
                key=pkey(mission_id, "crop"),
            )
            parameters["effective_rain_fraction"] = st.slider(
                "Effective-rain fraction", 0.0, 1.0, 0.80, 0.05,
                key=pkey(mission_id, "effective_rain_fraction"),
                help="Share of rainfall assumed available to the crop after runoff and other losses.",
            )
            parameters["application_efficiency"] = st.slider(
                "Application efficiency", 0.10, 1.0, 0.70, 0.05,
                key=pkey(mission_id, "application_efficiency"),
                help="Fraction of applied irrigation water that reaches the target root zone.",
            )
            parameters["pump_efficiency"] = st.slider(
                "Pump efficiency", 0.10, 1.0, 0.55, 0.05,
                key=pkey(mission_id, "pump_efficiency"),
            )
            parameters["total_dynamic_head_m"] = st.number_input(
                "Total dynamic head (m)", 0.0, 500.0, 18.0, 1.0,
                key=pkey(mission_id, "total_dynamic_head_m"),
                help="Vertical lift plus pressure and friction equivalent used in the hydraulic-energy estimate.",
            )
            if research_mode:
                parameters |= optional_override(
                    mission_id, "Crop coefficient", "crop_coefficient", 1.05,
                    min_value=0.1, max_value=2.0, step=0.05,
                )
                parameters |= optional_override(
                    mission_id, "7-day reference ET₀ (mm)", "et0_7d_mm", 34.0,
                    min_value=0.0, max_value=500.0, step=1.0,
                )
                parameters |= optional_override(
                    mission_id, "7-day rainfall (mm)", "rain_7d_mm", 12.0,
                    min_value=0.0, max_value=2_000.0, step=1.0,
                )

        elif mission_id == MissionId.CARBON:
            st.caption("Enter activity data for one consistent inventory period.")
            parameters["fertilizer_n_kg_ha"] = st.number_input(
                "Fertilizer N (kg/ha)", 0.0, 1_000.0, 110.0, 5.0,
                key=pkey(mission_id, "fertilizer_n_kg_ha"),
            )
            parameters["rice_area_hectares"] = st.number_input(
                "Rice area (ha)", 0.0, 10_000_000.0, float(min(area_hectares * 0.45, 10_000_000.0)), 10.0,
                key=pkey(mission_id, "rice_area_hectares"),
            )
            parameters["rice_cultivation_days"] = st.number_input(
                "Rice cultivation (days)", 0.0, 365.0, 110.0, 5.0,
                key=pkey(mission_id, "rice_cultivation_days"),
            )
            parameters["diesel_litres"] = st.number_input(
                "Diesel (L)", 0.0, 1_000_000_000.0, float(area_hectares * 65), 100.0,
                key=pkey(mission_id, "diesel_litres"),
            )
            parameters["electricity_kwh"] = st.number_input(
                "Electricity (kWh)", 0.0, 1_000_000_000.0, 0.0, 100.0,
                key=pkey(mission_id, "electricity_kwh"),
            )
            parameters["livestock_head"] = st.number_input(
                "Livestock head", 0.0, 100_000_000.0, 0.0, 10.0,
                key=pkey(mission_id, "livestock_head"),
            )
            if research_mode:
                parameters["rice_water_regime_factor"] = st.number_input(
                    "Rice water-regime factor", 0.0, 5.0, 1.0, 0.05,
                    key=pkey(mission_id, "rice_water_regime_factor"),
                )
                parameters["rice_organic_amendment_factor"] = st.number_input(
                    "Rice organic-amendment factor", 0.0, 5.0, 1.0, 0.05,
                    key=pkey(mission_id, "rice_organic_amendment_factor"),
                )
                parameters["grid_kg_co2_per_kwh"] = st.number_input(
                    "Grid factor (kg CO₂/kWh)", 0.0, 3.0, 0.45, 0.01,
                    key=pkey(mission_id, "grid_kg_co2_per_kwh"),
                )
                parameters["enteric_kg_ch4_head_year"] = st.number_input(
                    "Enteric factor (kg CH₄/head/year)", 0.0, 500.0, 47.0, 1.0,
                    key=pkey(mission_id, "enteric_kg_ch4_head_year"),
                )
                parameters["inventory_fraction_year"] = st.slider(
                    "Inventory fraction of year", 0.0, 1.0, 1.0, 0.05,
                    key=pkey(mission_id, "inventory_fraction_year"),
                )

        elif mission_id == MissionId.FIRE_HEAT:
            st.caption("Use automatic weather and optional FIRMS detections, or enter verified observations.")
            use_observations = st.checkbox(
                "I have verified local observations",
                key=pkey(mission_id, "use_observations"),
            )
            if use_observations:
                parameters["hotspot_count"] = st.number_input(
                    "Verified hotspot count", 0, 100_000, 0, 1, key=pkey(mission_id, "hotspot_count")
                )
                parameters["temperature_max_c"] = st.number_input(
                    "Maximum temperature (°C)", -40.0, 65.0, 37.0, 0.5,
                    key=pkey(mission_id, "temperature_max_c"),
                )
                parameters["relative_humidity_pct"] = st.number_input(
                    "Relative humidity (%)", 0.0, 100.0, 35.0, 1.0,
                    key=pkey(mission_id, "relative_humidity_pct"),
                )
                parameters["rain_7d_mm"] = st.number_input(
                    "7-day rainfall (mm)", 0.0, 2_000.0, 5.0, 1.0,
                    key=pkey(mission_id, "rain_7d_mm"),
                )
                parameters["wind_max_kmh"] = st.number_input(
                    "Maximum wind (km/h)", 0.0, 350.0, 28.0, 1.0,
                    key=pkey(mission_id, "wind_max_kmh"),
                )
            elif research_mode:
                st.info("Configure FIRMS_MAP_KEY in Streamlit secrets to request near-real-time thermal detections.")
    return parameters


def trust_profile(statuses: list[str]) -> tuple[str, str, str]:
    status_set = set(statuses)
    if "demonstration" in status_set:
        return (
            "DEMONSTRATION PRESENT",
            "bad",
            "One or more inputs are fallback examples. Explore the workflow, but do not cite the result as an observation.",
        )
    if "unavailable" in status_set:
        return (
            "EVIDENCE INCOMPLETE",
            "bad",
            "An expected source was unavailable. Treat the result as provisional and verify the missing evidence.",
        )
    if "user-supplied" in status_set and ({"forecast", "near-real-time", "observed"} & status_set):
        return (
            "MIXED EVIDENCE",
            "good",
            "The result combines traceable external information with your inputs. Verify the quality and dates of both.",
        )
    if {"forecast", "near-real-time", "observed"} & status_set:
        return (
            "LIVE-ASSISTED SCREENING",
            "good",
            "A current or forecast source contributed to the result. It remains a screening output, not an official warning.",
        )
    return (
        "CALCULATED SCREENING",
        "",
        "The result is calculated from stated inputs and assumptions. Its quality depends on those inputs.",
    )


def remember_result(result: dict[str, Any], request: dict[str, Any]) -> None:
    history = list(st.session_state.get("analysis_history", []))
    if not any(item["analysis_id"] == result["analysis_id"] for item in history):
        history.insert(
            0,
            {
                "analysis_id": result["analysis_id"],
                "study": request.get("name") or "Untitled screening",
                "mission": result["mission"],
                "latitude": result["coordinates"]["latitude"],
                "longitude": result["coordinates"]["longitude"],
                "score": result["score"],
                "risk": result["risk_level"],
                "confidence_pct": round(result["confidence"] * 100),
                "generated_at": result["generated_at"],
            },
        )
    st.session_state["analysis_history"] = history[:8]


def render_result(result: dict[str, Any], request: dict[str, Any], research_mode: bool) -> None:
    risk = str(result["risk_level"])
    trust_title, trust_class, trust_message = trust_profile(result["data_status"])
    st.markdown(f'<div class="ase-kicker">ANALYSIS COMPLETE · {result["analysis_id"][:8]}</div>', unsafe_allow_html=True)
    st.subheader(result["title"])

    score_col, risk_col, confidence_col, area_col = st.columns(4)
    score_col.metric("Priority index", f'{result["score"]:.1f} / 100')
    risk_col.metric("Priority class", risk.upper())
    confidence_col.metric("Evidence completeness", f'{result["confidence"] * 100:.0f}%')
    area_col.metric("Analysis area", f'{result["area_hectares"]:,.0f} ha')
    st.progress(float(result["score"]) / 100.0, text="Screening priority — this is not a probability or measured loss")
    st.caption("Evidence completeness is a rule-based traceability indicator, not a statistical confidence interval or model accuracy estimate.")

    st.markdown(
        f'<div class="ase-trust {trust_class}"><strong>{trust_title}</strong><br>{trust_message}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="ase-brief"><strong>{risk.upper()} PRIORITY.</strong> {result["summary"]}</div>', unsafe_allow_html=True)

    overview_tab, evidence_tab, methods_tab, export_tab, history_tab = st.tabs(
        ["Overview", "Evidence & trust", "Inputs & method", "Export package", "Session history"]
    )

    with overview_tab:
        metric_rows = [
            {
                "Indicator": item["label"],
                "Value": item["value"],
                "Unit": item["unit"],
                "Interpretation": item["interpretation"],
            }
            for item in result["metrics"]
        ]
        st.dataframe(pd.DataFrame(metric_rows), hide_index=True, width="stretch")
        action_col, caveat_col = st.columns(2, gap="large")
        with action_col:
            st.markdown("#### Recommended verification steps")
            for index, action in enumerate(MISSION_UI[MissionId(result["mission"])]["next_actions"], start=1):
                st.markdown(f"{index}. {action}")
        with caveat_col:
            st.markdown("#### Limitations to report")
            for caveat in result["caveats"]:
                st.markdown(f"- {caveat}")

    with evidence_tab:
        st.markdown("#### Evidence status")
        statuses = "".join(f'<span class="ase-pill">{status}</span>' for status in result["data_status"])
        st.markdown(statuses, unsafe_allow_html=True)
        for status in result["data_status"]:
            st.markdown(f"- **{status}:** {STATUS_GUIDE.get(status, 'Status recorded by the analysis engine.')}")
        st.caption(f'Methodology {result["methodology_version"]} · Generated {result["generated_at"]}')
        st.markdown("#### Source register")
        for source in result["sources"]:
            resolution = " · ".join(
                item for item in [source.get("spatial_resolution"), source.get("temporal_resolution")] if item
            )
            trace_items = [
                f"Identifier: {source['identifier']}" if source.get("identifier") else "",
                f"Acquired: {source['acquisition_datetime']}" if source.get("acquisition_datetime") else "",
                f"Accessed: {source['accessed_at']}" if source.get("accessed_at") else "",
                f"Terms: {source['license']}" if source.get("license") else "",
            ]
            trace = " · ".join(item for item in trace_items if item)
            source_heading = (
                f'<a href="{source["url"]}" target="_blank">{source["name"]} ↗</a>'
                if source.get("url")
                else f'<strong>{source["name"]}</strong>'
            )
            st.markdown(
                f"""
                <div class="ase-source">
                  {source_heading}
                  <div>{source['role']}</div>
                  <div class="ase-meta">Status: {source['status']}{(' · ' + resolution) if resolution else ''}</div>
                  <div class="ase-meta">{source.get('note') or ''}</div>
                  <div class="ase-meta">{trace}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with methods_tab:
        st.markdown("#### Reproducible input record")
        input_rows = [{"Input": key, "Value": value} for key, value in request.get("parameters", {}).items()]
        if input_rows:
            st.dataframe(pd.DataFrame(input_rows), hide_index=True, width="stretch")
        else:
            st.info("No optional mission parameters were supplied; the engine used documented defaults and available public data.")
        st.markdown(
            f"**Target:** `{request['latitude']}, {request['longitude']}`  \n"
            f"**Area:** `{request['area_hectares']} ha`  \n"
            f"**Study:** `{request.get('name') or 'Untitled screening'}`"
        )
        with st.expander("How to report this result"):
            st.write(
                "Report the mission, coordinates, area, analysis date, methodology version, every input, data-status labels, "
                "source access dates and stated limitations. Do not present the priority index as a probability."
            )
        if research_mode:
            st.markdown("#### Complete machine-readable record")
            st.code(json.dumps(build_research_package(result, request), indent=2), language="json")

    with export_tab:
        export_base = f"agriscope-{result['mission']}-{result['analysis_id'][:8]}"
        package = build_research_package(result, request)
        feature = dict(result["geometry"])
        feature["properties"] = {
            **feature.get("properties", {}),
            "analysis_id": result["analysis_id"],
            "mission": result["mission"],
            "score": result["score"],
            "risk_level": result["risk_level"],
            "confidence": result["confidence"],
            "data_status": result["data_status"],
        }
        geojson = {"type": "FeatureCollection", "features": [feature]}
        json_col, csv_col, geo_col, note_col = st.columns(4)
        json_col.download_button(
            "JSON research record", json.dumps(package, indent=2),
            file_name=f"{export_base}.json", mime="application/json", width="stretch",
        )
        csv_col.download_button(
            "CSV indicators", result_csv(result, request),
            file_name=f"{export_base}.csv", mime="text/csv", width="stretch",
        )
        geo_col.download_button(
            "GeoJSON target", json.dumps(geojson, indent=2),
            file_name=f"{export_base}.geojson", mime="application/geo+json", width="stretch",
        )
        note_col.download_button(
            "Markdown research note", research_note(result, request),
            file_name=f"{export_base}.md", mime="text/markdown", width="stretch",
        )
        st.caption("Exports preserve the analysis identifier, methodology version, evidence labels and supplied inputs.")

    with history_tab:
        history = st.session_state.get("analysis_history", [])
        if history:
            history_frame = pd.DataFrame(history)
            st.dataframe(history_frame, hide_index=True, width="stretch")
            st.download_button(
                "Download session comparison",
                history_frame.to_csv(index=False),
                file_name="agriscope-session-history.csv",
                mime="text/csv",
            )
            st.caption("Session history is temporary and disappears when the Streamlit session ends.")
        else:
            st.info("Run more than one analysis to build a temporary comparison table.")


load_styles()
configure_optional_secrets()

st.sidebar.markdown('<div class="ase-kicker">AGRISCOPE // EARTH</div>', unsafe_allow_html=True)
st.sidebar.caption("Transparent global research screening")

interface_mode = st.sidebar.radio(
    "INTERFACE MODE",
    ["Guided", "Research"],
    horizontal=True,
    key="interface_mode",
    help="Guided mode explains the essentials. Research mode exposes additional overrides and full records.",
)
research_mode = interface_mode == "Research"

mission_label_to_id = {
    f"{MISSION_UI[mission.id]['code']}  {MISSION_UI[mission.id]['plain_name']}": mission.id for mission in MISSIONS
}
mission_labels = list(mission_label_to_id)
selected_label = st.sidebar.radio(
    "CHOOSE A RESEARCH QUESTION",
    mission_labels,
    index=3,
    key="mission_selector",
)
mission_id = mission_label_to_id[selected_label]
mission = MISSION_BY_ID[mission_id]
mission_copy = MISSION_UI[mission_id]

st.sidebar.markdown(f"**{mission_copy['question']}**")
st.sidebar.caption(mission_copy["use_when"])

st.sidebar.button(
    "▶ RUN WORKED EXAMPLE",
    on_click=load_worked_example,
    args=(mission_id,),
    width="stretch",
    help="Loads a transparent example for the selected mission and runs it immediately.",
)

st.sidebar.markdown("---")
st.sidebar.markdown('<div class="ase-kicker">1 · FIND THE TARGET</div>', unsafe_allow_html=True)
place_query = st.sidebar.text_input(
    "Search place worldwide",
    placeholder="City, district or region",
    key="place_query",
)
search_clicked = st.sidebar.button("SEARCH PLACE", width="stretch")
if search_clicked:
    try:
        with st.spinner("Searching global places…"):
            st.session_state["place_matches"] = cached_place_search(place_query)
        if not st.session_state["place_matches"]:
            st.sidebar.warning("No place found. Try a larger city, district or region name.")
    except Exception:
        st.session_state["place_matches"] = []
        st.sidebar.warning("Place search is temporarily unavailable. Enter coordinates or click the map.")

place_matches = st.session_state.get("place_matches", [])
if place_matches:
    match_labels = [item["label"] for item in place_matches]
    selected_match_label = st.sidebar.selectbox("Search results", match_labels)
    selected_match = place_matches[match_labels.index(selected_match_label)]
    st.sidebar.button(
        "USE SELECTED PLACE",
        on_click=set_target,
        args=(mission_id, selected_match["latitude"], selected_match["longitude"], selected_match["label"]),
        width="stretch",
    )

latitude = st.sidebar.number_input(
    "Latitude",
    min_value=-90.0,
    max_value=90.0,
    value=float(mission.default_latitude),
    step=0.1,
    format="%.4f",
    key=f"lat_{mission_id.value}",
)
longitude = st.sidebar.number_input(
    "Longitude",
    min_value=-180.0,
    max_value=180.0,
    value=float(mission.default_longitude),
    step=0.1,
    format="%.4f",
    key=f"lon_{mission_id.value}",
)
location_label = st.session_state.get(f"location_{mission_id.value}", "Coordinate target")

st.sidebar.markdown('<div class="ase-kicker">2 · DEFINE THE STUDY</div>', unsafe_allow_html=True)
area_hectares = st.sidebar.number_input(
    "Area (hectares)",
    min_value=0.1,
    max_value=10_000_000.0,
    value=float(mission.default_area_hectares),
    step=100.0,
    key=f"area_{mission_id.value}",
)
analysis_name = st.sidebar.text_input(
    "Study name",
    placeholder="Example: North farm irrigation screen",
    max_chars=120,
    key=f"name_{mission_id.value}",
)
parameters = mission_inputs(mission_id, float(area_hectares), research_mode)

st.sidebar.markdown('<div class="ase-kicker">3 · RUN AND VERIFY</div>', unsafe_allow_html=True)
run_clicked = st.sidebar.button("RUN ANALYSIS", type="primary", width="stretch")
st.sidebar.caption("Public APIs are attempted when relevant. Fallback values are always labelled demonstration.")

auto_run = st.session_state.pop("auto_run_mission", None) == mission_id.value
if run_clicked or auto_run:
    request_model = AnalysisRequest(
        mission=mission_id,
        latitude=float(latitude),
        longitude=float(longitude),
        area_hectares=float(area_hectares),
        name=analysis_name or None,
        parameters=parameters,
    )
    try:
        with st.spinner("Acquiring evidence and running the Python research engine…"):
            result = execute_analysis(request_model.model_dump_json())
        request_record = request_model.model_dump(mode="json")
        st.session_state["analysis"] = result
        st.session_state["analysis_request"] = request_record
        st.session_state["analysis_mission"] = mission_id.value
        remember_result(result, request_record)
    except Exception as exc:
        st.error(f"The analysis could not complete. Check the inputs and try again. Technical detail: {exc}")

current_result = st.session_state.get("analysis")
current_request = st.session_state.get("analysis_request")
if st.session_state.get("analysis_mission") != mission_id.value:
    current_result = None
    current_request = None

st.markdown('<div class="ase-kicker">GLOBAL AGRICULTURE + ENVIRONMENT</div>', unsafe_allow_html=True)
st.markdown('<div class="ase-title">AGRISCOPE // EARTH</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="ase-subtitle">A real-data research screening workbench for agriculture and environmental monitoring. Choose a question, target any location, inspect every evidence receipt, and export a reproducible record for verification.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="ase-step-grid">
      <div class="ase-step"><b>01 · QUESTION</b><span>Choose one of six research missions.</span></div>
      <div class="ase-step"><b>02 · EVIDENCE</b><span>Search a place, click the map or enter coordinates.</span></div>
      <div class="ase-step"><b>03 · VERIFY</b><span>Run the model, inspect trust labels, then export.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

map_col, brief_col = st.columns([1.62, 0.78], gap="large")
with map_col:
    st.markdown(f'<div class="ase-kicker">{mission_copy["code"]} · EARTH OPERATIONS VIEW</div>', unsafe_allow_html=True)
    reliable_tab, operations_tab = st.tabs(["Reliable target map", "3D operations view"])
    with reliable_tab:
        map_object = build_research_map(
            mission_id,
            float(latitude),
            float(longitude),
            float(area_hectares),
            current_result,
            location_label,
        )
        map_state = st_folium(
            map_object,
            height=500,
            width=None,
            returned_objects=["last_clicked"],
            key=f"map_{mission_id.value}_{round(float(latitude), 4)}_{round(float(longitude), 4)}",
        )
        clicked_point = map_state.get("last_clicked") if map_state else None
        if clicked_point:
            click_lat = float(clicked_point["lat"])
            click_lon = float(clicked_point["lng"])
            st.button(
                f"USE MAP POINT · {click_lat:.4f}, {click_lon:.4f}",
                on_click=set_target,
                args=(mission_id, click_lat, click_lon, "Map-selected target"),
                width="stretch",
            )
        st.caption("Click anywhere to reveal coordinates, then use the button to make that point the research target. This Leaflet view works without WebGL.")
    with operations_tab:
        st.pydeck_chart(
            build_operations_deck(
                mission_id,
                float(latitude),
                float(longitude),
                float(area_hectares),
                current_result,
            ),
            height=500,
            width="stretch",
        )
        st.caption("A God’s-Eye-inspired tactical view built from original layers and styling. If WebGL is unavailable, use the reliable target map.")

with brief_col:
    st.markdown(f'<div class="ase-kicker">MISSION BRIEF · {mission_copy["code"]}</div>', unsafe_allow_html=True)
    st.subheader(mission_copy["plain_name"])
    st.markdown(f'<div class="ase-brief">{mission_copy["question"]}</div>', unsafe_allow_html=True)
    st.markdown(f"**Use it when**  \n{mission_copy['use_when']}")
    st.markdown(f"**It cannot prove**  \n{mission_copy['cannot_prove']}")
    st.markdown(f"**Target**  `{location_label}`")
    st.markdown(f"**Coordinates**  `{latitude:.4f}, {longitude:.4f}`")
    st.markdown(f"**Area**  `{area_hectares:,.1f} ha`")
    if current_result:
        trust_title, trust_class, _ = trust_profile(current_result["data_status"])
        st.markdown(f'<div class="ase-trust {trust_class}"><strong>{trust_title}</strong><br>Result synchronized with this mission and target.</div>', unsafe_allow_html=True)
    else:
        st.info("Start quickly with RUN WORKED EXAMPLE, or enter your own target and inputs in the sidebar.")
    with st.expander("Research-use boundary"):
        st.write(
            "AgriScope supports screening and prioritization. It does not replace field measurements, official warnings, "
            "audited greenhouse-gas inventories or professional agronomic advice."
        )

st.markdown("---")
if current_result and current_request:
    render_result(current_result, current_request, research_mode)
else:
    st.markdown('<div class="ase-kicker">START WITH A WORKED EXAMPLE</div>', unsafe_allow_html=True)
    st.subheader("A useful result is one click away")
    st.write(
        "The default Irrigation mission is the clearest introduction. Click **RUN WORKED EXAMPLE** in the sidebar to load a documented sample, run the engine and see how evidence labels, indicators and exports work."
    )
    mission_columns = st.columns(3)
    for index, definition in enumerate(MISSIONS):
        copy = MISSION_UI[definition.id]
        with mission_columns[index % 3]:
            st.markdown(f"**{copy['code']} · {copy['plain_name']}**")
            st.caption(copy["question"])

with st.expander("How to explain AgriScope Earth to another person"):
    st.write(
        "AgriScope Earth is an open-source global research-screening platform. A user chooses an agricultural or environmental question, selects a location, and combines live public data with documented local inputs in a transparent Python model. The platform returns a priority index, source receipts, limitations and reproducible exports. It helps researchers and practitioners decide what to investigate next; it does not replace field validation, causal analysis or official warnings."
    )

st.caption("AgriScope Earth · Open research demonstrator · MIT licensed · Methodology ASE-0.2")
