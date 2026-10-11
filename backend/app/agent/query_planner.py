import re
from urllib.parse import urlparse


def extract_job_title(message_text: str, company_name: str) -> str | None:
    patterns = [rf"selected by\s+{re.escape(company_name)}\s+for\s+(?:a|an)\s+(.+?)\s+(?:position|role)", r"selected\s+(?:for\s+)?(?:a|an)\s+(.+?)\s+(?:position|role)", r"(?:position|role)\s+(?:of\s+)?(?:a|an)\s+(.+?)(?:\.|,|$)", r"hired\s+(?:as\s+)?(?:a|an)\s+(.+?)(?:\.|,|$)"]
    for pattern in patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            if len(title) <= 80:
                return title
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
    def add_query(claim_id: str, query: str, purpose: str):
        queries.append({"id": f"query_{len(queries) + 1:03d}", "claim_id": claim_id, "query": query, "purpose": purpose, "status": "planned"})
    for claim in claims:
        claim_id, claim_type = claim["id"], claim["type"]
        if claim_type == "company_identity":
            add_query(claim_id, f'"{company_name}" official website', "Verify the company's official web presence")
            add_query(claim_id, f'"{company_name}" careers', "Find the company's official or established careers presence")
        elif claim_type == "employment":
            if job_title:
                add_query(claim_id, f'"{company_name}" "{job_title}" jobs', "Verify whether the claimed job opportunity exists")
                add_query(claim_id, f'"{company_name}" careers "{job_title}"', "Search for the claimed role in the company's hiring information")
            else:
                add_query(claim_id, f'"{company_name}" jobs careers', "Search for the company's current hiring information")
        elif claim_type == "application_url" and application_url:
            domain = urlparse(application_url).netloc
            if domain:
                add_query(claim_id, f'"{domain}"', "Investigate the domain used by the application")
                add_query(claim_id, f'"{domain}" "{company_name}"', "Check whether the application domain is associated with the company")
        elif claim_type == "job_listing":
            match = re.search(r"https?://[^\s]+", claim.get("text", ""))
            if match:
                domain = urlparse(match.group(0)).netloc
                if domain:
                    add_query(claim_id, f'"{domain}" "{company_name}"', "Check whether the supplied listing domain is associated with the company")
            if job_title:
                add_query(claim_id, f'"{company_name}" "{job_title}" job listing', "Search for independent references to the claimed job listing")
        elif claim_type == "recruiter_identity":
            recruiter_name = extract_recruiter_name(claim["text"], company_name)
            if recruiter_name:
                add_query(claim_id, f'"{recruiter_name}" "{company_name}" recruiter', "Check whether the recruiter is associated with the company")
                add_query(claim_id, f'"{recruiter_name}" "{company_name}" LinkedIn', "Look for independent professional evidence connecting the recruiter to the company")
        elif claim_type == "contact_information":
            email = extract_email(claim["text"])
            phone_match = re.search(r"(?:phone number\s+)([+()\d .-]{7,25})", claim.get("text", ""), re.IGNORECASE)
            if email:
                add_query(claim_id, f'"{email}"', "Search for references to the recruiter's contact email")
                add_query(claim_id, f'"{email.split("@")[-1]}" "{company_name}"', "Check whether the email domain is associated with the company")
            elif phone_match:
                add_query(claim_id, f'"{phone_match.group(1).strip()}" "{company_name}" recruiter', "Search for public references to the supplied recruiter phone number")
        elif claim_type == "payment":
            add_query(claim_id, f'"{company_name}" recruitment fee', "Check whether recruitment fees are associated with the company")
            add_query(claim_id, f'"{company_name}" recruitment scam payment', "Search for independent reports involving recruitment scams or payment requests")
    return queries
