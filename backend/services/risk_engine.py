# risk_engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict, Counter
import math

from services.xai_explainer import clip01, build_clause_xai, ClauseXAI
from services.risk_classifier import RiskClassifier, ClauseInput
from services.clause_type_mapper import normalize_clause_type



# -----------------------------
# 1) Clause type extraction (Option A: keyword rules from question)
# -----------------------------
def extract_clause_type(question: str) -> str:
    return normalize_clause_type(question)



# -----------------------------
# 2) Expected clause sets (V1 baseline, can refine later)
# -----------------------------
EXPECTED = {
    "m_and_a": {
        "purchase_price",
        "closing_conditions",
        "representations_and_warranties",
        "indemnification",
        "indemnification_basket_cap",
        "escrow_or_holdback",
        "working_capital_adjustment",
        "material_adverse_effect",
        "limitation_of_liability",
        "dispute_resolution",
        "post_closing_obligations",
        "notices",
    },
    "employment": {
        "employment_term",
        "termination",
        "termination_for_cause",
        "termination_without_cause",
        "notice_period",
        "compensation",
        "bonus_or_commission",
        "benefits",
        "severance",
        "non_compete",
        "non_solicitation",
        "duties_and_responsibilities",
        "working_hours",
        "overtime",
        "probation_period",
        "notices",
    },
    "nda": {
        "confidentiality_definition",
        "confidentiality_obligations",
        "confidentiality_permitted_disclosure",
        "confidentiality_exclusion",
        "confidentiality_non_use",
        "return_or_destruction",
        "residual_knowledge",
        "no_license_granted",
        "dispute_resolution",
        "governing_law",
        "notices",
    },
}

HIGH_IMPACT = {
    "m_and_a": {"indemnification", "purchase_price", "representations_and_warranties", "material_adverse_effect"},
    "employment": {"termination", "compensation", "non_compete", "severance"},
    "nda": {"confidentiality_obligations", "confidentiality_exclusion", "return_or_destruction"},
}


# -----------------------------
# 3) V1 contract score (missing clauses + risky clauses)
# -----------------------------
def compute_contract_missing_context(clauses: List[Dict[str, Any]], contract_type: str):
    expected = EXPECTED.get(contract_type, set())
    present = {c["clause_type"] for c in clauses}
    missing = expected - present
    missing_high = missing & HIGH_IMPACT.get(contract_type, set())
    return missing, missing_high, len(expected), len(present)


def v1_contract_score(clauses: List[Dict[str, Any]], contract_type: str) -> Tuple[float, Dict[str, Any]]:
    missing, missing_high, expected_n, _ = compute_contract_missing_context(clauses, contract_type)
    missing_ratio = (len(missing) / expected_n) if expected_n > 0 else 0.0
    high_missing_ratio = (len(missing_high) / max(1, len(HIGH_IMPACT.get(contract_type, set()))))

    # risky clause fraction from clause-level predictions
    risky_flags = [1 for c in clauses if c["risk_label"] == "risky"]
    risky_frac = (sum(risky_flags) / max(1, len(clauses)))

    # Simple interpretable weighting (V1)
    # (You already used this style: not opaque, just explicit knobs)
    score = 0.55 * missing_ratio + 0.25 * high_missing_ratio + 0.20 * risky_frac
    score = clip01(score)

    breakdown = {
        "missing": sorted(list(missing)),
        "missing_high_impact": sorted(list(missing_high)),
        "missing_ratio": missing_ratio,
        "high_missing_ratio": high_missing_ratio,
        "risky_fraction": risky_frac,
    }
    return score, breakdown


# -----------------------------
# 4) Priors (learned from your dataset) – computed at runtime from historical labeled JSONL
# -----------------------------
def compute_clause_priors(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Returns: priors[clause_type][contract_type] = P(risky)
    """
    stats = defaultdict(lambda: defaultdict(lambda: {"risky": 0, "total": 0}))
    for r in records:
        ct = r["contract_type"]
        ctype = r["clause_type"]
        stats[ctype][ct]["total"] += 1
        if r["risk_label"] == "risky":
            stats[ctype][ct]["risky"] += 1

    priors = defaultdict(dict)
    for ctype, by_ct in stats.items():
        for ct, s in by_ct.items():
            priors[ctype][ct] = (s["risky"] / s["total"]) if s["total"] else 0.0
    return priors


# -----------------------------
# 5) V2-A: context-adjusted clause score
# -----------------------------
def v2_adjust_clause_risk(
    base_risk: float,
    prior: float,
    missing_ratio: float,
    high_missing_ratio: float,
    contract_baseline: float,
    same_type_count: int,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    # Default interpretable weights (tunable)
    w = {
        "prior": 0.35,
        "missing": 0.18,
        "highmiss": 0.12,
        "contract": 0.15,
        "repeat": 0.03,
    }
    if weights:
        w.update(weights)

    adj = base_risk
    adj = (1 - w["prior"]) * adj + w["prior"] * prior
    adj += w["missing"] * missing_ratio
    adj += w["highmiss"] * high_missing_ratio
    adj += w["contract"] * (contract_baseline - 0.5)
    adj += w["repeat"] * math.log(1 + max(0, same_type_count - 1))

    return clip01(adj)


# -----------------------------
# 6) Main Engine: classifier → clause risk → aggregation → report
# -----------------------------
@dataclass
class ClauseResult:
    clause_id: str
    contract_id: str
    contract_type: str
    clause_type: str
    clause_text: str
    question: str
    risk_label: str
    risk_confidence: float
    p_risky: float
    v2_adjusted_risk: float
    xai: ClauseXAI


@dataclass
class ContractResult:
    contract_id: str
    contract_type: str
    v1_score: float
    v2_score: float
    overall_risk: str
    num_clauses: int
    num_missing_clauses: int
    missing_clauses: List[str]
    missing_high_impact: List[str]


class RiskEngine:
    def __init__(
        self,
        classifier: RiskClassifier,
        priors: Optional[Dict[str, Dict[str, float]]] = None,
        v2_weights: Optional[Dict[str, float]] = None,
    ):
        self.classifier = classifier
        self.priors = priors or defaultdict(dict)
        self.v2_weights = v2_weights

    def _prior(self, contract_type: str, clause_type: str) -> float:
        # fallback: if unknown prior, be mildly conservative but not extreme
        return float(self.priors.get(clause_type, {}).get(contract_type, 0.35))

    def score_contract(self, clauses: List[Dict[str, Any]]) -> Tuple[ContractResult, List[ClauseResult]]:
        """
        clauses: list of dicts from span extractor (must have at least: clause_id, contract_id, clause_text, question, contract_type)
        """
        if not clauses:
            raise ValueError("No clauses provided for scoring")

        contract_id = clauses[0]["contract_id"]
        contract_type = clauses[0]["contract_type"]

        # 1) Attach clause_type
        for c in clauses:
            c["clause_type"] = extract_clause_type(c.get("question", ""))

        # 2) Run classifier inference
        inputs = [
            ClauseInput(
                clause_text=c["clause_text"],
                question=c["question"],
                contract_type=c["contract_type"],
            )
            for c in clauses
        ]
        preds = self.classifier.predict(inputs)

        # 3) Attach clause-level label/confidence from classifier
        for c, p in zip(clauses, preds):
            c["risk_label"] = p.predicted_label
            c["risk_confidence"] = p.confidence
            c["p_risky"] = p.p_risky

        # 4) V1 baseline contract context
        v1_score, v1_breakdown = v1_contract_score(clauses, contract_type)
        missing = set(v1_breakdown["missing"])
        missing_high = set(v1_breakdown["missing_high_impact"])

        missing_ratio = v1_breakdown["missing_ratio"]
        high_missing_ratio = v1_breakdown["high_missing_ratio"]

        # 5) Clause repetition counts
        counts = Counter([c["clause_type"] for c in clauses])

        # 6) V2 clause adjustments + XAI objects
        clause_results: List[ClauseResult] = []
        v2_scores: List[float] = []

        for c in clauses:
            # base risk = p(risky) is the cleanest base for inference-time
            base_risk = float(c["p_risky"])
            prior = self._prior(contract_type, c["clause_type"])
            same_type_count = counts[c["clause_type"]]

            v2 = v2_adjust_clause_risk(
                base_risk=base_risk,
                prior=prior,
                missing_ratio=missing_ratio,
                high_missing_ratio=high_missing_ratio,
                contract_baseline=v1_score,
                same_type_count=same_type_count,
                weights=self.v2_weights,
            )

            xai = build_clause_xai(
                clause_type=c["clause_type"],
                base_risk=base_risk,
                prior=prior,
                missing_ratio=missing_ratio,
                high_missing_ratio=high_missing_ratio,
                same_type_count=same_type_count,
                contract_baseline=v1_score,
                adjusted=v2,
            )

            v2_scores.append(v2)

            clause_results.append(
                ClauseResult(
                    clause_id=c["clause_id"],
                    contract_id=c["contract_id"],
                    contract_type=c["contract_type"],
                    clause_type=c["clause_type"],
                    clause_text=c["clause_text"],
                    question=c["question"],
                    risk_label=c["risk_label"],
                    risk_confidence=float(c["risk_confidence"]),
                    p_risky=float(c["p_risky"]),
                    v2_adjusted_risk=float(v2),
                    xai=xai,
                )
            )

        v2_contract = float(sum(v2_scores) / max(1, len(v2_scores)))

        # 7) Risk level thresholds (same style you used)
        if v2_contract < 0.4:
            level = "LOW"
        elif v2_contract < 0.7:
            level = "MEDIUM"
        else:
            level = "HIGH"

        contract_result = ContractResult(
            contract_id=contract_id,
            contract_type=contract_type,
            v1_score=float(round(v1_score, 3)),
            v2_score=float(round(v2_contract, 3)),
            overall_risk=level,
            num_clauses=len(clauses),
            num_missing_clauses=len(missing),
            missing_clauses=sorted(list(missing)),
            missing_high_impact=sorted(list(missing_high)),
        )

        return contract_result, clause_results
