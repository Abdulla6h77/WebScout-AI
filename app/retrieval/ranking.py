import math
import re
from collections import Counter

STOP = set("a an the is are was were who what which when where how of for in on to and or me find tell does do it this at from please website page".split())
SYNONYMS = {"founded": "founder", "founders": "founder", "founding": "founder", "refunds": "refund",
            "cost": "price", "costs": "price", "pricing": "price", "prices": "price", "created": "founder"}


def tokens(text):
    return [SYNONYMS.get(t, t) for t in re.findall(r"[\w-]+", text.lower()) if t not in STOP]


def rank(question: str, passages: list[str]) -> list[tuple[int, float]]:
    q = set(tokens(question))
    docs = [Counter(tokens(p)) for p in passages]
    lengths = [sum(d.values()) for d in docs]
    avg = sum(lengths) / max(1, len(docs))
    df = Counter(term for doc in docs for term in doc)
    scored = []
    for i, doc in enumerate(docs):
        score = 0.0
        for term in q:
            tf = doc.get(term, 0)
            idf = math.log(1 + (len(docs) - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * lengths[i] / max(1, avg)))
            if tf and any(c.isdigit() for c in term):
                score += 2
        scored.append((i, score))
    return sorted(scored, key=lambda x: x[1], reverse=True)
