from fastapi import APIRouter

from app.models.schemas import InvestigationRequest, InvestigationResponse
from app.agent.claims import extract_claims
from app.agent.query_planner import plan_queries
from app.services.serpapi import SerpApiService
from app.services.sources import normalize_results
from app.services.evidence import analyze_evidence

router = APIRouter()


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate(request: InvestigationRequest):

    # --------------------------------
    # 1. Prepare recruiter details
    # --------------------------------

    recruiter_details = None

    if request.recruiter_details:
        recruiter_details = request.recruiter_details.model_dump()

    # --------------------------------
    # 2. Extract claims
    # --------------------------------

    claims = extract_claims(
        message_text=request.message_text,
        company_name=request.company_name,
        application_url=request.application_url,
        job_listing_url=request.job_listing_url,
        recruiter_details=recruiter_details,
    )

    # --------------------------------
    # 3. Generate verification queries
    # --------------------------------

    search_queries = plan_queries(
        claims=claims,
        company_name=request.company_name,
        message_text=request.message_text,
        application_url=request.application_url,
    )

    # --------------------------------
    # 4. Search live web using SerpApi
    # --------------------------------

    serpapi_service = SerpApiService()

    all_sources = []

    for query in search_queries:

        try:
            results = serpapi_service.search(
                query["query"]
            )

            query["status"] = "completed"

            sources = normalize_results(
                results,
                query["id"],
            )

            all_sources.extend(sources)

        except Exception as e:

            query["status"] = "failed"

            print(
                f"SerpApi search failed for "
                f"'{query['query']}': {e}"
            )

    # --------------------------------
    # 5. Analyze collected evidence
    # --------------------------------

    evidence, findings = analyze_evidence(
       claims=claims,
       sources=all_sources,
       company_name=request.company_name,
   )

    # --------------------------------
    # 6. Build investigation trail
    # --------------------------------

    investigation_trail = []

    for claim in claims:

        claim_queries = [
            query
            for query in search_queries
            if query["claim_id"] == claim["id"]
        ]

        steps = [
            {
                "type": "claim",
                "content": claim["text"],
            }
        ]

        for query in claim_queries:

            steps.append(
                {
                    "type": "query",
                    "content": query["query"],
                }
            )

            steps.append(
                {
                    "type": "search",
                    "content": (
                        "SerpApi search "
                        f"{query['status']}"
                    ),
                }
            )

        investigation_trail.append(
            {
                "claim_id": claim["id"],
                "steps": steps,
            }
        )

    # --------------------------------
    # 7. Return investigation report
    # --------------------------------

    return {
        "investigation_id": "inv_demo_001",

        "overall_finding": {
            "status": "needs_verification",
            "label": "Needs verification",
        },

        "claims": claims,

        "search_queries": search_queries,

        "sources": all_sources,

        "evidence": evidence,

        "findings": findings,

        "explanation": (
            f"TrustLens extracted {len(claims)} claims "
            f"and generated {len(search_queries)} "
            "targeted verification searches. "
            f"SerpApi retrieved live evidence from "
            f"{len(all_sources)} sources."
        ),

        "investigation_trail": investigation_trail,
    }