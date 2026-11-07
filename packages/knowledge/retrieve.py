import math
import re
from collections import Counter

from packages.domain.models import KnowledgeEntry


def tokens(text: str) -> list[str]:
    text = re.sub(r"\s+", "", text.lower())
    return [text[i:i+2] for i in range(max(0, len(text)-1))] or [text]


class Retriever:
    """Small-corpus BM25 over character bigrams; only approved evidence is searchable."""
    def __init__(self, entries: list[KnowledgeEntry]):
        self.entries = [e for e in entries if e.review_status == "approved" and e.answer.strip()]
        self.docs = [Counter(tokens(e.question + " " + " ".join(e.category))) for e in self.entries]
        self.df = Counter(t for doc in self.docs for t in doc)
        self.avg = sum(sum(d.values()) for d in self.docs) / max(1, len(self.docs))

    def search(self, query: str, limit=3, allowed_ids: set[str] | None = None):
        scores = []
        for entry, doc in zip(self.entries, self.docs):
            if allowed_ids is not None and entry.entry_id not in allowed_ids:
                continue
            score = 0
            for word in set(tokens(query)):
                tf = doc.get(word, 0)
                idf = math.log(1 + (len(self.docs) - self.df[word] + .5) / (self.df[word] + .5))
                score += idf * tf * 2.5 / (tf + 1.5 * (.25 + .75 * sum(doc.values()) / max(self.avg, 1)))
            if score > 0:
                scores.append((entry, score))
        return sorted(scores, key=lambda x: (-x[1], x[0].entry_id))[:limit]
