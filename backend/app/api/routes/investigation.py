import asyncio
from uuid import uuid4
from fastapi import APIRouter
from app.models.schemas import InvestigationRequest, InvestigationResponse
from app.agent.claims import extract_claims
from app.agent.query_planner import plan_queries
from app.services.serpapi import SerpApiService
from app.services.sources import deduplicate_sources, normalize_results
from app.services.evidence import analyze_evidence, summarize_overall_finding

router = APIRouter()
MAX_CONCURRENT_SEARCHES = 3


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate(request: InvestigationRequest):
    recruiter_details = request.recruiter_details.model_dump() if request.recruiter_details else None
    claims = extract_claims(request.message_text, request.company_name, request.application_url, request.job_listing_url, recruiter_details)
    search_queries = plan_queries(claims, request.company_name, request.message_text, request.application_url)
    all_sources = []
    search_service = None
    service_error = None
    try:
        search_service = SerpApiService()
    except Exception as exc:
        service_error = str(exc) or "Search service is unavailable."
    if search_service is None:
        for query in search_queries:
            query.update(status="failed", error=service_error, result_count=0)
    else:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEARCHES)
        async def execute_query(query: dict) -> list[dict]:
            async with semaphore:
                try:
                    results = await asyncio.to_thread(search_service.search, query["query"])
                    sources = normalize_results(results, query["id"], request.company_name)
                    for source in sources:
                        source["claim_id"] = query["claim_id"]
                    query.update(status="completed", result_count=len(sources))
                    return sources
                except Exception:
                    query.update(status="failed", error="Search provider request failed. Check connectivity, API configuration, and provider quota.", result_count=0)
                    return []
        source_batches = await asyncio.gather(*(execute_query(query) for query in search_queries))
        for batch in source_batches:
            all_sources.extend(batch)
    all_sources = deduplicate_sources(all_sources)
    evidence, findings = analyze_evidence(claims, all_sources, request.company_name)
    overall_finding = summarize_overall_finding(claims, findings, search_queries)
    investigation_trail = []
    for claim in claims:
        claim_queries = [query for query in search_queries if query["claim_id"] == claim["id"]]
        claim_evidence = [item for item in evidence if item["claim_id"] == claim["id"]]
        steps = [{"type": "claim", "content": claim["text"]}]
        for query in claim_queries:
            steps.append({"type": "query", "content": query["query"]})
            state = f"Search {query['status']}"
            if query.get("result_count") is not None:
                state += f"; {query['result_count']} result(s)"
            if query.get("error"):
                state += f" ({query['error']})"
            steps.append({"type": "search", "content": state})
        steps.extend({"type": "evidence", "content": item["summary"]} for item in claim_evidence)
        investigation_trail.append({"claim_id": claim["id"], "steps": steps})
    completed = sum(q.get("status") == "completed" for q in search_queries)
    explanation = f"TrustLens extracted {len(claims)} claims and planned {len(search_queries)} searches. {completed} searches completed and {len(all_sources)} distinct source result(s) were collected. Findings are investigative signals, not a definitive fraud determination."
    if service_error:
        explanation += " Live search is unavailable: configure SERPAPI_API_KEY and install backend requirements."
    return {"investigation_id": f"inv_{uuid4().hex[:12]}", "overall_finding": overall_finding, "claims": claims, "search_queries": search_queries, "sources": all_sources, "evidence": evidence, "findings": findings, "explanation": explanation, "investigation_trail": investigation_trail}
