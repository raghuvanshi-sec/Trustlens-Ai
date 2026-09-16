from urllib.parse import urlparse


def classify_source(url: str, title: str = "") -> str:
    domain = urlparse(url).netloc.lower()

    official_domains = [
        "microsoft.com",
        "careers.microsoft.com",
    ]

    if any(
        domain == d or domain.endswith("." + d)
        for d in official_domains
    ):
        return "official"

    if ".gov" in domain or ".gov.in" in domain:
        return "official"

    professional_network_domains = [
       "linkedin.com",
    ]
    job_domains = [
       "indeed.com",
        "naukri.com",
        "glassdoor.com",
        "monster.com",
    ]

    if any(d in domain 
        for d in professional_network_domains
    ):
        return "professional_network"

    news_domains = [
        "reuters.com",
        "bbc.com",
        "bbc.co.uk",
        "ndtv.com",
        "thehindu.com",
        "timesofindia.indiatimes.com",
    ]

    if any(d in domain for d in news_domains):
        return "news"

    return "other"


def normalize_results(
    search_results: dict,
    query_id: str,
) -> list[dict]:

    sources = []

    organic_results = search_results.get(
        "organic_results",
        []
    )

    for index, result in enumerate(organic_results):

        url = result.get("link")

        if not url:
            continue

        title = result.get(
            "title",
            "Untitled source"
        )

        snippet = result.get(
            "snippet",
            ""
        )

        domain = urlparse(url).netloc.lower()

        source = {
            "id": f"{query_id}_source_{index + 1}",
            "query_id": query_id,
            "title": title,
            "url": url,
            "domain": domain,
            "source_type": classify_source(
                url,
                title
            ),
            "snippet": snippet,
            "relevance": "medium",
        }

        sources.append(source)

    return sources