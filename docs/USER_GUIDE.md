# User guide

## What AgriScope Earth does

AgriScope Earth helps a researcher, extension worker, farm manager, student, or environmental analyst answer one practical question at a time. It combines live public data, transparent user inputs, and documented equations to produce a **screening priority**, evidence receipt, limitations, and reusable research files.

It helps answer “What should I investigate next?” It does not replace an agronomist, laboratory, field survey, official warning, audited inventory, or causal study.

## The three-minute workflow

1. Choose **Guided** mode for explanations or **Research** mode for advanced source filters and overrides.
2. Choose one of the six research questions.
3. Search a place worldwide, enter coordinates, or click the reliable map.
4. Set the analysis area and give the study a meaningful name.
5. Review the mission-specific inputs. Use real measurements only when you can document them.
6. Select **Run analysis**.
7. Read the evidence banner before reading the priority index.
8. Inspect indicators, source receipts, acquisition identifiers, assumptions, and limitations.
9. Export JSON for reproducibility, CSV for analysis, GeoJSON for GIS, or Markdown for a research note.
10. Verify important findings with field evidence or the relevant authority.

## Which mission should I choose?

| If your question is… | Choose | Bring or verify |
|---|---|---|
| Could river and rainfall conditions expose crops? | M01 Flood exposure | Crop stage, drainage, local warning and terrain/inundation map |
| Which fields deserve stress scouting first? | M02 Crop stress | Field boundary/crop stage; use live Sentinel-2 or your cloud-screened NDVI/NDMI |
| Did water, cropland, or tree share change? | M03 Land change | Two comparable classified summaries and their accuracy assessment |
| How much water and pumping energy may be needed? | M04 Irrigation | Crop stage coefficient, effective rainfall, application efficiency, pump head/efficiency |
| Which farm activities dominate a screening GHG inventory? | M05 Carbon | Activity data for one consistent period and appropriate emission factors |
| Do heat, dryness, wind, and hotspots require rapid checking? | M06 Fire + heat | Optional FIRMS key, safe field verification, official fire/weather information |

## Understand the evidence banner

- **Live-assisted screening:** a current observation, near-real-time source, or forecast contributed.
- **Mixed evidence:** live/public evidence and user-entered values were combined.
- **Calculated screening:** the result comes from stated inputs and equations.
- **Demonstration present:** at least one value is an example or fallback. Do not cite the output as an observation.
- **Evidence incomplete:** an expected source was unavailable. Treat the result as provisional.

The percentage called **evidence completeness** is a rule-based traceability indicator. It is not model accuracy, a probability, a p-value, or a confidence interval.

## M02 live Sentinel-2 mode

Live mode can take tens of seconds because the app searches and reads a bounded part of recent satellite imagery. A successful result contains:

- STAC item identifier and acquisition time;
- sampled area and valid-pixel fraction;
- whole-scene cloud metadata;
- clear-pixel median NDVI and NDMI;
- the quality-mask method and limitations.

If satellite access fails or clear pixels are insufficient, the app does not invent a live result. It displays a demonstration label and records why the source was unavailable.

## M03 CSV format

Download the template in the sidebar. It must contain exactly the required columns and both periods:

```csv
period,water_pct,cropland_pct,tree_pct
baseline,28,42,24
current,23,48,19
```

The three displayed classes do not have to total 100 if other mutually exclusive classes exist. A total above 100 requires explanation because the classes may overlap or be inconsistent.

## How to describe the app to other people

> AgriScope Earth is an open-source global screening workbench for agriculture and environmental research. It combines traceable public Earth data with documented local inputs, shows exactly where each value came from, and exports a reproducible record. It helps decide what to investigate next; it does not replace field validation or official warnings.

## Common problems

**The 3D view is blank.**  
Your browser or hosted environment may not provide WebGL. Use **Reliable target map**; it uses Leaflet and remains fully functional.

**A run says demonstration.**  
Open **Evidence & trust**. A public API may be unreachable, a required key may be absent, or you selected demonstration mode. Do not use that run as observational evidence.

**Sentinel-2 is slow or unavailable.**  
Try a longer lookback or larger cloud threshold in Research mode. Optical imagery may still be unusable under persistent cloud, snow, or low valid coverage.

**The priority looks precise.**  
The decimal is for reproducible comparison, not validated certainty. Report inputs, evidence status, assumptions, and sensitivity—not only the score.

**Can I publish a paper using it?**  
You can use the software and exported provenance as part of a defensible workflow, but a publication still needs a study-specific protocol, validated measurements, statistical analysis, uncertainty, ethics/licensing where applicable, and calibrated claims. Read [Scientific validation and integrity status](SCIENTIFIC_VALIDATION.md).
