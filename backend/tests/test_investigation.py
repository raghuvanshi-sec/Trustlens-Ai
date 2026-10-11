from fastapi.testclient import TestClient
from app.agent.claims import extract_claims
from app.main import app
from app.api.routes import investigation as investigation_route
from app.services.evidence import analyze_evidence, summarize_overall_finding
from app.services.sources import classify_source, normalize_results


def test_salary_amount_alone_is_not_misclassified_as_payment_request():
    claims = extract_claims("The role pays ₹80,000 per month.", "Example Corporation")
    assert not any(claim["type"] == "payment" for claim in claims)


def test_recruitment_fee_is_detected_as_risk_signal():
    claims = extract_claims("Pay a registration fee of ₹2,000 to secure the job.", "Example Corporation")
    assert any(claim["type"] == "payment" for claim in claims)


def test_company_domain_is_only_candidate_not_proven_official():
    assert classify_source("https://example.com/careers", company_name="Example Corporation") == "official_candidate"


def test_normalized_results_include_valid_source_metadata():
    sources = normalize_results({"organic_results": [{"title": "Example jobs", "link": "https://jobs.example.com/opening", "snippet": "Example Corporation"}, {"title": "Missing URL"}]}, "query_001", "Example Corporation")
    assert len(sources) == 1 and sources[0]["query_id"] == "query_001" and sources[0]["domain"] == "jobs.example.com"


def test_evidence_is_mapped_to_query_claim_not_all_company_results():
    claims = [{"id": "company", "type": "company_identity", "text": "Example Corporation identity"}, {"id": "recruiter", "type": "recruiter_identity", "text": "Alex Smith claims to represent Example Corporation."}]
    sources = [{"id": "s1", "claim_id": "company", "source_type": "official_candidate", "title": "Example Corporation", "snippet": "Company website", "domain": "example.com", "url": "https://example.com"}]
    evidence, findings = analyze_evidence(claims, sources, "Example Corporation")
    recruiter_evidence = [item for item in evidence if item["claim_id"] == "recruiter"]
    assert len(recruiter_evidence) == 1 and recruiter_evidence[0]["source_id"] is None
    assert findings[1]["status"] == "needs_verification"


def test_overall_finding_is_derived_from_payment_risk():
    overall = summarize_overall_finding([{"id": "payment", "type": "payment"}], [{"claim_id": "payment", "status": "risk_signal"}], [])
    assert overall["status"] == "elevated_risk_signals"


def test_api_returns_report_when_search_key_is_missing(monkeypatch):
    class MissingSearchService:
        def __init__(self):
            raise RuntimeError("SERPAPI_API_KEY is not configured with a valid key.")
    monkeypatch.setattr(investigation_route, "SerpApiService", MissingSearchService)
    response = TestClient(app).post("/api/investigate", json={"message_text": "You have been selected for a software engineer role. Pay a registration fee to continue.", "company_name": "Example Corporation"})
    assert response.status_code == 200
    body = response.json()
    assert body["investigation_id"].startswith("inv_") and body["overall_finding"]["status"] == "elevated_risk_signals"
    assert body["search_queries"] and all(query["status"] == "failed" for query in body["search_queries"])
    assert body["evidence"]


def test_api_returns_sources_and_claim_level_evidence(monkeypatch):
    class FakeSearchService:
        def __init__(self): pass
        def search(self, query):
            if "official website" in query or "careers" in query:
                return {"organic_results": [{"title": "Example Corporation — Careers", "link": "https://example.com/careers", "snippet": "Example Corporation career opportunities"}]}
            return {"organic_results": []}
    monkeypatch.setattr(investigation_route, "SerpApiService", FakeSearchService)
    response = TestClient(app).post("/api/investigate", json={"message_text": "I received a job offer from Example Corporation.", "company_name": "Example Corporation"})
    assert response.status_code == 200
    body = response.json()
    assert body["sources"] and all(source.get("claim_id") for source in body["sources"])
    assert body["investigation_trail"] and body["overall_finding"]["status"] != "elevated_risk_signals"


def test_blank_required_fields_are_rejected():
    response = TestClient(app).post("/api/investigate", json={"message_text": "   ", "company_name": "Example Corporation"})
    assert response.status_code == 422


def test_non_http_application_url_is_rejected():
    response = TestClient(app).post("/api/investigate", json={"message_text": "Please apply for this role.", "company_name": "Example Corporation", "application_url": "javascript:alert(1)"})
    assert response.status_code == 422


def test_recruiter_phone_becomes_a_separate_claim():
    claims = extract_claims("Please contact the recruiter about this role.", "Example Corporation", recruiter_details={"phone": "+91 98765 43210"})
    phone_claims = [claim for claim in claims if claim["id"] == "claim_phone"]
    assert len(phone_claims) == 1 and phone_claims[0]["type"] == "contact_information"


def test_source_deduplication_keeps_claim_relationships():
    from app.services.sources import deduplicate_sources
    sources = [{"id": "s1", "claim_id": "claim_company", "url": "https://example.com/careers"}, {"id": "s2", "claim_id": "claim_company", "url": "https://example.com/careers/"}, {"id": "s3", "claim_id": "claim_employment", "url": "https://example.com/careers"}]
    result = deduplicate_sources(sources)
    assert [source["id"] for source in result] == ["s1", "s3"]


def test_health_endpoint_returns_service_status():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200 and response.json() == {"status": "ok", "service": "TrustLens AI"}


def test_explicit_no_fee_statement_is_not_misclassified_as_payment_request():
    claims = extract_claims("There is no registration fee and we do not ask candidates to pay any amount.", "Example Corporation")
    assert not any(claim["type"] == "payment" for claim in claims)


def test_failed_searches_keep_overall_finding_incomplete_even_with_some_support():
    overall = summarize_overall_finding([{"id": "company", "type": "company_identity"}], [{"claim_id": "company", "status": "supported"}], [{"status": "completed"}, {"status": "failed"}])
    assert overall["status"] == "investigation_incomplete"


def test_attacker_domain_is_not_classified_as_government():
    assert classify_source("https://example.gov.attacker.com/path") == "other"


def test_non_http_search_results_are_discarded():
    sources = normalize_results({"organic_results": [{"title": "FTP result", "link": "ftp://example.com/file"}, {"title": "Unsafe scheme", "link": "javascript:alert(1)"}, {"title": "Valid result", "link": "https://example.com/careers"}]}, "query_001", "Example Corporation")
    assert len(sources) == 1 and sources[0]["url"] == "https://example.com/careers"


def test_company_match_does_not_use_partial_domain_word():
    from app.services.evidence import source_matches_company
    assert not source_matches_company({"title": "Acmeon careers", "snippet": "Open positions", "domain": "acmeon.example"}, "Acme")


def test_phone_claim_generates_targeted_search_query():
    from app.agent.query_planner import plan_queries
    claims = extract_claims("Please contact the recruiter about this role.", "Example Corporation", recruiter_details={"phone": "+91 98765 43210"})
    queries = plan_queries(claims, "Example Corporation", "Please contact the recruiter about this role.")
    phone_queries = [query for query in queries if query["claim_id"] == "claim_phone"]
    assert len(phone_queries) == 1 and "98765" in phone_queries[0]["query"]


def test_individual_search_failure_is_reported_without_exposing_exception(monkeypatch):
    class FailingSearchService:
        def __init__(self): pass
        def search(self, query): raise RuntimeError("private transport details")
    monkeypatch.setattr(investigation_route, "SerpApiService", FailingSearchService)
    response = TestClient(app).post("/api/investigate", json={"message_text": "I received a job offer from Example Corporation.", "company_name": "Example Corporation"})
    assert response.status_code == 200
    body = response.json()
    assert body["overall_finding"]["status"] == "investigation_incomplete"
    assert all(query["status"] == "failed" for query in body["search_queries"])
    assert "private transport details" not in response.text


def test_serpapi_placeholder_key_is_rejected(monkeypatch):
    from app.services.serpapi import SerpApiService
    monkeypatch.setenv("SERPAPI_API_KEY", "your_serpapi_key_here")
    try:
        SerpApiService()
    except RuntimeError as exc:
        assert "not configured" in str(exc)
    else:
        raise AssertionError("Placeholder SerpApi key should be rejected")
