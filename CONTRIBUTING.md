# Contributing

Contributions are welcome when they preserve scientific transparency.

## Before opening a pull request

1. Create a focused branch.
2. Add or update tests for every changed equation or threshold.
3. Run `python -m pytest backend/tests tests/test_streamlit_app.py -q` from the repository root.
4. Run `npm run build`, `npm test`, and `npm run lint` from the repository root.
5. Update `docs/METHODOLOGY.md` when a calculation, factor, boundary or status rule changes.
6. Add source licence and attribution details to `docs/DATA_SOURCES.md` for new datasets.
7. Update `docs/SCIENTIFIC_VALIDATION.md` when a change affects a claim, validation requirement, or research-use boundary.

## Non-negotiable rules

- Never label modelled, forecast, interpolated or demonstration data as observed.
- Never add an unsupported crop-disease diagnosis.
- Never hide uncertainty, source latency or missing-data fallback.
- Never commit API keys, tokens, farmer identifiers or precise private farm boundaries.
- Keep external request destinations fixed or allow-listed.

Bug reports should include the mission ID, request payload with private information removed, methodology version and expected result.
