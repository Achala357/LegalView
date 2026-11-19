# xai_explainer.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List
import math


def clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _pct(x: float) -> int:
    return int(round(clip01(x) * 100))


def _band(x: float) -> str:
    """
    Human-friendly risk bands for lawyers/non-technical users.
    """
    x = clip01(x)
    if x < 0.20:
        return "very low"
    if x < 0.40:
        return "low"
    if x < 0.60:
        return "moderate"
    if x < 0.80:
        return "high"
    return "very high"


def _delta_phrase(base: float, adjusted: float) -> str:
    d = adjusted - base
    if abs(d) < 0.05:
        return "stayed about the same"
    if d > 0:
        return "increased"
    return "decreased"


@dataclass
class ClauseXAI:
    clause_type: str
    base_risk: float
    prior_risky_rate: float
    missing_ratio: float
    high_missing_ratio: float
    same_type_count: int
    contract_baseline: float
    adjusted_risk: float
    narrative: str


def build_clause_xai(
    clause_type: str,
    base_risk: float,
    prior: float,
    missing_ratio: float,
    high_missing_ratio: float,
    same_type_count: int,
    contract_baseline: float,
    adjusted: float,
) -> ClauseXAI:
    """
    Produces a lawyer-readable explanation.

    IMPORTANT: We keep the semicolon rule used by your frontend:
      - BEFORE the first ';'  => clause-level explanation (shown per clause)
      - AFTER the first ';'   => contract-wide context (shown once in Risk Summary)
    """

    base_r = clip01(base_risk)
    adj_r = clip01(adjusted)
    prior_r = clip01(prior)

    # ---------------------------
    # Clause-level explanation (no semicolons here)
    # ---------------------------
    change = _delta_phrase(base_r, adj_r)

    clause_bits: List[str] = []
    # clause-specific drivers belong here (since they vary by clause type)
    if prior_r >= 0.60:
        clause_bits.append(f"this clause type is often risky in similar contracts (~{_pct(prior_r)}% historically)")
    elif prior_r <= 0.25:
        clause_bits.append(f"this clause type is usually safer in similar contracts (~{_pct(prior_r)}% historically)")

    if same_type_count >= 2:
        clause_bits.append(f"this clause type appears multiple times (count={same_type_count})")

    clause_driver_text = ""
    if clause_bits:
        clause_driver_text = " Key clause signals: " + ", ".join(clause_bits) + "."

    clause_part = (
        f"Model’s initial view: {_band(base_r)} concern (~{_pct(base_r)}% chance this clause is risky). "
        f"After considering contract context, the concern {change} to {_band(adj_r)} (~{_pct(adj_r)}%)."
        f"{clause_driver_text}"
    )

    # ---------------------------
    # Contract-wide context (semicolon-separated bullets, stable across clauses)
    # ---------------------------
    contract_drivers: List[str] = []

    if missing_ratio >= 0.60:
        contract_drivers.append(
            f"Contract completeness is low: many expected clauses are missing (~{_pct(missing_ratio)}%)"
        )
    elif missing_ratio >= 0.35:
        contract_drivers.append(
            f"Contract completeness is partial: some expected clauses are missing (~{_pct(missing_ratio)}%)"
        )

    if high_missing_ratio >= 0.50:
        contract_drivers.append(
            f"Several high-impact safeguards appear missing (~{_pct(high_missing_ratio)}%)"
        )
    elif high_missing_ratio >= 0.25:
        contract_drivers.append(
            f"Some high-impact safeguards appear missing (~{_pct(high_missing_ratio)}%)"
        )

    if contract_baseline >= 0.65:
        contract_drivers.append(f"Overall contract risk baseline looks elevated")
    elif contract_baseline <= 0.35:
        contract_drivers.append(f"Overall contract risk baseline looks low")

    if not contract_drivers:
        contract_drivers.append("No major contract-wide risk amplifiers were detected")

    # This becomes your contract-wide block in the UI
    contract_context = "; ".join([d + "." for d in contract_drivers])

    # ---------------------------
    # Final narrative (one semicolon boundary)
    # ---------------------------
    narrative = f"{clause_part}; {contract_context}"

    return ClauseXAI(
        clause_type=clause_type,
        base_risk=base_r,
        prior_risky_rate=prior_r,
        missing_ratio=clip01(missing_ratio),
        high_missing_ratio=clip01(high_missing_ratio),
        same_type_count=int(same_type_count),
        contract_baseline=clip01(contract_baseline),
        adjusted_risk=adj_r,
        narrative=narrative,
    )
