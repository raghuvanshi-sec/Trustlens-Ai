# TrustLens AI

TrustLens AI investigates suspicious job offers by extracting checkable claims, searching public web sources, and linking findings to evidence. It is an investigative aid, not a definitive fraud detector.

## Stack

- FastAPI, Pydantic, Uvicorn, SerpApi
- React, Vite, Lucide icons
- DM Sans + IBM Plex Mono; warm paper, ink, slate, and restrained rust-red warnings

## Run locally

### Backend (PowerShell)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
# Set SERPAPI_API_KEY in backend/.env, then:
python -m uvicorn app.main:app --reload
```

### Frontend (second terminal)

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to FastAPI on port 8000. Build with `npm run build`.

## Test backend

From `backend/`:

```powershell
python -m pytest -q
```

The tests use mocked search responses; they do not require a live SerpApi key. Live search requires a valid `SERPAPI_API_KEY`.

## API

- `GET /api/health`
- `POST /api/investigate`

Example request:

```json
{
  "company_name": "Example Corporation",
  "message_text": "You have been selected for a role. Pay a registration fee to continue.",
  "application_url": "https://example.com/apply"
}
```

The report contains extracted claims, planned searches, normalized sources, claim-level evidence, findings, an overall assessment, and a search trail. Search failures are reported as incomplete results rather than treated as proof of fraud.

## Safety and limitations

- Payment requests are treated as a risk signal and should be verified independently before paying.
- A domain that resembles a company name is only a candidate, not proof of ownership.
- Search snippets can be incomplete or misleading; open the source and verify through contact details obtained independently.
- The MVP does not include authentication, rate limiting, persistent storage, or production deployment hardening. Do not expose it publicly without those controls.
- Never commit `.env` files or API credentials. `.gitignore` excludes environment files while allowing `.env.example`.

## QA

See [`docs/QA_REPORT.md`](docs/QA_REPORT.md) for verified checks and environment-dependent checks. Local browser-to-API testing and a live SerpApi request remain to be run on a machine with configured credentials.
