"use client";

import {
  Activity,
  Crosshair,
  Database,
  Download,
  Droplets,
  ExternalLink,
  Flame,
  Layers3,
  Leaf,
  Play,
  Radio,
  Sprout,
  Waves,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

declare global {
  interface Window {
    // Cesium is loaded at runtime from the official CDN, outside this bundle.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    Cesium?: any;
  }
}

type Metric = { key: string; label: string; value: string | number | null; unit: string; interpretation: string };
type Source = { name: string; url?: string | null; role: string; status: string; spatial_resolution?: string | null; temporal_resolution?: string | null };
type Analysis = {
  analysis_id: string; generated_at: string; methodology_version: string; mission: string; title: string;
  score: number; risk_level: string; confidence: number; summary: string; data_status: string[];
  metrics: Metric[]; sources: Source[]; caveats: string[];
};
type Mission = {
  id: string; code: string; name: string; label: string; question: string; accent: string;
  latitude: number; longitude: number; area: number; icon: typeof Waves; score: number;
  metrics: Array<[string, number, string, string]>;
};

const MISSIONS: Mission[] = [
  {
    id: "flood-watch", code: "01", name: "Global Flood & Crop Exposure Watch", label: "FLOOD WATCH",
    question: "Where could forecast river conditions expose agricultural land?", accent: "#48e5c2",
    latitude: 15.4, longitude: 105.8, area: 25000, icon: Waves, score: 68,
    metrics: [
      ["Peak / mean discharge", 1.83, "ratio", "Above-mean modelled river discharge"],
      ["Forecast precipitation", 84.6, "mm / 7 d", "Weather-model accumulation"],
      ["Screened crop exposure", 11820, "ha", "Verification priority, not measured loss"],
    ],
  },
  {
    id: "crop-stress", code: "02", name: "Global Crop Stress Patrol", label: "CROP STRESS",
    question: "Which fields should be checked first for vegetation, moisture or heat stress?", accent: "#b7ff4a",
    latitude: 30.7, longitude: 75.8, area: 8000, icon: Sprout, score: 57,
    metrics: [
      ["NDVI", 0.39, "index", "Demonstration processed vegetation index"],
      ["NDMI", 0.12, "index", "Demonstration canopy-moisture proxy"],
      ["Priority verification area", 3648, "ha", "Area screened for closer inspection"],
    ],
  },
  {
    id: "land-change", code: "03", name: "Global Wetland & Land-Use Change Audit", label: "LAND CHANGE",
    question: "How have water, cropland and tree-cover shares changed between observations?", accent: "#44a7ff",
    latitude: -18.3, longitude: -57.5, area: 50000, icon: Layers3, score: 46,
    metrics: [
      ["Water / wetland change", -6.4, "percentage points", "Current minus baseline share"],
      ["Cropland change", 4.9, "percentage points", "Current minus baseline share"],
      ["Approximate changed area", 2980, "ha", "Summary-based screening estimate"],
    ],
  },
  {
    id: "irrigation", code: "04", name: "Global Irrigation Intelligence", label: "IRRIGATION",
    question: "How much water and pumping energy may be needed during the next seven days?", accent: "#5ed6ff",
    latitude: 29.9, longitude: 31.2, area: 1200, icon: Droplets, score: 61,
    metrics: [
      ["Gross irrigation depth", 39.7, "mm", "Need adjusted for application efficiency"],
      ["Irrigation volume", 476400, "m³", "One mm over one ha equals ten m³"],
      ["Pumping electricity", 42492, "kWh", "Hydraulic screening estimate"],
    ],
  },
  {
    id: "carbon", code: "05", name: "Global Agricultural Carbon Scanner", label: "CARBON",
    question: "What is the Tier 1 footprint of supplied agricultural activity data?", accent: "#ffbd59",
    latitude: 41.8, longitude: 12.4, area: 500, icon: Leaf, score: 52,
    metrics: [
      ["Total screening emissions", 3092, "t CO₂e", "Included Tier 1 source categories"],
      ["Area-based intensity", 6.18, "t CO₂e/ha", "Total divided by selected area"],
      ["Rice methane", 1779, "t CO₂e", "Daily factor with management scalars"],
    ],
  },
  {
    id: "fire-heat", code: "06", name: "Global Agricultural Fire & Heat Watch", label: "FIRE + HEAT",
    question: "Where do heat, dryness, wind and hotspots justify rapid verification?", accent: "#ff6b4a",
    latitude: 37.3, longitude: 23.7, area: 10000, icon: Flame, score: 73,
    metrics: [
      ["Heat index", 41.8, "°C", "Screening apparent-temperature indicator"],
      ["Nearby thermal detections", 5, "detections", "Demonstration hotspot count"],
      ["Maximum wind", 34.2, "km/h", "Weather-model spread proxy"],
    ],
  },
];

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";
const STREAMLIT_APP = process.env.NEXT_PUBLIC_STREAMLIT_APP_URL ?? "https://env-agri-earth.streamlit.app/";

function riskBand(score: number) {
  if (score < 25) return "low";
  if (score < 50) return "moderate";
  if (score < 75) return "high";
  return "severe";
}

function demoAnalysis(mission: Mission, latitude: number, longitude: number): Analysis {
  const shift = Math.round(((Math.abs(latitude) * 1.7 + Math.abs(longitude) * 0.6) % 11) - 5);
  const score = Math.max(0, Math.min(100, mission.score + shift));
  return {
    analysis_id: `demo-${mission.id}`,
    generated_at: new Date().toISOString(),
    methodology_version: "ASE-0.2",
    mission: mission.id,
    title: mission.name,
    score,
    risk_level: riskBand(score),
    confidence: 0.42,
    summary: `The global screening workflow indicates ${riskBand(score)} priority at this representative area of interest. Connect the Python engine for current public data and supply field or processed satellite inputs before scientific use.`,
    data_status: ["demonstration", "modelled", "calculated"],
    metrics: mission.metrics.map(([label, value, unit, interpretation], index) => ({ key: `metric-${index + 1}`, label, value, unit, interpretation })),
    sources: [{ name: "AgriScope demonstration dataset", url: "https://github.com/180-abdullah/agriscope-earth", role: "Interface demonstration until the Python API is connected", status: "demonstration" }],
    caveats: [
      "Values marked demonstration are deterministic interface examples, not observations for this coordinate.",
      "Use the Python API, documented inputs and ground verification for analysis.",
    ],
  };
}

export default function Home() {
  const [missionId, setMissionId] = useState(MISSIONS[0].id);
  const mission = useMemo(() => MISSIONS.find((item) => item.id === missionId) ?? MISSIONS[0], [missionId]);
  const [latitude, setLatitude] = useState(mission.latitude);
  const [longitude, setLongitude] = useState(mission.longitude);
  const [area, setArea] = useState(mission.area);
  const [analysis, setAnalysis] = useState<Analysis>(() => demoAnalysis(MISSIONS[0], MISSIONS[0].latitude, MISSIONS[0].longitude));
  const [running, setRunning] = useState(false);
  const [engine, setEngine] = useState<"demo" | "python">("demo");
  const [globeReady, setGlobeReady] = useState(false);
  const [globeFailed, setGlobeFailed] = useState(false);
  const [utc, setUtc] = useState("SYNCHRONIZING");
  const globeElementRef = useRef<HTMLDivElement | null>(null);
  // Runtime Cesium objects are intentionally opaque to the React bundle.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const viewerRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const markerRef = useRef<any>(null);

  const stageMission = useCallback((next: Mission) => {
    setMissionId(next.id);
    setLatitude(next.latitude);
    setLongitude(next.longitude);
    setArea(next.area);
    setAnalysis(demoAnalysis(next, next.latitude, next.longitude));
    setEngine("demo");
  }, []);

  useEffect(() => {
    const tick = () => setUtc(new Date().toISOString().replace("T", " ").slice(0, 19));
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const init = () => {
      if (cancelled || viewerRef.current || !globeElementRef.current || !window.Cesium) return;
      const Cesium = window.Cesium;
      try {
      const viewer = new Cesium.Viewer(globeElementRef.current, {
        animation: false,
        baseLayerPicker: false,
        fullscreenButton: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        navigationHelpButton: false,
        sceneModePicker: false,
        selectionIndicator: false,
        timeline: false,
        shouldAnimate: true,
        baseLayer: new Cesium.ImageryLayer(new Cesium.OpenStreetMapImageryProvider({ url: "https://tile.openstreetmap.org/" })),
      });
      viewer.scene.backgroundColor = Cesium.Color.fromCssColorString("#020908");
      viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#061613");
      viewer.scene.globe.enableLighting = true;
      viewer.scene.skyAtmosphere.hueShift = -0.22;
      viewer.scene.skyAtmosphere.saturationShift = -0.35;
      viewer.scene.skyAtmosphere.brightnessShift = -0.25;
      viewer.camera.setView({ destination: Cesium.Cartesian3.fromDegrees(15, 12, 19000000) });
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      viewer.screenSpaceEventHandler.setInputAction((movement: any) => {
        const position = viewer.camera.pickEllipsoid(movement.position, viewer.scene.globe.ellipsoid);
        if (!position) return;
        const cartographic = Cesium.Cartographic.fromCartesian(position);
        setLatitude(Number(Cesium.Math.toDegrees(cartographic.latitude).toFixed(4)));
        setLongitude(Number(Cesium.Math.toDegrees(cartographic.longitude).toFixed(4)));
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
      viewerRef.current = viewer;
      setGlobeReady(true);
      setGlobeFailed(false);
      } catch {
        setGlobeFailed(true);
      }
    };

    if (window.Cesium) init();
    else {
      if (!document.querySelector('link[data-cesium="true"]')) {
        const css = document.createElement("link");
        css.rel = "stylesheet";
        css.href = "https://cesium.com/downloads/cesiumjs/releases/1.124/Build/Cesium/Widgets/widgets.css";
        css.dataset.cesium = "true";
        document.head.appendChild(css);
      }
      const existing = document.querySelector<HTMLScriptElement>('script[data-cesium="true"]');
      if (existing) existing.addEventListener("load", init, { once: true });
      else {
        const script = document.createElement("script");
        script.src = "https://cesium.com/downloads/cesiumjs/releases/1.124/Build/Cesium/Cesium.js";
        script.async = true;
        script.dataset.cesium = "true";
        script.addEventListener("load", init, { once: true });
        document.body.appendChild(script);
      }
    }
    return () => {
      cancelled = true;
      if (viewerRef.current && !viewerRef.current.isDestroyed()) viewerRef.current.destroy();
      viewerRef.current = null;
    };
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (!viewerRef.current) setGlobeFailed(true);
    }, 9000);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const Cesium = window.Cesium;
    const viewer = viewerRef.current;
    if (!Cesium || !viewer) return;
    if (markerRef.current) viewer.entities.remove(markerRef.current);
    const radius = Math.max(22000, Math.min(220000, Math.sqrt(area) * 1200));
    markerRef.current = viewer.entities.add({
      position: Cesium.Cartesian3.fromDegrees(longitude, latitude),
      point: { pixelSize: 11, color: Cesium.Color.fromCssColorString(mission.accent), outlineColor: Cesium.Color.BLACK, outlineWidth: 2, disableDepthTestDistance: Number.POSITIVE_INFINITY },
      ellipse: { semiMajorAxis: radius, semiMinorAxis: radius, material: Cesium.Color.fromCssColorString(mission.accent).withAlpha(0.13), outline: true, outlineColor: Cesium.Color.fromCssColorString(mission.accent).withAlpha(0.85) },
      label: { text: mission.label, font: "12px monospace", fillColor: Cesium.Color.fromCssColorString(mission.accent), showBackground: true, backgroundColor: Cesium.Color.BLACK.withAlpha(0.72), pixelOffset: new Cesium.Cartesian2(0, -30), disableDepthTestDistance: Number.POSITIVE_INFINITY },
    });
    viewer.camera.flyTo({ destination: Cesium.Cartesian3.fromDegrees(longitude, latitude, 2400000), duration: 1.8 });
  }, [area, globeReady, latitude, longitude, mission]);

  async function runAnalysis() {
    setRunning(true);
    try {
      if (!API_BASE) throw new Error("Python API URL is not configured");
      const response = await fetch(`${API_BASE}/api/v1/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mission: mission.id, latitude, longitude, area_hectares: area, parameters: {} }),
      });
      if (!response.ok) throw new Error(`Analysis failed: ${response.status}`);
      setAnalysis((await response.json()) as Analysis);
      setEngine("python");
    } catch {
      setAnalysis(demoAnalysis(mission, latitude, longitude));
      setEngine("demo");
    } finally { setRunning(false); }
  }

  function downloadResult() {
    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `agriscope-${mission.id}-${analysis.analysis_id.slice(0, 8)}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const Icon = mission.icon;
  return (
    <main className="research-console" style={{ "--mission": mission.accent } as React.CSSProperties}>
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark"><Leaf size={18} /><span className="orbit-dot" /></div>
          <div><strong>AGRISCOPE</strong><span>EARTH / RESEARCH CONSOLE</span></div>
        </div>
        <div className="system-state"><span className="pulse" /> GLOBAL SYSTEM ONLINE</div>
        <div className="coordinate-entry">
          <label>LAT<input aria-label="Latitude" type="number" min={-90} max={90} step="0.0001" value={latitude} onChange={(event) => setLatitude(Number(event.target.value))} /></label>
          <label>LON<input aria-label="Longitude" type="number" min={-180} max={180} step="0.0001" value={longitude} onChange={(event) => setLongitude(Number(event.target.value))} /></label>
          <label>AREA<input aria-label="Area in hectares" type="number" min={0.01} value={area} onChange={(event) => setArea(Math.max(0.01, Number(event.target.value)))} /><em>HA</em></label>
          <button className="run-button" onClick={runAnalysis} disabled={running}>
            {running ? <Activity className="spin" size={15} /> : <Play size={15} fill="currentColor" />}
            {running ? "ANALYZING" : "RUN ANALYSIS"}
          </button>
        </div>
      </header>

      <section className="console-grid">
        <aside className="mission-panel panel-frame">
          <div className="panel-heading"><span>RESEARCH MISSIONS</span><b>06 ACTIVE</b></div>
          <p className="panel-intro">Select a global mission, then click anywhere on Earth to reposition the area of interest.</p>
          <nav aria-label="Research missions" className="mission-list">
            {MISSIONS.map((item) => {
              const ItemIcon = item.icon;
              return (
                <button key={item.id} className={`mission-item ${item.id === mission.id ? "selected" : ""}`} onClick={() => stageMission(item)}>
                  <span className="mission-code">{item.code}</span><ItemIcon size={17} />
                  <span><strong>{item.label}</strong><small>{item.question}</small></span><i style={{ background: item.accent }} />
                </button>
              );
            })}
          </nav>
          <div className="integrity-card">
            <div><Database size={15} /><strong>DATA INTEGRITY</strong></div>
            <p>Every output declares whether its inputs are observed, near-real-time, forecast, modelled, calculated, user-supplied or demonstration.</p>
          </div>
        </aside>

        <section className="globe-stage" aria-label="Interactive global mission map">
          <div ref={globeElementRef} className="cesium-host" />
          <div className={`globe-fallback ${globeReady ? "hidden" : ""}`}>
            <Leaf size={34} />
            <strong>{globeFailed ? "3D VIEW UNAVAILABLE" : "INITIALIZING EARTH VIEW"}</strong>
            <p>{globeFailed ? "This browser has no usable WebGL context. The full Streamlit workbench includes a dependable non-WebGL map." : "Loading the optional Cesium operations globe…"}</p>
            {globeFailed && <a href={STREAMLIT_APP} target="_blank" rel="noreferrer">OPEN RELIABLE RESEARCH APP</a>}
          </div>
          <div className="scanlines" aria-hidden="true" /><div className="sweep" aria-hidden="true" />
          <div className="reticle" aria-hidden="true"><span /><span /><Crosshair size={42} /></div>
          <div className="stage-label"><Icon size={15} /><span>{mission.label}</span><b>AOI LOCKED</b></div>
          <div className="stage-telemetry">
            <div><span>LATITUDE</span><b>{latitude.toFixed(4)}°</b></div><div><span>LONGITUDE</span><b>{longitude.toFixed(4)}°</b></div>
            <div><span>AREA</span><b>{area.toLocaleString()} HA</b></div><div><span>GLOBE</span><b>{globeReady ? "CESIUM READY" : "LOADING"}</b></div>
          </div>
          <div className="map-help"><Crosshair size={13} /> CLICK GLOBE TO MOVE AOI · DRAG TO ORBIT · SCROLL TO ZOOM</div>
        </section>

        <aside className="analysis-panel panel-frame">
          <div className="panel-heading"><span>MISSION READOUT</span><b className={engine}>{engine === "python" ? "PYTHON LIVE" : "DEMO MODE"}</b></div>
          <div className="analysis-title"><span>{mission.code}</span><div><small>{analysis.methodology_version}</small><h1>{mission.name}</h1></div></div>
          <div className="score-block">
            <div className="score-ring" style={{ "--score": `${analysis.score * 3.6}deg` } as React.CSSProperties}><strong>{analysis.score.toFixed(0)}</strong><span>/ 100</span></div>
            <div><small>SCREENING PRIORITY</small><b className={`risk ${analysis.risk_level}`}>{analysis.risk_level.toUpperCase()}</b><p>{Math.round(analysis.confidence * 100)}% evidence completeness · not accuracy</p></div>
          </div>
          <p className="summary">{analysis.summary}</p>
          <div className="status-row">{analysis.data_status.map((status) => <span key={status}>{status}</span>)}</div>
          <div className="metric-stack">
            {analysis.metrics.slice(0, 5).map((metric) => (
              <article key={metric.key}>
                <div><span>{metric.label}</span><strong>{typeof metric.value === "number" ? metric.value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : metric.value}<em>{metric.unit}</em></strong></div>
                <p>{metric.interpretation}</p>
              </article>
            ))}
          </div>
          <div className="sources">
            <div className="section-label"><Radio size={13} /> SOURCE REGISTER</div>
            {analysis.sources.slice(0, 3).map((source) => source.url ? (
              <a key={source.name} href={source.url} target="_blank" rel="noreferrer"><span>{source.name}<small>{source.role}</small></span><ExternalLink size={13} /></a>
            ) : (
              <div className="source-static" key={source.name}><span>{source.name}<small>{source.role}</small></span></div>
            ))}
          </div>
          <div className="action-row">
            <button onClick={downloadResult}><Download size={14} /> EXPORT JSON</button>
            <a href="/methodology.txt" target="_blank" rel="noreferrer"><Database size={14} /> METHODOLOGY</a>
          </div>
          <a className="streamlit-link" href={STREAMLIT_APP} target="_blank" rel="noreferrer"><Sprout size={14} /> OPEN FULL STREAMLIT WORKBENCH</a>
        </aside>
      </section>

      <footer className="console-footer">
        <span><i /> AGRICULTURAL + ENVIRONMENTAL INTELLIGENCE</span>
        <span>GLOBAL COVERAGE · WGS 84 · RESEARCH SCREENING ONLY</span>
        <span>UTC {utc}</span>
      </footer>
    </main>
  );
}
