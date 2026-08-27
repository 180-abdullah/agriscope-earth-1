# Security policy

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose credentials, private farm locations or infrastructure. Contact the repository owner privately after replacing the placeholder contact details in the GitHub repository settings.

## Deployment guidance

- Keep `FIRMS_MAP_KEY` and future provider keys on the Python server.
- Treat `NEXT_PUBLIC_*` values as public browser configuration.
- Restrict `CORS_ORIGINS` to deployed frontend origins.
- Put production deployments behind HTTPS and rate limiting.
- Do not log raw farmer identifiers or confidential field boundaries.
- Review provider terms, quotas and required attribution.
- Keep the Sentinel sample cap bounded for public deployments; the default is 2,500 ha.
- Do not enable `SENTINEL_ALLOW_INSECURE_SSL` on a public deployment. It exists only for controlled local TLS-inspection diagnostics.
- Keep Streamlit upload limits small because M03 accepts a two-row CSV, not arbitrary raster uploads.

The fixed external-service adapters reject user-defined upstream URLs, reducing server-side request-forgery risk.
