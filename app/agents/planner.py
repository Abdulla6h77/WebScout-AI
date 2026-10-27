import re
from urllib.parse import urlsplit

from app.core.security import canonicalize


def analyze(query):
    url = query.starting_url
    if not url:
        found = re.search(r"https?://[^\s<>\"']+", query.question)
        if found:
            url = found.group().rstrip(".,);!?")
    url = canonicalize(url) if url else None
    domains = [urlsplit(canonicalize("https://" + d)).hostname for d in query.allowed_domains]
    if url and not domains:
        domains = [urlsplit(url).hostname]
    clean_question = re.sub(r"https?://\S+", "", query.question).strip()
    return {"domains": domains, "queue": [(url, 0)] if url else [],
            "search_queries": [clean_question, clean_question + " official source", clean_question + " documentation"]}
