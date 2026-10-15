"""Intent definitions for the case-deflection assistant.

Kept in Python rather than YAML so the harness stays on the declared dependency set (pytest +
pandas). Each of the six recurring P3 topics has:

* ``phrases``  - multi-word regex/keyword signals matched on the normalized text.
* ``keywords`` - single-token signals matched against the token set (with a prefix match for
  tokens of length >= 5, so ``return`` also catches ``returning``).
* ``exemplars`` - canonical utterances used for token-overlap scoring, and for documentation.

The seven-way label space is the six topics plus an implicit ``escalate`` fallback for anything the
router cannot confidently place (which is exactly what a human would expect from an agent that must
not guess).
"""

from __future__ import annotations

import re

STOPWORDS = {
    "i", "my", "the", "a", "an", "is", "are", "do", "does", "did", "you", "your", "we", "can",
    "could", "would", "to", "for", "of", "on", "in", "it", "this", "that", "have", "has", "had",
    "am", "was", "were", "be", "been", "and", "or", "if", "me", "please", "hi", "hello", "hey",
    "just", "about", "with", "at", "from", "when", "what", "how", "there", "here", "still", "not",
    "no", "yes", "thanks", "thank", "up", "so", "get", "got", "but", "as", "out",
}

INTENTS: dict[str, dict] = {
    "Order Status": {
        "phrases": {
            "where is my order": 3.0,
            "where's my order": 3.0,
            "where is my package": 3.0,
            "order status": 3.0,
            "track my order": 3.0,
            "status of my order": 3.0,
            "when will my order": 2.5,
            "hasn't arrived": 2.5,
            "has not arrived": 2.5,
            "did not arrive": 2.5,
            "not received": 1.5,
            "any update": 1.5,
            "been shipped": 2.0,
            "order number": 1.5,
            "still waiting": 1.5,
            "the status of my": 2.5,
            "not heard anything": 2.0,
            "supposed to be here": 2.5,
            "out for delivery": 2.0,
        },
        "keywords": {
            "order": 0.6,
            "package": 1.5,
            "parcel": 1.5,
            "tracking": 2.5,
            "tracked": 2.0,
            "track": 1.5,
            "shipped": 1.5,
            "shipment": 1.5,
            "dispatched": 1.5,
            "status": 1.2,
            "eta": 1.5,
            "arrived": 1.0,
            "delayed": 0.8,
            "deliver": 1.5,
            "carrier": 1.5,
            "stuck": 2.0,
            "received": 1.2,
            "late": 1.5,
        },
        "exemplars": [
            "where is my order",
            "can you tell me the status of my order",
            "my package has not arrived",
            "has my order shipped yet",
            "any update on my tracking",
        ],
    },
    "Return": {
        "phrases": {
            "send back": 2.5,
            "send it back": 2.5,
            "money back": 2.5,
            "return label": 3.0,
            "start a return": 3.0,
            "return an item": 3.0,
            "want to return": 3.0,
            "like to return": 3.0,
            "how do i return": 3.0,
            "return policy": 3.0,
            "get a refund": 3.0,
            "exchange this": 2.5,
            "return my": 2.5,
        },
        "keywords": {
            "return": 2.5,
            "refund": 3.0,
            "refunded": 2.5,
            "exchange": 2.5,
            "rma": 3.0,
            "credit": 1.0,
        },
        "exemplars": [
            "i want to return the boots i bought",
            "how do i send back an item for a refund",
            "i need to start a return",
            "can i exchange this for a different color",
            "i would like my money back",
        ],
    },
    "Warranty": {
        "phrases": {
            "under warranty": 3.0,
            "still under warranty": 3.0,
            "covered by warranty": 3.0,
            "warranty claim": 3.0,
            "warranty cover": 3.0,
            "does the warranty": 3.0,
            "stopped working": 2.5,
            "fell apart": 2.5,
        },
        "keywords": {
            "warranty": 3.0,
            "warranties": 3.0,
            "defect": 2.5,
            "defective": 2.5,
            "broken": 2.5,
            "broke": 2.5,
            "repair": 2.5,
            "repairing": 2.0,
            "faulty": 2.5,
            "damaged": 2.0,
            "torn": 2.0,
            "tore": 2.0,
            "snapped": 2.0,
            "cracked": 2.0,
            "malfunction": 2.5,
            "coverage": 1.5,
            "covered": 1.5,
            "guarantee": 1.5,
        },
        "exemplars": [
            "is my order still under warranty",
            "the zipper broke can i get it repaired under warranty",
            "does the warranty cover a cracked stove",
            "my boots split after three months is that covered",
            "is this a warranty claim",
        ],
    },
    "Shipping": {
        "phrases": {
            "how long does shipping": 3.0,
            "shipping options": 3.0,
            "shipping cost": 2.5,
            "shipping policy": 3.0,
            "do you ship to": 3.0,
            "free shipping": 2.5,
            "express shipping": 2.5,
            "standard shipping": 2.5,
            "cost to ship": 2.5,
            "how much is postage": 3.0,
            "delivery time": 2.0,
            "how long does it take": 2.0,
            "how long does delivery take": 3.0,
            "same day delivery": 3.0,
            "available at checkout": 1.5,
        },
        "keywords": {
            "shipping": 2.0,
            "ship": 1.2,
            "postage": 2.5,
            "freight": 2.5,
            "courier": 1.5,
            "express": 1.5,
            "expedited": 2.0,
            "international": 2.0,
            "overseas": 2.0,
            "postal": 2.0,
            "deliver": 2.0,
            "cost": 1.5,
            "method": 1.5,
        },
        "exemplars": [
            "how long does standard shipping take",
            "what shipping options do you offer",
            "do you ship to canada",
            "how much is postage to canada",
            "is free shipping available on large orders",
        ],
    },
    "Sizing": {
        "phrases": {
            "true to size": 3.0,
            "what size": 3.0,
            "which size": 3.0,
            "size up": 2.5,
            "size chart": 3.0,
            "sizing chart": 3.0,
            "between sizes": 3.0,
            "run small": 2.5,
            "run large": 2.5,
            "run narrow": 2.5,
            "how do they fit": 2.5,
            "will it fit": 2.0,
            "should i order": 1.5,
            "half sizes": 2.5,
        },
        "keywords": {
            "size": 2.0,
            "sizes": 2.0,
            "sizing": 2.5,
            "fit": 2.0,
            "fits": 1.5,
            "fitting": 1.5,
            "measurement": 2.5,
            "measurements": 2.5,
            "chart": 1.5,
            "waist": 1.5,
            "inseam": 2.0,
            "narrow": 1.2,
            "wide": 1.0,
            "measure": 2.5,
            "foot": 1.5,
            "medium": 1.0,
            "large": 1.0,
            "half": 1.0,
            "womens": 1.0,
            "mens": 1.0,
        },
        "exemplars": [
            "how do your boots run should i size up",
            "what size jacket should i order",
            "do you have a sizing chart",
            "are the pants true to size",
            "will the harness fit a tall person",
        ],
    },
    "Store Hours": {
        "phrases": {
            "store hours": 3.0,
            "what time do you open": 3.0,
            "are you open": 3.0,
            "when do you open": 3.0,
            "when do you close": 3.0,
            "when are you open": 3.0,
            "holiday hours": 3.0,
            "opening hours": 3.0,
            "business hours": 3.0,
            "closest store": 3.0,
            "near me": 2.0,
            "store location": 3.0,
            "store locator": 3.0,
        },
        "keywords": {
            "hours": 3.0,
            "open": 2.0,
            "opens": 2.0,
            "close": 2.0,
            "closes": 2.0,
            "closed": 1.5,
            "closing": 2.0,
            "location": 2.5,
            "locations": 2.5,
            "directions": 2.5,
            "address": 1.5,
            "store": 1.5,
            "stores": 1.5,
            "nearby": 2.0,
            "holiday": 2.0,
            "locator": 2.5,
        },
        "exemplars": [
            "what time do you open on saturday",
            "are you open on sundays",
            "what are the store hours for the bozeman location",
            "when does the downtown store close",
            "where is the closest store",
        ],
    },
}


def normalize(text: str) -> str:
    """Lowercase, strip apostrophes, and collapse punctuation to single spaces."""
    lowered = (text or "").lower().replace("'", "").replace("\u2019", "")
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


def tokenize(text: str) -> list[str]:
    """Normalized tokens."""
    return normalize(text).split()


def _content_tokens(text: str) -> set[str]:
    return {t for t in tokenize(text) if t not in STOPWORDS}


def _build_vocab() -> dict[str, set[str]]:
    vocab: dict[str, set[str]] = {}
    for intent, spec in INTENTS.items():
        words: set[str] = set()
        for exemplar in spec["exemplars"]:
            words.update(_content_tokens(exemplar))
        vocab[intent] = words
    return vocab


#: Content-word vocabulary per intent, derived from the exemplars (used for token-overlap scoring).
INTENT_VOCAB: dict[str, set[str]] = _build_vocab()


def score_intents(text: str) -> dict[str, float]:
    """Raw match score per intent: weighted phrase hits + keyword hits + exemplar token overlap."""
    norm = normalize(text)
    tokens = set(tokenize(text))
    content = _content_tokens(text)
    scores: dict[str, float] = {}

    for intent, spec in INTENTS.items():
        total = 0.0
        for phrase, weight in spec["phrases"].items():
            if re.search(r"\b" + re.escape(phrase) + r"\b", norm):
                total += weight
        for keyword, weight in spec["keywords"].items():
            if keyword in tokens or (len(keyword) >= 5 and any(t.startswith(keyword) for t in tokens)):
                total += weight
        overlap = len(content & INTENT_VOCAB[intent]) / max(1, len(content))
        total += 1.0 * overlap
        scores[intent] = round(total, 4)
    return scores
