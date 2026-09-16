import re


def extract_claims(
    message_text: str,
    company_name: str,
    application_url: str | None = None,
    job_listing_url: str | None = None,
    recruiter_details: dict | None = None,
) -> list[dict]:

    claims = []

    # Company identity
    if company_name:
        claims.append({
            "id": "claim_company",
            "text": f"{company_name} is the company associated with this job offer.",
            "type": "company_identity",
            "importance": "high",
            "verification_status": "needs_verification"
        })

    # Employment claim
    if message_text:
        claims.append({
            "id": "claim_employment",
            "text": f"The sender claims to offer employment at {company_name}.",
            "type": "employment",
            "importance": "high",
            "verification_status": "needs_verification"
        })

    # Application URL
    if application_url:
        claims.append({
            "id": "claim_application_url",
            "text": f"The application URL is {application_url}.",
            "type": "application_url",
            "importance": "high",
            "verification_status": "needs_verification"
        })

    # Job listing
    if job_listing_url:
        claims.append({
            "id": "claim_job_listing",
            "text": f"The provided job listing is {job_listing_url}.",
            "type": "job_listing",
            "importance": "medium",
            "verification_status": "needs_verification"
        })

    # Recruiter identity
    if recruiter_details:
        name = recruiter_details.get("name")
        email = recruiter_details.get("email")

        if name:
            claims.append({
                "id": "claim_recruiter",
                "text": f"{name} claims to represent {company_name}.",
                "type": "recruiter_identity",
                "importance": "high",
                "verification_status": "needs_verification"
            })

        if email:
            claims.append({
                "id": "claim_contact",
                "text": f"The recruiter uses the contact email {email}.",
                "type": "contact_information",
                "importance": "medium",
                "verification_status": "needs_verification"
            })

    # Payment-related claim detection
    payment_patterns = [
        r"₹\s?[\d,]+",
        r"\b\d[\d,]*\s?(rupees|rs)\b",
        r"\bregistration fee\b",
        r"\bprocessing fee\b",
        r"\bsecurity deposit\b",
        r"\bpay\b.*\bfee\b"
    ]

    for pattern in payment_patterns:
        if re.search(pattern, message_text, re.IGNORECASE):
            claims.append({
                "id": "claim_payment",
                "text": "The message appears to request a payment or fee.",
                "type": "payment",
                "importance": "high",
                "verification_status": "needs_verification"
            })
            break

    return claims