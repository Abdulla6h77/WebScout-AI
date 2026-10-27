import hashlib
import re

from app.core.security import suspicious
from app.evaluation.schemas import Evidence
from app.retrieval.ranking import rank


def collect_evidence(question, pages):
    chunks, owners, seen = [], [], set()
    for page in pages:
        if page.evidence_kind != "page_text" or page.status != "success":
            continue
        lines = [line.strip() for line in re.split(r"\n+|(?<=[.!?])\s+(?=[A-Z])", page.content) if line.strip()]
        # Keep adjacent context, but reject any passage containing an instruction injection signal.
        for i in range(len(lines)):
            passage = " ".join(lines[max(0, i - 1):i + 2])[:2000]
            digest = hashlib.sha256(passage.encode()).hexdigest()
            if len(passage) < 12 or suspicious(passage) or digest in seen:
                continue
            seen.add(digest)
            chunks.append(passage)
            owners.append(page)
    evidence = []
    for i, score in rank(question, chunks):
        if score <= 0:
            continue
        page = owners[i]
        evidence.append(Evidence(id="e" + hashlib.sha256((page.url + chunks[i]).encode()).hexdigest()[:14],
            url=page.url, title=page.title, passage=chunks[i], provider=page.provider, score=score,
            retrieved_at=page.retrieved_at, published_at=page.published_at))
    return evidence[:12]
