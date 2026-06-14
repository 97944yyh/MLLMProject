from __future__ import annotations

import hashlib
import math
import re
from collections import Counter


TOKEN_RE = re.compile(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(text.lower()):
        if all("\u4e00" <= char <= "\u9fff" for char in raw):
            chars = list(raw)
            tokens.extend(chars)
            for ngram_size in (2, 3):
                tokens.extend(
                    "".join(chars[index : index + ngram_size])
                    for index in range(0, max(0, len(chars) - ngram_size + 1))
                )
        else:
            tokens.append(raw)
    return tokens


class HashEmbedding:
    """Deterministic local embedding used before real models are downloaded."""

    def __init__(self, dimensions: int = 512) -> None:
        self.dimensions = dimensions

    def embed_text(self, texts: list[str]) -> list[dict[int, float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> dict[int, float]:
        counts = Counter(tokenize(text))
        if not counts:
            return {}

        vector: dict[int, float] = {}
        for token, count in counts.items():
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest, "big") % self.dimensions
            vector[bucket] = vector.get(bucket, 0.0) + 1.0 + math.log(count)

        norm = math.sqrt(sum(value * value for value in vector.values()))
        if norm == 0:
            return vector
        return {key: value / norm for key, value in vector.items()}


def dot(left: dict[int, float], right: dict[int, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())
