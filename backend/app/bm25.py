"""BM25 Okapi in pure Python. Deterministic, offline, no model download."""
import math
import re

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text):
    return _TOKEN.findall(text.lower())


class BM25Index:
    def __init__(self, texts, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        docs = [tokenize(t) for t in texts]
        self.doc_len = [len(d) for d in docs]
        self.n = len(docs)
        self.avgdl = (sum(self.doc_len) / self.n) if self.n else 1.0
        if self.avgdl == 0:
            self.avgdl = 1.0

        self.tf = []
        df = {}
        for doc in docs:
            counts = {}
            for tok in doc:
                counts[tok] = counts.get(tok, 0) + 1
            self.tf.append(counts)
            for tok in counts:
                df[tok] = df.get(tok, 0) + 1
        self.idf = {
            tok: math.log(1 + (self.n - d + 0.5) / (d + 0.5)) for tok, d in df.items()
        }

    def search(self, query, top_k=5):
        """Returns [(chunk_index, score)] for the best matches with score > 0."""
        scores = [0.0] * self.n
        for tok in tokenize(query):
            idf = self.idf.get(tok)
            if idf is None:
                continue
            for i, counts in enumerate(self.tf):
                freq = counts.get(tok)
                if not freq:
                    continue
                denom = freq + self.k1 * (
                    1 - self.b + self.b * self.doc_len[i] / self.avgdl
                )
                scores[i] += idf * freq * (self.k1 + 1) / denom
        ranked = sorted(range(self.n), key=lambda i: scores[i], reverse=True)
        return [(i, scores[i]) for i in ranked[:top_k] if scores[i] > 0]
