from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import model_registry
from sqlalchemy.orm import Session
from fastapi import Depends
from audit.db import get_db, SessionLocal
from audit.logger import log_event, sha256_json, sha256_hex
import hashlib


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/qa", tags=["QA"])


class QAAskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question about the contract")

    #  identify which uploaded contract to scope retrieval to
    filename: Optional[str] = Field(
        default=None,
        description="Uploaded filename (e.g., 20260207_185546_000000037.txt) to scope evidence retrieval.",
    )

    structured_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional structured context from /api/contracts/analyze "
            "(extracted spans, risk findings, contract type, filename, etc.)."
        ),
    )

    top_k_contract: int = Field(default=5, ge=1, le=20)
    top_k_case: int = Field(default=3, ge=0, le=20)


@router.get("/health")
def qa_health() -> Dict[str, Any]:
    return {"dual_rag_ready": bool(getattr(model_registry, "DUAL_RAG", None))}


@router.post("/ask")
def ask_question(payload: QAAskRequest) -> Dict[str, Any]:
    dual_rag = getattr(model_registry, "DUAL_RAG", None)
    if dual_rag is None:
        raise HTTPException(
            status_code=500,
            detail="DUAL_RAG is not initialised. Check startup() in main.py.",
        )

    try:

        upload_store = None
        stores = getattr(model_registry, "UPLOAD_CONTRACT_STORES", None)
        if payload.filename and isinstance(stores, dict):
            upload_store = stores.get(payload.filename)

        # --- existing QA logic ---
        result = dual_rag.answer(
            question=payload.question,
            top_k_contract=payload.top_k_contract,
            top_k_case=payload.top_k_case,
            structured_context=payload.structured_context,
            filename=payload.filename,
            contract_store_override=upload_store,
        )


        question_text = (payload.question or "").strip()
        question_hash = sha256_hex(question_text.encode("utf-8"))

        answer_text = (result.get("answer") or "")
        answer_hash = sha256_hex(answer_text.encode("utf-8"))

        qa_summary = {
            "question_hash": question_hash,
            "answer_hash": answer_hash,
            "used_upload_index": bool(upload_store),
            "used_case_law": result.get("used_case_law"),
            "contract_evidence_count": len(result.get("contract_evidence", []) or []),
            "case_evidence_count": len(result.get("case_evidence", []) or []),
        }


        qa_summary["output_hash"] = sha256_json(qa_summary)


        db = SessionLocal()
        try:
            log_event(
                db,
                action_type="QA_ASKED",
                actor_id="system",
                contract_id=payload.filename,
                payload=qa_summary,
            )
        finally:
            db.close()


        return {"question": payload.question, **result}

    except AssertionError as e:
        logger.exception("FAISS assertion error in /qa/ask")
        raise HTTPException(
            status_code=500,
            detail=(
                "FAISS search failed (likely embedding dim mismatch with index). "
                f"Details: {str(e)}"
            ),
        )
    except Exception as e:
        logger.exception("POST /qa/ask failed")
        raise HTTPException(status_code=500, detail=str(e))
