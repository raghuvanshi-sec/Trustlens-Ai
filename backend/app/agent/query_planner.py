import re
from urllib.parse import urlparse


_ROLE_WORDS = re.compile(
    r"\b(engineer|developer|analyst|intern|designer|manager|consultant|scientist|architect|"
    r"administrator|tester|qa|support|associate|specialist|trainee|executive)\b",
    re.IGNORECASE,
)
_EXPERIENCE_OR_LOCATION = re.compile(
    r"\s*(?:[-–—|•]\s*)?(?:\(?\s*\d+\s*(?:[-–to]+\s*\d+)?\s*\)?\s*years?\s+of\s+experience.*|"
    r"\d+\+?\s*years?.*|"
    r"(?:in|at)\s+[A-Z][A-Za-z .-]+,\s*[A-Z][A-Za-z .-]+.*)$",
    re.IGNORECASE,
)


def extract_job_title(message_text: str, company_name: str) -> str | None:
    text = message_text or ""
    patterns = [
        rf"selected by\s+{re.escape(company_name)}\s+for\s+(?:a|an)\s+(.+?)\s+(?:position|role)",
        r"selected\s+(?:for\s+)?(?:a|an)\s+(.+?)\s+(?:position|role)",
        r"(?:position|role)\s+(?:of\s+)?(?:a|an)\s+(.+?)(?:\.|,|$)",
        r"hired\s+(?:as\s+)?(?:a|an)\s+(.+?)(?:\.|,|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            title = match.group(1).strip(" \t.,:-")
            if 2 <= len(title) <= 80:
                return title

    # Job-board descriptions often begin with a title, followed by experience or location metadata.
    for line in text.splitlines()[:8]:
        candidate = re.sub(r"\s+", " ", line).strip(" \t.,:-|")
        if not candidate or len(candidate) > 100:
            continue
        candidate = _EXPERIENCE_OR_LOCATION.sub("", candidate).strip(" \t.,:-|")
        if 2 <= len(candidate) <= 80 and _ROLE_WORDS.search(candidate):
            # Avoid treating an entire promotional sentence as a job title.
            if len(candidate.split()) <= 9 and not re.search(r"[.!?]", candidate):
                return candidate
    return None


def extract_job_location(message_text: str) -> str | None:
    text = message_text or ""
    patterns = [
        r"\b(?:location|based in|located in)\s*[:\-]?\s*([A-Z][A-Za-z .'-]{2,40}(?:,\s*[A-Z][A-Za-z .'-]{2,30})?)",
        r"\b(Hyderabad|Bengaluru|Bangalore|Chennai|Pune|Mumbai|Delhi|Noida|Gurugram|Gurgaon|Kolkata|Indore|Remote)\b(?:,\s*([A-Z][A-Za-z .'-]+))?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return " ".join(part for part in match.groups() if part).strip()
    return None


def extract_recruiter_name(claim_text: str, company_name: str) -> str | None:
    suffix = f" claims to represent {company_name}."
    return claim_text.replace(suffix, "").strip() if suffix in claim_text else None


def extract_email(claim_text: str) -> str | None:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", claim_text)
    return match.group(0) if match else None


def plan_queries(claims: list[dict], company_name: str, message_text: str, application_url: str | None = None) -> list[dict]:
    queries = []
    job_title = extract_job_title(message_text, company_name)
    job_location = extract_job_location(message_text)

    def add_query(claim_id: str, query: str, purpose: str):
        # Keep query count bounded and the trail auditable.
        if any(item["claim_id"] == claim_id and item["query"].casefold() == query.casefold() for item in queries):
            return
        queries.append({
            "id": f"query_{len(queries) + 1:03d}",
            "claim_id": claim_id,
            "query": query,
            "purpose": purpose,
            "status": "planned",
        })

    for claim in claims:
        claim_id, claim_type = claim["id"], claim["type"]
        if claim_type == "company_identity":
            add_query(claim_id, f'"{company_name}" official website', "Find the company's official web presence")
            add_query(claim_id, f'"{company_name}" company profile', "Disambiguate organizations using the same or similar name")
            add_query(claim_id, f'"{company_name}" careers', "Find an established careers presence")
        elif claim_type == "employment":
            if job_title:
                add_query(claim_id, f'"{company_name}" "{job_title}"', "Search for the exact role and employer together")
                if job_location:
                    add_query(claim_id, f'"{company_name}" "{job_title}" "{job_location}"', "Cross-check the role against the stated location")
                add_query(claim_id, f'"{company_name}" careers "{job_title}"', "Look for the role on company hiring pages")
                add_query(claim_id, f'"{company_name}" "{job_title}" job opening', "Find independent references to the specific vacancy")
            else:
                add_query(claim_id, f'"{company_name}" jobs careers', "Search for current hiring information")
                add_query(claim_id, f'"{company_name}" recruitment hiring jobs', "Broaden coverage for hiring references")
        elif claim_type == "application_url" and application_url:
            domain = urlparse(application_url).hostname or ""
            if domain:
                add_query(claim_id, f'"{domain}"', "Find public references to the supplied application domain")
                add_query(claim_id, f'"{domain}" "{company_name}"', "Check whether the application domain is associated with the employer")
        elif claim_type == "job_listing":
            match = re.search(r"https?://[^\s]+", claim.get("text", ""))
            if match:
                domain = urlparse(match.group(0)).hostname or ""
                if domain:
                    add_query(claim_id, f'"{domain}" "{company_name}"', "Check whether the listing domain is associated with the employer")
            if job_title:
                add_query(claim_id, f'"{company_name}" "{job_title}" job listing', "Search for independent references to the claimed listing")
        elif claim_type == "recruiter_identity":
            recruiter_name = extract_recruiter_name(claim["text"], company_name)
            if recruiter_name:
                add_query(claim_id, f'"{recruiter_name}" "{company_name}" recruiter', "Check whether the recruiter is associated with the employer")
                add_query(claim_id, f'"{recruiter_name}" "{company_name}" LinkedIn', "Look for professional evidence connecting the recruiter to the employer")
        elif claim_type == "contact_information":
            email = extract_email(claim["text"])
            phone_match = re.search(r"(?:phone number\s+)([+()\d .-]{7,25})", claim.get("text", ""), re.IGNORECASE)
            if email:
                add_query(claim_id, f'"{email}"', "Search for public references to the contact email")
                add_query(claim_id, f'"{email.split("@")[-1]}" "{company_name}"', "Check whether the email domain is associated with the employer")
            elif phone_match:
                add_query(claim_id, f'"{phone_match.group(1).strip()}" "{company_name}" recruiter', "Search for public references to the supplied recruiter phone number")
        elif claim_type == "payment":
            add_query(claim_id, f'"{company_name}" recruitment fee', "Check for public information about recruitment fees")
            add_query(claim_id, f'"{company_name}" recruitment scam payment', "Search for independent reports involving recruitment scams or payment requests")
    return queries
