"""Conservative, claim-level evidence mapping for investigation reports."""
from urllib.parse import urlparse
import re


def normalize_domain(domain: str) -> str:
    domain = (domain or "").lower().strip().split(":", 1)[0]
    return domain[4:] if domain.startswith("www.") else domain


def get_source_domain(source: dict) -> str:
    domain = source.get("domain", "")
    if not domain and source.get("url"):
        domain = urlparse(source["url"]).hostname or ""
    return normalize_domain(domain)


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) >= 3]


def source_matches_company(source: dict, company_name: str) -> bool:
    company = (company_name or "").strip().lower()
    title, snippet, domain = (source.get("title") or "").lower(), (source.get("snippet") or "").lower(), get_source_domain(source)
    if not company:
        return False
    if re.search(rf"(?<![a-z0-9]){re.escape(company)}(?![a-z0-9])", title) or re.search(rf"(?<![a-z0-9]){re.escape(company)}(?![a-z0-9])", snippet):
        return True
    ignored = {"inc", "llc", "ltd", "limited", "private", "pvt", "corporation", "corp", "company"}
    tokens = [token for token in _tokens(company) if token not in ignored]
    labels = [part for label in domain.split(".")[:-1] for part in label.split("-") if part not in {"www", "careers", "jobs", "apply", "recruitment"}]
    return bool(tokens and any(token == label for token in tokens for label in labels))


def _add(claim_id: str, source: dict | None, relation: str, strength: str, summary: str, index: int) -> dict:
    return {"id": f"evidence_{claim_id}_{index}", "claim_id": claim_id, "source_id": source.get("id") if source else None, "relation": relation, "strength": strength, "summary": summary}


def analyze_claim(claim: dict, sources: list[dict], company_name: str) -> list[dict]:
    claim_id, claim_type = claim["id"], claim["type"]
    related = [source for source in sources if source.get("claim_id") == claim_id]
    if sources and not any("claim_id" in source for source in sources):
        related = [source for source in sources if source_matches_company(source, company_name)]
    evidence = []
    if claim_type == "company_identity":
        candidates = [source for source in related if source.get("source_type") in {"official", "official_candidate"}]
        if candidates:
            for index, source in enumerate(candidates[:3], 1):
                if source.get("source_type") == "official":
                    evidence.append(_add(claim_id, source, "supports", "strong", "This result is from a domain classified as an official source. Confirm that it is the correct company before relying on it.", index))
                else:
                    evidence.append(_add(claim_id, source, "context", "weak", "The domain resembles the company name, but domain ownership has not been independently confirmed.", index))
        else:
            evidence.append(_add(claim_id, None, "missing", "weak", "No authoritative company source was identified in the collected results.", 1))
    elif claim_type in {"employment", "job_listing"}:
        candidates = [source for source in related if source.get("source_type") in {"official", "official_candidate", "job_board"} and source_matches_company(source, company_name)]
        if candidates:
            for index, source in enumerate(candidates[:3], 1):
                strength = "medium" if source.get("source_type") in {"official", "job_board"} else "weak"
                evidence.append(_add(claim_id, source, "supports", strength, "This result contains potentially relevant hiring information. It does not by itself authenticate the specific message or recruiter.", index))
        else:
            evidence.append(_add(claim_id, None, "missing", "weak", "The claimed employment opportunity could not be independently verified from relevant collected results.", 1))
    elif claim_type == "recruiter_identity":
        person = claim.get("text", "").split(" claims to represent ", 1)[0].strip().lower()
        candidates = [source for source in related if source.get("source_type") == "professional_network" and person and person in ((source.get("title", "") + " " + source.get("snippet", "")).lower()) and source_matches_company(source, company_name)]
        if candidates:
            evidence.append(_add(claim_id, candidates[0], "context", "weak", "A professional-network result appears to mention the recruiter and company. Profile identity and control of the sending account still require verification.", 1))
        else:
            evidence.append(_add(claim_id, None, "missing", "weak", "No result directly connecting the named recruiter with the company was identified.", 1))
    elif claim_type == "application_url":
        match = re.search(r"https?://[^\s]+", claim.get("text", ""))
        claimed_domain = normalize_domain(urlparse(match.group(0)).hostname or "") if match else ""
        exact = [source for source in related if claimed_domain and (get_source_domain(source) == claimed_domain or get_source_domain(source).endswith("." + claimed_domain))]
        company_related = [source for source in related if source_matches_company(source, company_name)]
        if exact:
            evidence.append(_add(claim_id, exact[0], "context", "weak", "Search results reference the supplied domain. This does not establish that the domain is controlled by the company or that the page is safe.", 1))
        elif company_related:
            evidence.append(_add(claim_id, company_related[0], "context", "weak", f"Company-related results were found, but the supplied domain ({claimed_domain or 'unknown'}) was not confirmed as company-controlled.", 1))
        else:
            evidence.append(_add(claim_id, None, "missing", "weak", "The supplied application domain could not be independently associated with the company from collected results.", 1))
    elif claim_type == "contact_information":
        match = re.search(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", claim.get("text", ""))
        email_domain = normalize_domain(match.group(1)) if match else ""
        matching = [source for source in related if email_domain and (get_source_domain(source) == email_domain or email_domain in ((source.get("snippet", "") + " " + source.get("title", "")).lower()))]
        if matching:
            evidence.append(_add(claim_id, matching[0], "context", "weak", "A result references the supplied email domain or address. Sender authenticity still requires an independently verified contact channel.", 1))
        else:
            evidence.append(_add(claim_id, None, "missing", "weak", "The supplied contact information could not be independently associated with the company.", 1))
    elif claim_type == "payment":
        evidence.append(_add(claim_id, None, "risk_signal", "high", "The submitted message appears to request a recruitment-related payment. Treat this as a warning sign and independently verify through the company's official contact channel before paying.", 1))
    else:
        evidence.append(_add(claim_id, None, "missing", "weak", "Insufficient evidence was collected to evaluate this claim.", 1))
    return evidence


def build_finding_summary(status: str, claim: dict) -> str:
    if status == "supported":
        return "Collected evidence supports part of this claim; it does not authenticate the entire offer or sender."
    if status == "conflicting":
        return "Collected sources contain conflicting evidence related to this claim."
    if status == "risk_signal":
        return "This claim contains a risk indicator that warrants caution and independent verification."
    return "The available evidence is insufficient to independently verify this claim."


def analyze_evidence(claims: list[dict], sources: list[dict], company_name: str) -> tuple[list[dict], list[dict]]:
    all_evidence, findings = [], []
    for claim in claims:
        items = analyze_claim(claim, sources, company_name)
        all_evidence.extend(items)
        relations = {item["relation"] for item in items}
        status = "conflicting" if "contradicts" in relations else "risk_signal" if "risk_signal" in relations else "supported" if "supports" in relations else "needs_verification"
        findings.append({"claim_id": claim["id"], "status": status, "summary": build_finding_summary(status, claim), "evidence_ids": [item["id"] for item in items]})
    return all_evidence, findings


def summarize_overall_finding(claims: list[dict], findings: list[dict], search_queries: list[dict]) -> dict:
    statuses = {finding.get("status") for finding in findings}
    failed = sum(query.get("status") == "failed" for query in search_queries)
    payment = any(claim.get("type") == "payment" for claim in claims)
    if payment or "risk_signal" in statuses:
        return {"status": "elevated_risk_signals", "label": "Elevated risk signals", "summary": "A recruitment-related payment request was detected. Do not pay until the opportunity is independently verified."}
    if "conflicting" in statuses:
        return {"status": "conflicting_evidence", "label": "Conflicting evidence", "summary": "Some collected information conflicts. Verify the claims through official channels before proceeding."}
    if failed:
        return {"status": "investigation_incomplete", "label": "Investigation incomplete", "summary": "One or more searches failed. Review any available evidence, but retry the investigation before drawing a conclusion."}
    if findings and all(finding.get("status") == "supported" for finding in findings):
        return {"status": "some_claims_supported", "label": "Claims supported; offer not authenticated", "summary": "Collected sources support the checked claims, but this does not prove the message or sender is authentic."}
    return {"status": "needs_verification", "label": "Needs verification", "summary": "Evidence is incomplete or mixed. Verify the sender and opportunity through independently obtained official contact details."}
