# contract_type_heuristic.py
from __future__ import annotations

from typing import Dict, List, Tuple
import re

# Weighted phrase rules (simple, but less “employment-biased” than generic words)
RULES: Dict[str, List[Tuple[str, int]]] = {
    "nda": [
        (r"\bnon[-\s]?disclosure\b", 4),
        (r"\bconfidential information\b", 4),
        (r"\bdisclosing party\b", 3),
        (r"\brecipient\b", 2),
        (r"\bconfidentiality\b", 2),
        (r"\breturn (or )?destroy\b", 2),
        (r"\bproprietary\b", 1),
    ],
    "m_and_a": [
        (r"\bmerger\b", 4),
        (r"\bacquisition\b", 4),
        (r"\b(purchase|stock|asset)\s+purchase\s+agreement\b", 4),
        (r"\bpurchase price\b", 3),
        (r"\bclosing conditions\b", 3),
        (r"\bindemnification\b", 2),
        (r"\brepresentations and warranties\b", 2),
        (r"\bbuyer\b", 1),
        (r"\bseller\b", 1),
    ],
    "employment": [
        (r"\bat[-\s]?will\b", 4),
        (r"\bemployment agreement\b", 3),
        (r"\bemployee\b", 2),
        (r"\bsalary\b", 2),
        (r"\bcompensation\b", 2),
        (r"\btermination\b", 2),
        (r"\bseverance\b", 2),
        (r"\bnon[-\s]?compete\b", 2),
    ],
}

# If best score is below this, we treat it as not confidently any of the 3 types.
MIN_SCORE = 5


def _score(text_l: str) -> Dict[str, int]:
    scores: Dict[str, int] = {k: 0 for k in RULES.keys()}
    for ctype, patterns in RULES.items():
        for pat, w in patterns:
            if re.search(pat, text_l):
                scores[ctype] += w
    return scores


def detect_contract_type(contract_text: str) -> str:
    """
    Returns: 'employment' | 'nda' | 'm_and_a' | 'other'
    """
    if not contract_text:
        return "other"

    text_l = contract_text.lower()
    scores = _score(text_l)

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score < MIN_SCORE:
        return "other"

    return best_type
