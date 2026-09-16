from fastapi import APIRouter

from app.models.schemas import InvestigationRequest, InvestigationResponse
from app.agent.claims import extract_claims
from app.agent.query_planner import plan_queries

router = APIRouter()


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate(request: InvestigationRequest):

    recruiter_details = None

    if request.recruiter_details:
        recruiter_details = request.recruiter_details.model_dump()

    claims = extract_claims(
        message_text=request.message_text,
        company_name=request.company_name,
        application_url=request.application_url,
        job_listing_url=request.job_listing_url,
        recruiter_details=recruiter_details,
    )
    search_queries = plan_queries(
        claims=claims,
        company_name=request.company_name,
        application_url=request.application_url,
    )

    return {
        "investigation_id": "inv_demo_001",

        "overall_finding": {
            "status": "needs_verification",
            "label": "Needs verification"
        },

        "claims": claims,

        "search_queries": [],

        "sources": [],

        "findings": [
            {
                "claim_id": claim["id"],
                "status": "needs_verification",
                "summary": "This claim requires independent verification."
            }
            for claim in claims
        ],

        "explanation": (
            "TrustLens extracted claims from the submitted job offer. "
            "The next stage will generate targeted searches for these claims."
        ),

        "investigation_trail": [
            {
                "claim_id": claim["id"],
                "steps": [
                    {
                        "type": "claim",
                        "content": claim["text"]
                    }
                ]
            }
            for claim in claims
        ]
    }