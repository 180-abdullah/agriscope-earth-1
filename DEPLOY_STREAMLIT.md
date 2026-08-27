# Publish AgriScope Earth with Streamlit Community Cloud

The repository is already arranged for Streamlit Community Cloud. The public app entry point is `streamlit_app.py`; no build command or JavaScript server is required.

## 1. Upload to GitHub

Create a new empty GitHub repository, for example `agriscope-earth`. Do not add a README or license on GitHub because both are already included here.

From this project folder:

```bash
git init
git add .
git commit -m "Launch AgriScope Earth"
git branch -M main
git remote add origin https://github.com/180-abdullah/agriscope-earth.git
git push -u origin main
```

You can also extract the supplied ZIP and upload its contents using GitHub's **Add file → Upload files** interface.

### Updating an existing repository

The safest method is GitHub Desktop:

1. Clone your existing repository in GitHub Desktop.
2. Extract the release ZIP into the cloned folder, replacing the old project files.
3. Check the **Changes** tab. Do not add `.streamlit/secrets.toml` if you created one locally.
4. Commit with a message such as `Upgrade AgriScope Earth to 0.2.0`.
5. Select **Push origin**.

Streamlit Community Cloud watches the repository and normally redeploys after the push. If it does not, open the app menu and select **Reboot app**.

## 2. Deploy publicly

1. Sign in at [share.streamlit.io](https://share.streamlit.io/) with GitHub.
2. Select **Create app**.
3. Choose your `agriscope-earth` repository and the `main` branch.
4. Set **Main file path** to `streamlit_app.py`.
5. Choose a public app and click **Deploy**.

Streamlit installs `requirements.txt`, reads `runtime.txt`, and starts the app automatically. The generated `https://...streamlit.app` address can be opened by anyone.

The first ASE-0.2 build may take several minutes because NumPy and Rasterio are installed for the live Sentinel-2 processor.

## 3. Optional NASA FIRMS hotspots

The app works without secrets. To enable actual nearby NASA FIRMS thermal detections:

1. Request a free [NASA FIRMS map key](https://firms.modaps.eosdis.nasa.gov/api/map_key/).
2. Open the app's **Settings → Secrets** page.
3. Add:

```toml
FIRMS_MAP_KEY = "your-key-here"
```

Never commit `.streamlit/secrets.toml`; it is ignored by Git.

## 4. Local check before publishing

```bash
python -m venv .venv
```

Activate the environment, then:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open `http://localhost:8501`.

## Alternative: Docker

```bash
docker compose -f docker-compose.streamlit.yml up --build
```

Open `http://localhost:8501`.

## Public-data note

Open-Meteo weather/flood/geocoding and Element 84 Earth Search are queried at runtime. If a service is unavailable, rate-limited, cloud-obscured or unreadable, AgriScope Earth records the failure and labels any fallback `demonstration`. That policy prevents sample values from being presented as observations.

## Deployment troubleshooting

- **Module installation fails:** verify the app uses the included `runtime.txt` and Python 3.12, then reboot.
- **The 3D panel is blank:** use the Reliable target map. The analysis still works when WebGL is disabled.
- **Sentinel-2 times out:** retry, increase the lookback/cloud limit in Research mode, or supply your own processed NDVI/NDMI.
- **FIRMS stays demonstration:** add a valid `FIRMS_MAP_KEY` to Streamlit Secrets and reboot.
- **The old version still appears:** confirm the latest commit is on the deployed branch and use **Reboot app**.
