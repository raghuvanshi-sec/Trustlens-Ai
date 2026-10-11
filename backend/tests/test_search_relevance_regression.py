from app.agent.query_planner import extract_job_title


def test_extracts_role_from_job_board_heading():
    text = "Full Stack Engineer (1 - 3) Years of experience\nHyderabad, Telangana, India"
    assert extract_job_title(text, "WorkElate") == "Full Stack Engineer"

from app.services.sources import deduplicate_sources
from app.services.evidence import analyze_evidence


def test_duplicate_urls_merge_claim_associations():
    sources = [
        {"id": "s1", "url": "https://example.org/jobs?utm_source=search", "claim_id": "claim_company", "query_id": "query_001", "title": "Jobs"},
        {"id": "s2", "url": "https://www.example.org/jobs#role", "claim_id": "claim_employment", "query_id": "query_002", "title": "Jobs"},
    ]
    result = deduplicate_sources(sources)
    assert len(result) == 1
    assert set(result[0]["claim_ids"]) == {"claim_company", "claim_employment"}
    assert set(result[0]["query_ids"]) == {"query_001", "query_002"}


def test_company_product_page_does_not_support_specific_job():
    claims = [{"id": "claim_employment", "type": "employment", "text": "The sender claims to offer employment at WorkElate."}]
    sources = [{
        "id": "s1", "url": "https://workelate.example/about", "domain": "workelate.example",
        "source_type": "official_candidate", "title": "WorkElate productivity platform",
        "snippet": "WorkElate is an AI-native productivity platform.", "claim_id": "claim_employment",
    }]
    evidence, findings = analyze_evidence(
        claims, sources, "WorkElate",
        "Full Stack Engineer (1 - 3) Years of experience\nHyderabad, Telangana, India",
    )
    assert evidence[0]["relation"] == "missing"
    assert findings[0]["status"] == "needs_verification"
