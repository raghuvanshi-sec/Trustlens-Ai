"""Normalize and conservatively classify web search results."""
from urllib.parse import urlparse
import re

KNOWN_OFFICIAL_DOMAINS = {"microsoft.com", "careers.microsoft.com"}
PROFESSIONAL_NETWORK_DOMAINS = {"linkedin.com"}
JOB_BOARD_DOMAINS = {"indeed.com", "naukri.com", "glassdoor.com", "monster.com", "foundit.in", "wellfound.com", "lever.co", "greenhouse.io"}
NEWS_DOMAINS = {"reuters.com", "bbc.com", "bbc.co.uk", "ndtv.com", "thehindu.com", "timesofindia.indiatimes.com"}


def normalize_domain(domain: str) -> str:
    domain = (domain or "").strip().lower().split(":", 1)[0]
    return domain[4:] if domain.startswith("www.") else domain


def _is_domain_or_subdomain(domain: str, root: str) -> bool:
    domain, root = normalize_domain(domain), normalize_domain(root)
    return domain == root or domain.endswith("." + root)


def _company_domain_candidate(domain: str, company_name: str) -> bool:
    domain = normalize_domain(domain)
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    ignored = {"inc", "llc", "ltd", "limited", "private", "pvt", "corporation", "corp", "company", "co"}
    tokens = [re.sub(r"[^a-z0-9]", "", token.lower()) for token in (company_name or "").split()]
    tokens = [token for token in tokens if len(token) >= 3 and token not in ignored]
    host_labels = [part for label in labels[:-1] for part in label.split("-") if part not in {"www", "careers", "jobs", "apply", "recruitment"}]
    return bool(tokens and any(token == label for token in tokens for label in host_labels))


def classify_source(url: str, title: str = "", company_name: str = "") -> str:
    parsed = urlparse(url if "://" in (url or "") else "https://" + (url or ""))
    domain = normalize_domain(parsed.hostname or "")
    if not domain:
        return "other"
    if any(_is_domain_or_subdomain(domain, d) for d in KNOWN_OFFICIAL_DOMAINS):
        return "official"
    if any(domain.endswith(suffix) for suffix in (".gov", ".gov.in", ".gov.uk", ".gov.au", ".gc.ca")):
        return "government"
    if any(_is_domain_or_subdomain(domain, d) for d in PROFESSIONAL_NETWORK_DOMAINS):
        return "professional_network"
    if any(_is_domain_or_subdomain(domain, d) for d in JOB_BOARD_DOMAINS):
        return "job_board"
    if any(_is_domain_or_subdomain(domain, d) for d in NEWS_DOMAINS):
        return "news"
    if company_name and _company_domain_candidate(domain, company_name):
        return "official_candidate"
    return "other"


def normalize_results(search_results: dict, query_id: str, company_name: str = "") -> list[dict]:
    sources = []
    for index, result in enumerate(search_results.get("organic_results", []) or []):
        url = result.get("link")
        if not isinstance(url, str) or not url:
            continue
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url) and not url.lower().startswith(("http://", "https://")):
            continue
        parsed = urlparse(url if url.lower().startswith(("http://", "https://")) else "https://" + url)
        domain = normalize_domain(parsed.hostname or "")
        if parsed.scheme not in {"http", "https"} or not domain:
            continue
        title, snippet = result.get("title") or "Untitled source", result.get("snippet") or ""
        sources.append({"id": f"{query_id}_source_{index + 1}", "query_id": query_id, "title": title, "url": url, "domain": domain, "source_type": classify_source(url, title, company_name), "snippet": snippet, "relevance": "medium"})
    return sources


def deduplicate_sources(sources: list[dict]) -> list[dict]:
    unique_sources, seen_keys = [], set()
    for source in sources:
        url = (source.get("url") or "").strip().lower().rstrip("/")
        if not url:
            continue
        key = (source.get("claim_id") or "", url)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_sources.append(source)
    return unique_sources
