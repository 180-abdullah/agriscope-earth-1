from __future__ import annotations

import csv
import io
import json
import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from . import __version__
from .missions import run_mission
from .missions.catalog import MISSIONS
from .models import AnalysisRequest, ExportRequest


app = FastAPI(
    title="AgriScope Earth API",
    version=__version__,
    description="Python research engines for six global agricultural and environmental missions.",
    license_info={"name": "MIT", "url": "https://opensource.org/license/mit"},
)

origins = [
    item.strip()
    for item in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:4173").split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "name": "AgriScope Earth API",
        "version": __version__,
        "mission_count": len(MISSIONS),
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/api/v1/missions")
async def missions() -> list[dict[str, Any]]:
    return [mission.model_dump(mode="json") for mission in MISSIONS]


@app.post("/api/v1/analyze")
async def analyze(request: AnalysisRequest) -> JSONResponse:
    result = await run_mission(request)
    return JSONResponse(result.model_dump(mode="json"))


@app.post("/api/v1/export")
async def export(payload: ExportRequest) -> Response:
    analysis = payload.analysis.model_dump(mode="json")
    filename = f"agriscope-{payload.analysis.mission.value}-{payload.analysis.analysis_id[:8]}"

    if payload.format == "json":
        return Response(
            json.dumps(analysis, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}.json"'},
        )
    if payload.format == "geojson":
        feature = dict(analysis["geometry"])
        feature["properties"] = {
            **feature.get("properties", {}),
            "analysis_id": analysis["analysis_id"],
            "mission": analysis["mission"],
            "score": analysis["score"],
            "risk_level": analysis["risk_level"],
            "generated_at": analysis["generated_at"],
        }
        body = {"type": "FeatureCollection", "features": [feature]}
        return Response(
            json.dumps(body, indent=2),
            media_type="application/geo+json",
            headers={"Content-Disposition": f'attachment; filename="{filename}.geojson"'},
        )

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["analysis_id", analysis["analysis_id"]])
    writer.writerow(["mission", analysis["mission"]])
    writer.writerow(["generated_at", analysis["generated_at"]])
    writer.writerow(["latitude", analysis["coordinates"]["latitude"]])
    writer.writerow(["longitude", analysis["coordinates"]["longitude"]])
    writer.writerow(["area_hectares", analysis["area_hectares"]])
    writer.writerow(["score", analysis["score"]])
    writer.writerow(["risk_level", analysis["risk_level"]])
    writer.writerow([])
    writer.writerow(["metric_key", "metric_label", "value", "unit", "interpretation"])
    for metric in analysis["metrics"]:
        writer.writerow([metric["key"], metric["label"], metric["value"], metric["unit"], metric["interpretation"]])
    return PlainTextResponse(
        stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )
