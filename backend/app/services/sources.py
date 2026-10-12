"""Normalize and conservatively classify web search results."""
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import re

KNOWN_OFFICIAL_DOMAINS = {"microsoft.com", "careers.microsoft.com"}
PROFESSIONAL_NETWORK_DOMAINS = {"linkedin.com"}
JOB_BOARD_DOMAINS = {"indeed.com", "naukri.com", "glassdoor.com", "monster.com", "foundit.in", "wellfound.com", "lever.co", "greenhouse.io", "workday.com", "myworkdayjobs.com"}
NEWS_DOMAINS = {"reuters.com", "bbc.com", "bbc.co.uk", "ndtv.com", "thehindu.com", "timesofindia.indiatimes.com"}
TRACKING_PARAMS = {"gclid", "fbclid", "mc_cid", "mc_eid", "ref", "source"}


def normalize_domain(domain: str) -> str:
    domain = (domain or "").strip().lower().split(":", 1)[0].rstrip(".")
    return domain[4:] if domain.startswith("www.") else domain


def _is_domain_or_subdomain(domain: str, root: str) -> bool:
    domain, root = normalize_domain(domain), normalize_domain(root)
    return domain == root or domain.endswith("." + root)


def _company_domain_candidate(domain: str, company_name: str) -> bool:
    # Name resemblance is only a lead, never proof of domain ownership.
    domain = normalize_domain(domain)
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    ignored = {"inc", "llc", "ltd", "limited", "private", "pvt", "corporation", "corp", "company", "co"}
    tokens = [re.sub(r"[^a-z0-9]", "", t.lower()) for t in re.findall(r"[A-Za-z0-9]+", company_name or "")]
    tokens = [t for t in tokens if len(t) >= 3 and t not in ignored]
    host_labels = [p for label in labels[:-1] for p in label.split("-") if p not in {"www", "careers", "jobs", "apply", "recruitment", "mail", "docs"}]
    return bool(tokens and any(t == label for t in tokens for label in host_labels))


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


def _canonical_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    domain = normalize_domain(parsed.hostname or "")
    if not domain:
        return ""
    port = parsed.port
    netloc = domain if not port or (parsed.scheme.lower() == "https" and port == 443) or (parsed.scheme.lower() == "http" and port == 80) else f"{domain}:{port}"
    path = parsed.path.rstrip("/") or "/"
    params = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")]
    params.sort()
    return urlunparse((parsed.scheme.lower() or "https", netloc, path, "", urlencode(params, doseq=True), ""))


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
        sources.append({
            "id": f"{query_id}_source_{index + 1}", "query_id": query_id, "query_ids": [query_id],
            "claim_id": None, "claim_ids": [], "title": result.get("title") or "Untitled source",
            "url": url, "canonical_url": _canonical_url(url), "domain": domain,
            "source_type": classify_source(url, result.get("title") or "", company_name),
            "snippet": result.get("snippet") or "", "relevance": "medium",
        })
    return sources


def deduplicate_sources(sources: list[dict]) -> list[dict]:
    """Deduplicate URLs across the investigation while retaining claim/query associations."""
    unique, indexed = [], {}
    for source in sources:
        key = _canonical_url(source.get("canonical_url") or source.get("url") or "")
        if not key:
            continue
        claim_ids = set(source.get("claim_ids") or [])
        query_ids = set(source.get("query_ids") or [])
        if source.get("claim_id"):
            claim_ids.add(source["claim_id"])
        if source.get("query_id"):
            query_ids.add(source["query_id"])
        current = indexed.get(key)
        if current is None:
            current = dict(source)
            current["canonical_url"] = key
            current["claim_ids"] = sorted(claim_ids)
            current["query_ids"] = sorted(query_ids)
            current["claim_id"] = next(iter(current["claim_ids"]), None)
            current["query_id"] = next(iter(current["query_ids"]), None)
            indexed[key] = current
            unique.append(current)
        else:
            current["claim_ids"] = sorted(set(current.get("claim_ids", [])) | claim_ids)
            current["query_ids"] = sorted(set(current.get("query_ids", [])) | query_ids)
            current["claim_id"] = next(iter(current["claim_ids"]), None)
            current["query_id"] = next(iter(current["query_ids"]), None)
            if len(source.get("snippet") or "") > len(current.get("snippet") or ""):
                current["snippet"] = source["snippet"]
            if current.get("title") == "Untitled source" and source.get("title"):
                current["title"] = source["title"]
    return unique
