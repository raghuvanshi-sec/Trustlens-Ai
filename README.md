# TrustLens AI

TrustLens AI is an evidence-driven investigation engine for suspicious job offers. It extracts verifiable claims from recruiter messages, creates targeted search queries, collects live web results through SerpApi, classifies sources, and returns a structured investigation trail for human review.

The project is currently in an early backend-first stage. The FastAPI service is implemented; the `frontend` directory is reserved for the user interface and the `docs` directory contains project documentation.

## Key Features

- Extracts company, employment, recruiter, contact, URL, and payment-related claims.
- Generates verification queries based on the claims found in a message.
- Searches live web results with SerpApi.
- Normalizes sources and classifies them as official, professional network, news, or other.
- Produces claim-level evidence, findings, and an investigation trail.
- Exposes a health endpoint for local and deployment checks.

## Tech Stack

- **Language:** Python 3.10+
- **API framework:** FastAPI
- **ASGI server:** Uvicorn
- **Web search:** SerpApi
- **Configuration:** Environment variables loaded with `python-dotenv`
- **Client application:** Planned in `frontend/`

## Repository Layout

```mermaid
   flowchart TD
.
+-- backend/
|   +-- app/
|   |   +-- agent/       # Claim extraction and query planning
|   |   +-- api/         # FastAPI routes
|   |   +-- models/      # Request and response schemas
|   |   +-- services/    # Search and evidence processing
|   +-- requirements.txt
+-- docs/                # Project documentation
+-- frontend/            # Reserved for the web client
+-- README.md
```

## Prerequisites

- Python 3.10 or newer
- A SerpApi account and API key for live investigations
- Git

## Getting Started

### 1. Clone the repository

```powershell
git clone https://github.com/raghuvanshi-sec/Trustlens-Ai.git
cd Trustlens-Ai
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

### 4. Configure SerpApi

Set the API key in the shell before starting the service. The application reads `SERPAPI_API_KEY` from the environment or a `.env` file in the working directory.

PowerShell:

```powershell
$env:SERPAPI_API_KEY = "your-serpapi-key"
```

Or create `backend/.env`:

```env
SERPAPI_API_KEY=your-serpapi-key
```

Do not commit real API keys. The repository ignores `.env` files.

### 5. Start the API

Run Uvicorn from the `backend` directory so Python can resolve the `app` package:

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## API Reference

### Health check

```http
GET /api/health
```

Example response:

```json
{
  "status": "ok",
  "service": "TrustLens AI"
}
```

### Investigate a job offer

```http
POST /api/investigate
Content-Type: application/json
```

Example request:

```json
{
  "message_text": "You have been selected for a software engineer position. Please pay a registration fee to continue.",
  "company_name": "Example Corporation",
  "recruiter_details": {
    "name": "Alex Recruiter",
    "email": "alex@example.com"
  },
  "application_url": "https://example.com/apply",
  "job_listing_url": "https://example.com/jobs/123"
}
```

The response includes the generated claims, search queries, normalized sources, evidence, findings, an overall finding, and the ordered investigation trail. A live SerpApi key is required because the route performs web searches for each planned query.

Example request with PowerShell:

```powershell
$body = @{
  message_text = "You have been selected for a software engineer position."
  company_name = "Example Corporation"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/api/investigate `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

## How It Works

1. The route receives recruiter message and company details.
2. `claims.py` extracts claims that can be checked independently.
3. `query_planner.py` turns claims into targeted search queries.
4. `serpapi.py` retrieves live search results.
5. `sources.py` normalizes result metadata and classifies source domains.
6. `evidence.py` compares sources with claims and creates conservative evidence and findings.
7. The route assembles the report and investigation trail for the client.

## Important Limitations

- Results are investigative signals, not a definitive fraud determination.
- Source matching is intentionally conservative and currently uses simple company-name and domain comparisons.
- Search availability and result quality depend on SerpApi and the configured search engine.
- The current investigation ID is a demo value and is not persisted.
- There is no database, authentication, rate limiting, or production deployment configuration yet.
- The frontend is not implemented yet.

## Development Notes

Keep the backend working directory set to `backend` when launching Uvicorn. Before opening a pull request, verify the health endpoint and exercise `/api/investigate` with a test SerpApi key. Add automated tests as the claim extraction, query planning, and evidence rules grow.

## Deployment

No deployment target is configured yet. For a basic production deployment, install the dependencies in an isolated Python environment, provide `SERPAPI_API_KEY` through the platform's secret manager, and run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Run that command with `backend` as the working directory. Add authentication, request validation at the edge, logging, rate limiting, and persistent investigation storage before exposing the service publicly.

## License

No license has been specified yet.