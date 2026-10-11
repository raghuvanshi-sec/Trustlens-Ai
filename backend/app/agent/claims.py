import re


def extract_claims(
    message_text: str,
    company_name: str,
    application_url: str | None = None,
    job_listing_url: str | None = None,
    recruiter_details: dict | None = None,
) -> list[dict]:
    claims = []
    if company_name:
        claims.append({"id": "claim_company", "text": f"{company_name} is the company associated with this job offer.", "type": "company_identity", "importance": "high", "verification_status": "needs_verification"})
    if message_text:
        claims.append({"id": "claim_employment", "text": f"The sender claims to offer employment at {company_name}.", "type": "employment", "importance": "high", "verification_status": "needs_verification"})
    if application_url:
        claims.append({"id": "claim_application_url", "text": f"The application URL is {application_url}.", "type": "application_url", "importance": "high", "verification_status": "needs_verification"})
    if job_listing_url:
        claims.append({"id": "claim_job_listing", "text": f"The provided job listing is {job_listing_url}.", "type": "job_listing", "importance": "medium", "verification_status": "needs_verification"})
    if recruiter_details:
        name = recruiter_details.get("name")
        email = recruiter_details.get("email")
        if name:
            claims.append({"id": "claim_recruiter", "text": f"{name} claims to represent {company_name}.", "type": "recruiter_identity", "importance": "high", "verification_status": "needs_verification"})
        if email:
            claims.append({"id": "claim_contact", "text": f"The recruiter uses the contact email {email}.", "type": "contact_information", "importance": "medium", "verification_status": "needs_verification"})
        phone = recruiter_details.get("phone")
        if phone:
            claims.append({"id": "claim_phone", "text": f"The recruiter provided the contact phone number {phone}.", "type": "contact_information", "importance": "medium", "verification_status": "needs_verification"})
    payment_patterns = [r"\bregistration fee\b", r"\bprocessing fee\b", r"\bsecurity deposit\b", r"\bapplication fee\b", r"\btraining fee\b", r"\brecruitment fee\b", r"\bupfront payment\b", r"\bpay\b.{0,50}\b(fee|deposit|charges|amount|rupees|rs)\b", r"\b(pay|send|transfer|deposit|remit)\b.{0,60}(₹\s?[\d,]+|\b\d[\d,]*\s?(?:rupees|rs)\b)"]
    for pattern in payment_patterns:
        for match in re.finditer(pattern, message_text, re.IGNORECASE):
            before = message_text[max(0, match.start() - 55):match.start()]
            same_sentence = before.rsplit(".", 1)[-1].rsplit("!", 1)[-1].rsplit("?", 1)[-1]
            explicit_negation = re.search(r"\b(?:no|not|never|without|don't|do not|doesn't|does not|won't|will not|isn't|is not)\b[^;:]{0,45}$", same_sentence, re.IGNORECASE)
            negated_fee_phrase = re.search(r"\b(?:no|zero|without)\s+(?:any\s+)?(?:registration|processing|security|application|training|recruitment)\s+fee\b", match.group(0), re.IGNORECASE)
            if explicit_negation or negated_fee_phrase:
                continue
            claims.append({"id": "claim_payment", "text": "The message appears to request a payment or fee.", "type": "payment", "importance": "high", "verification_status": "needs_verification"})
            return claims
    return claims
