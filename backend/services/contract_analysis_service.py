# services/contract_analysis_service.py
from typing import Dict, Any, Optional

from services import model_registry
from services.contract_type_heuristic import detect_contract_type

# 🔹 NEW (RAG)
from services.rag_service import build_rag_context


def analyze_contract(
    contract_text: str,
    filename: str,
    include_rag_context: bool = False
) -> Dict[str, Any]:

    # -------------------------------
    # 1️⃣ Sanity checks
    # -------------------------------
    if getattr(model_registry, "SPAN_EXTRACTOR", None) is None:
        raise RuntimeError("Span extractor not initialized")

    if getattr(model_registry, "RISK_ENGINE", None) is None:
        raise RuntimeError("Risk engine not initialized")

    # -------------------------------
    # 2️⃣ Detect contract type
    # -------------------------------
    contract_type = detect_contract_type(contract_text)

    # -------------------------------
    # 2.1️⃣ Out-of-scope fallback (other / missing question bank)
    # -------------------------------
    question_banks = getattr(model_registry, "QUESTION_BANKS", {}) or {}
    question_bank = question_banks.get(contract_type)

    # If 'other' OR key missing OR empty list -> out of scope
    if not question_bank:
        msg = f"Contract type '{contract_type}' is out of scope to run analysis."

        payload: Dict[str, Any] = {
            "filename": filename,
            "contract_type": contract_type,
            "out_of_scope": True,
            "message": msg,
            # Keep stable response shape for UI
            "extracted_spans": [],
            "risk_clauses": [],
            "risk_assessment": {
                "contract_risk_score": None,
                "risk_level": "OUT_OF_SCOPE",
                "num_clauses": 0,
                "missing_clauses": [],
                "summary": msg,
            },
        }

        if include_rag_context:
            payload["rag_context"] = None

        return payload

    # -------------------------------
    # 3️⃣ Clause span extraction (✅ correct method name: extract)
    # -------------------------------
    spans = model_registry.SPAN_EXTRACTOR.extract(
        text=contract_text,
        contract_type=contract_type,
        question_bank=question_bank,
    )

    # If nothing extracted, avoid crashing risk engine
    if not spans:
        msg = "No clauses could be extracted for the detected contract type."
        payload: Dict[str, Any] = {
            "filename": filename,
            "contract_type": contract_type,
            "extracted_spans": [],
            "risk_clauses": [],
            "risk_assessment": {
                "contract_risk_score": None,
                "risk_level": "UNKNOWN",
                "num_clauses": 0,
                "missing_clauses": [],
                "summary": msg,
            },
        }
        if include_rag_context:
            payload["rag_context"] = None
        return payload

    # ===============================
    # 🔹 RISK PIPELINE (V2 Engine)
    # ===============================
    contract_id = filename  # stable identifier
    clauses_payload = []

    for idx, span in enumerate(spans):
        clause_text = span.get("clause_text", "")
        question = span.get("question", "")

        clauses_payload.append({
            "clause_id": f"{contract_id}:{idx}",
            "contract_id": contract_id,
            "contract_type": contract_type,
            "clause_text": clause_text,
            "question": question,
        })

    # Engine returns: (ContractResult, List[ClauseResult])
    contract_result, clause_results = model_registry.RISK_ENGINE.score_contract(clauses_payload)

    # -------------------------------
    # Map clause-level results to your existing frontend structure
    # -------------------------------
    clauses_for_risk = []
    for cr in clause_results:
        clauses_for_risk.append({
            "clause_text": cr.clause_text,
            "clause_type": cr.clause_type,
            "contract_type": cr.contract_type,
            "risk_label": cr.risk_label,
            "risk_confidence": cr.risk_confidence,
            # keep the same key your UI already uses
            "risk_reason": cr.xai.narrative,
        })

    # -------------------------------
    # Map contract-level results to your existing frontend structure
    # -------------------------------
    risk_report = {
        "contract_risk_score": contract_result.v2_score,   # use V2 as final score
        "risk_level": contract_result.overall_risk,
        "num_clauses": contract_result.num_clauses,
        "missing_clauses": contract_result.missing_clauses,
        "summary": (
            "Risk assessment reflects clause-level model signals combined with "
            "contract structural completeness and learned priors."
        ),
    }

    # ===============================
    # 🔹 OPTIONAL RAG CONTEXT
    # ===============================
    rag_context: Optional[str] = None

    if include_rag_context:
        rag_context = build_rag_context(
            extracted_spans=spans,
            risk_clauses=clauses_for_risk,
            risk_assessment=risk_report
        )

    # ===============================
    # 🔹 FINAL RESPONSE (UNCHANGED SHAPE)
    # ===============================
    response = {
        "filename": filename,
        "contract_type": contract_type,
        "extracted_spans": spans,
        "risk_clauses": clauses_for_risk,
        "risk_assessment": risk_report,
    }

    if include_rag_context:
        response["rag_context"] = rag_context

    return response
