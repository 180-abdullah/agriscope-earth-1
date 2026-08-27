from __future__ import annotations

import csv
import io
import json
from typing import Any


def build_research_package(result: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    return {
        "package_type": "AgriScope Earth reproducible screening record",
        "request": request,
        "analysis": result,
    }


def result_csv(result: dict[str, Any], request: dict[str, Any]) -> str:
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["analysis_id", result["analysis_id"]])
    writer.writerow(["mission", result["mission"]])
    writer.writerow(["generated_at", result["generated_at"]])
    writer.writerow(["study_name", request.get("name") or ""])
    writer.writerow(["latitude", result["coordinates"]["latitude"]])
    writer.writerow(["longitude", result["coordinates"]["longitude"]])
    writer.writerow(["area_hectares", result["area_hectares"]])
    writer.writerow(["score", result["score"]])
    writer.writerow(["risk_level", result["risk_level"]])
    writer.writerow(["evidence_completeness", result["confidence"]])
    writer.writerow(["data_status", "|".join(result["data_status"])])
    writer.writerow([])
    writer.writerow(["input_key", "input_value"])
    for key, value in sorted(request.get("parameters", {}).items()):
        writer.writerow([key, value])
    writer.writerow([])
    writer.writerow(["metric_key", "metric_label", "value", "unit", "interpretation"])
    for metric in result["metrics"]:
        writer.writerow([metric["key"], metric["label"], metric["value"], metric["unit"], metric["interpretation"]])
    return stream.getvalue()


def research_note(result: dict[str, Any], request: dict[str, Any]) -> str:
    statuses = ", ".join(result["data_status"])
    metrics = "\n".join(
        f"- **{item['label']}:** {item['value']} {item['unit']} — {item['interpretation']}"
        for item in result["metrics"]
    )
    caveats = "\n".join(f"- {item}" for item in result["caveats"])
    parameters = json.dumps(request.get("parameters", {}), indent=2, ensure_ascii=False)
    return f"""# {result['title']}

**Study:** {request.get('name') or 'Untitled screening'}  
**Analysis ID:** {result['analysis_id']}  
**Generated:** {result['generated_at']}  
**Methodology:** {result['methodology_version']}  
**Target:** {result['coordinates']['latitude']}, {result['coordinates']['longitude']}  
**Area:** {result['area_hectares']} ha  
**Priority index:** {result['score']}/100 ({result['risk_level']})  
**Evidence completeness:** {result['confidence'] * 100:.0f}% (rule-based traceability indicator)  
**Data status:** {statuses}

## Interpretation

{result['summary']}

The priority index is a screening score, not a probability or measured loss.

## Indicators

{metrics}

## Inputs

```json
{parameters}
```

## Limitations

{caveats}

## Research-use statement

This output supports screening and prioritization. Validate it with field measurements, official warnings and domain expertise before operational or scientific claims.
"""
