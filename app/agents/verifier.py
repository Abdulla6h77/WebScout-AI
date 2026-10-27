import re
from datetime import datetime, timezone

from app.core.security import suspicious
from app.evaluation.schemas import Citation
from app.retrieval.ranking import tokens


def normalize(text):
    return " ".join(text.split()).casefold()


def verify(draft, evidence, question):
    indexed = {e.id: e for e in evidence}
    accepted, citations, warnings = [], [], []
    if draft.contradictions:
        return [], [], ["Conflicting evidence: " + "; ".join(draft.contradictions)]
    for claim in draft.claims:
        e = indexed.get(claim.evidence_id)
        if not e or claim.relation != "direct" or suspicious(claim.quote):
            continue
        if claim.quote not in e.passage or claim.text not in claim.quote:
            continue
        if re.search(r"\b(not|never|neither|no longer)\b", claim.quote, re.I) and not re.search(
                r"\b(not|never|neither|no longer)\b", claim.text, re.I):
            warnings.append("Rejected answer substring that discards source negation")
            continue
        if not set(tokens(question)).intersection(tokens(claim.quote)):
            continue
        if re.search(r"\b(current|latest|today|now)\b", question, re.I):
            if re.search(r"\b(archived|withdrawn|superseded|obsolete)\b", e.passage, re.I):
                warnings.append("Excluded superseded evidence")
                continue
            if e.published_at:
                try:
                    published = datetime.fromisoformat(e.published_at.replace("Z", "+00:00"))
                    published = published.replace(tzinfo=published.tzinfo or timezone.utc)
                    if (datetime.now(timezone.utc) - published).days > 365:
                        warnings.append("Evidence is over one year old; current applicability is unverified")
                        continue
                except ValueError:
                    warnings.append("Publication date is unparseable")
                    continue
            else:
                warnings.append("Publication date unavailable; retrieval time does not prove freshness")
        if claim.text not in accepted:
            accepted.append(claim.text)
            citations.append(Citation(url=e.url, title=e.title, supporting_text=claim.quote,
                claim=claim.text, evidence_id=e.id, retrieved_at=e.retrieved_at, published_at=e.published_at))
    # Conservative deterministic conflict guard for directly comparable numeric facts.
    # Different products/tier/currencies must not be merged into one slot.
    question_tokens = set(tokens(question))
    if question_tokens & {"refund", "price", "deadline", "hours"}:
        values = {}
        for e in evidence:
            for sentence in re.split(r"[\n.!?]", e.passage):
                if not (question_tokens & set(tokens(sentence))):
                    continue
                for match in re.finditer(r"(?:\$|USD\s*)\d+(?:\.\d+)?|\b\d+\s+days\b", sentence, re.I):
                    slot = normalize(re.sub(r"(?:\$|USD\s*)\d+(?:\.\d+)?|\b\d+\s+days\b", "<value>", sentence, flags=re.I))
                    values.setdefault(slot, set()).add(normalize(match.group()))
        if any(len(v) > 1 for v in values.values()):
            return [], [], warnings + ["Contradictory numeric facts in comparable passages"]
    return accepted, citations, warnings
