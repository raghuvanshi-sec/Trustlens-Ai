from urllib.parse import urlparse


def normalize_domain(domain: str) -> str:
    """Normalize a domain for comparison."""
    domain = domain.lower().strip()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def get_source_domain(source: dict) -> str:
    """Get a normalized domain from a source."""
    domain = source.get("domain", "")

    if not domain and source.get("url"):
        domain = urlparse(source["url"]).netloc

    return normalize_domain(domain)


def source_matches_company(
    source: dict,
    company_name: str,
) -> bool:
    """
    Basic company-name/domain matching.

    This is intentionally conservative.
    """
    title = source.get("title", "").lower()
    snippet = source.get("snippet", "").lower()
    company = company_name.lower().strip()

    domain = get_source_domain(source)

    company_tokens = [
        token
        for token in company.replace(",", " ").split()
        if len(token) > 2
    ]

    domain_match = any(
        token in domain
        for token in company_tokens
    )

    text_match = company in title or company in snippet

    return domain_match or text_match


def analyze_claim(
    claim: dict,
    sources: list[dict],
    company_name: str,
) -> list[dict]:
    """
    Analyze collected sources against a single claim.

    This first version deliberately avoids aggressive
    scam/fraud conclusions.
    """

    claim_id = claim["id"]
    claim_type = claim["type"]

    evidence = []

    matching_sources = [
        source
        for source in sources
        if source_matches_company(
            source,
            company_name,
        )
    ]

    # --------------------------------
    # Company identity
    # --------------------------------

    if claim_type == "company_identity":

        official_sources = [
            source
            for source in matching_sources
            if source.get("source_type") == "official"
        ]

        if official_sources:

            for source in official_sources[:3]:
                evidence.append({
                    "id": f"evidence_{claim_id}_{len(evidence)+1}",
                    "claim_id": claim_id,
                    "source_id": source["id"],
                    "relation": "supports",
                    "strength": "strong",
                    "summary": (
                        f"The source provides evidence of "
                        f"{company_name}'s official web presence."
                    ),
                })

        else:
            evidence.append({
                "id": f"evidence_{claim_id}_1",
                "claim_id": claim_id,
                "source_id": None,
                "relation": "missing",
                "strength": "weak",
                "summary": (
                    "No authoritative company source "
                    "was identified in the collected results."
                ),
            })

    # --------------------------------
    # Employment / job claim
    # --------------------------------

    elif claim_type in {
        "employment",
        "job_listing",
    }:

        job_sources = [
            source
            for source in matching_sources
            if source.get("source_type")
            in {
                "official",
                "job_board",
            }
        ]

        if job_sources:

            for source in job_sources[:3]:
                evidence.append({
                    "id": f"evidence_{claim_id}_{len(evidence)+1}",
                    "claim_id": claim_id,
                    "source_id": source["id"],
                    "relation": "supports",
                    "strength": "medium",
                    "summary": (
                        "The collected source provides evidence "
                        "that the company has relevant hiring "
                        "or job information."
                    ),
                })

        else:
            evidence.append({
                "id": f"evidence_{claim_id}_1",
                "claim_id": claim_id,
                "source_id": None,
                "relation": "missing",
                "strength": "weak",
                "summary": (
                    "The claimed employment opportunity could "
                    "not be independently verified from the "
                    "collected sources."
                ),
            })

    # --------------------------------
    # Recruiter identity
    # --------------------------------

    elif claim_type == "recruiter_identity":

        professional_sources = [
            source
            for source in sources
            if source.get("source_type")
            == "professional_network"
        ]

        if professional_sources:

            evidence.append({
                "id": f"evidence_{claim_id}_1",
                "claim_id": claim_id,
                "source_id": professional_sources[0]["id"],
                "relation": "context",
                "strength": "weak",
                "summary": (
                    "Professional-network results were found, "
                    "but matching a person's identity to the "
                    "sender requires additional verification."
                ),
            })

        else:
            evidence.append({
                "id": f"evidence_{claim_id}_1",
                "claim_id": claim_id,
                "source_id": None,
                "relation": "missing",
                "strength": "weak",
                "summary": (
                    "No professional evidence was identified "
                    "for the claimed recruiter."
                ),
            })

    # --------------------------------
    # Application URL
    # --------------------------------

    elif claim_type == "application_url":

        evidence.append({
            "id": f"evidence_{claim_id}_1",
            "claim_id": claim_id,
            "source_id": None,
            "relation": "missing",
            "strength": "weak",
            "summary": (
                "The application domain requires independent "
                "verification against the company's known "
                "official web presence."
            ),
        })

    # --------------------------------
    # Contact information
    # --------------------------------

    elif claim_type == "contact_information":

        evidence.append({
            "id": f"evidence_{claim_id}_1",
            "claim_id": claim_id,
            "source_id": None,
            "relation": "missing",
            "strength": "weak",
            "summary": (
                "The supplied contact information could not "
                "be conclusively associated with the company "
                "from the collected evidence."
            ),
        })

    # --------------------------------
    # Payment
    # --------------------------------

    elif claim_type == "payment":

        evidence.append({
            "id": f"evidence_{claim_id}_1",
            "claim_id": claim_id,
            "source_id": None,
            "relation": "context",
            "strength": "medium",
            "summary": (
                "The message contains a payment-related claim. "
                "This requires verification against authoritative "
                "recruitment information."
            ),
        })

    # --------------------------------
    # Fallback
    # --------------------------------

    else:

        evidence.append({
            "id": f"evidence_{claim_id}_1",
            "claim_id": claim_id,
            "source_id": None,
            "relation": "missing",
            "strength": "weak",
            "summary": (
                "Insufficient evidence was collected "
                "to evaluate this claim."
            ),
        })

    return evidence


def analyze_evidence(
    claims: list[dict],
    sources: list[dict],
    company_name: str,
) -> tuple[list[dict], list[dict]]:

    all_evidence = []
    findings = []

    for claim in claims:

        claim_evidence = analyze_claim(
            claim=claim,
            sources=sources,
            company_name=company_name,
        )

        all_evidence.extend(claim_evidence)

        relations = {
            evidence["relation"]
            for evidence in claim_evidence
        }

        if "contradicts" in relations:
            status = "conflicting"

        elif "supports" in relations:
            status = "supported"

        else:
            status = "needs_verification"

        findings.append({
            "claim_id": claim["id"],
            "status": status,
            "summary": build_finding_summary(
                status,
                claim,
            ),
            "evidence_ids": [
                evidence["id"]
                for evidence in claim_evidence
            ],
        })

    return all_evidence, findings


def build_finding_summary(
    status: str,
    claim: dict,
) -> str:

    if status == "supported":
        return (
            "Collected evidence supports part of this claim, "
            "but support does not necessarily establish the "
            "authenticity of the entire offer."
        )

    if status == "conflicting":
        return (
            "Collected sources contain conflicting evidence "
            "related to this claim."
        )

    return (
        "The available evidence is insufficient to "
        "independently verify this claim."
    )