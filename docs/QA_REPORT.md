# TrustLens AI — QA report

## Checks completed in this workspace

- Backend automated tests: **21 passed** using `pytest` and FastAPI's test client.
- Python source compilation: **passed** with `python -m compileall -q app tests`.
- Frontend JSX syntax parsing: **passed** with the available TypeScript parser.
- CSS structural check: **passed**; the stylesheet contains no gradients or box shadows.
- Accessibility palette spot-check: key body text, warning text, muted labels, and status colors meet WCAG AA contrast against their intended backgrounds.
- API contract tests cover missing search credentials, mocked successful search responses, per-query failures, request validation, and source URL filtering. No live SerpApi request was made.
- Packaging excludes `.git`, local environment files, caches, `node_modules`, and build output.

## Checks not completed here

- `npm install` and `npm run build` could not run because the npm registry could not be resolved from this workspace (`EAI_AGAIN`). The production frontend bundle is therefore **not build-verified here**.
- Live SerpApi behavior and the local browser-to-API flow were intentionally not tested. They require the user's local environment and API key.

## Recommended local verification

1. Install dependencies from `backend/requirements-dev.txt` and run `python -m pytest -q` from `backend/`.
2. Run `npm install` and `npm run build` from `frontend/`.
3. Configure `SERPAPI_API_KEY` in `backend/.env`, start FastAPI from `backend/`, then start Vite from `frontend/`.
4. Submit a normal offer, a payment-request example, and an offer with no search results. Confirm the report distinguishes risk signals from incomplete evidence.
