from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from backend.app.services.earth_data import earth_data


MISSION_OPTIONS = [
    "M01  Flood exposure",
    "M02  Crop stress",
    "M03  Land and wetland change",
    "M04  Irrigation planning",
    "M05  Farm carbon screening",
    "M06  Fire and heat",
]
APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"


@pytest.fixture(autouse=True)
def offline_public_services(monkeypatch):
    async def unavailable(*_args, **_kwargs):
        raise RuntimeError("offline test fixture")

    monkeypatch.setattr(earth_data, "weather", unavailable)
    monkeypatch.setattr(earth_data, "flood", unavailable)
    monkeypatch.setattr(earth_data, "fires", unavailable)


def test_streamlit_analysis_renders_results() -> None:
    earth_data.timeout_seconds = 0.05
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()

    worked_example = next(button for button in app.button if button.label == "▶ RUN WORKED EXAMPLE")
    worked_example.click().run(timeout=20)

    assert not app.exception
    assert [metric.label for metric in app.metric] == [
        "Priority index",
        "Priority class",
        "Evidence completeness",
        "Analysis area",
    ]
    assert any("ANALYSIS COMPLETE" in markdown.value for markdown in app.markdown)


@pytest.mark.parametrize("mission_option", MISSION_OPTIONS)
def test_every_mission_control_panel_loads(mission_option: str) -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()

    mission_radio = next(radio for radio in app.radio if radio.label == "CHOOSE A RESEARCH QUESTION")
    mission_radio.set_value(mission_option).run(timeout=20)

    assert not app.exception
    assert next(radio for radio in app.radio if radio.label == "CHOOSE A RESEARCH QUESTION").value == mission_option


@pytest.mark.parametrize("mission_option", MISSION_OPTIONS)
def test_every_worked_example_executes(mission_option: str) -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()
    mission_radio = next(radio for radio in app.radio if radio.label == "CHOOSE A RESEARCH QUESTION")
    mission_radio.set_value(mission_option).run(timeout=20)
    worked_example = next(button for button in app.button if button.label == "▶ RUN WORKED EXAMPLE")
    worked_example.click().run(timeout=20)

    assert not app.exception
    assert [metric.label for metric in app.metric[:4]] == [
        "Priority index",
        "Priority class",
        "Evidence completeness",
        "Analysis area",
    ]
    assert any("ANALYSIS COMPLETE" in markdown.value for markdown in app.markdown)
