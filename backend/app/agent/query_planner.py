from urllib.parse import urlparse


def plan_queries(
    claims: list[dict],
    company_name: str,
    application_url: str | None = None,
) -> list[dict]:

    queries = []
    query_number = 1

    def add_query(claim_id: str, query: str, purpose: str):
        nonlocal query_number

        queries.append({
            "id": f"query_{query_number:03d}",
            "claim_id": claim_id,
            "query": query,
            "purpose": purpose,
            "status": "planned"
        })

        query_number += 1

    for claim in claims:

        claim_id = claim["id"]
        claim_type = claim["type"]

        if claim_type == "company_identity":

            add_query(
                claim_id,
                f"{company_name} official website",
                "Verify the company's official web presence"
            )

            add_query(
                claim_id,
                f"site:{company_name.lower().replace(' ', '')}.com careers",
                "Look for an official careers presence"
            )

        elif claim_type == "employment":

            add_query(
                claim_id,
                f"{company_name} software engineer jobs",
                "Verify whether the claimed employment opportunity exists"
            )

            add_query(
                claim_id,
                f"{company_name} careers software engineer",
                "Search the company's hiring information"
            )

        elif claim_type == "application_url":

            if application_url:
                domain = urlparse(application_url).netloc

                add_query(
                    claim_id,
                    domain,
                    "Investigate the domain used for the application"
                )

                add_query(
                    claim_id,
                    f'"{domain}" {company_name}',
                    "Check whether the application domain is associated with the company"
                )

        elif claim_type == "recruiter_identity":

            recruiter_name = claim["text"].replace(
               " claims to represent " + company_name + ".", ""
            )

            add_query(
                claim_id,
                f'"{claim["text"]}"',
                "Search for the claimed recruiter identity"
            )

            add_query(
                claim_id,
                f"{company_name} recruiter {recruiter_name}",
                "Check whether the recruiter is associated with the company"
            )

        elif claim_type == "contact_information":

            # Extract email from the claim text
            text = claim["text"]

            email = None

            if "@" in text:
                email = text.split("email ", 1)[-1].rstrip(".")

            if email:
                add_query(
                    claim_id,
                    f'"{email}"',
                    "Search for the recruiter's contact information"
                )

        elif claim_type == "payment":

            add_query(
                claim_id,
                f"{company_name} recruitment fee",
                "Check whether the company requires recruitment payments"
            )

            add_query(
                claim_id,
                f"{company_name} job scam payment",
                "Search for independent scam reports involving recruitment payments"
            )

    return queries