from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from sqlalchemy.orm import Session
from fastapi import Depends
from audit.db import get_db, SessionLocal
from audit.logger import log_event, sha256_hex, sha256_json


from services.contract_analysis_service import analyze_contract
from services import model_registry

# Your in-memory upload index builder
from services.rag.upload_faiss_builder import build_upload_store_from_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/contracts", tags=["contracts"])

@router.post("/analyze")
async def analyze_contract_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    1) Run your normal analysis pipeline (classification, spans, risk).
    2) Build an in-memory FAISS index FOR THIS UPLOAD and cache it in model_registry,
       so /qa/ask can retrieve evidence only from this contract.
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")


        input_file_hash = sha256_hex(content)


        text = content.decode("utf-8", errors="ignore")
        analysis = analyze_contract(text, file.filename)

        if not isinstance(analysis, dict):
            raise HTTPException(status_code=500, detail="analyze_contract() did not return a dict.")


        analysis.setdefault("filename", file.filename)


        risk = analysis.get("risk_assessment", {}) or {}

        audit_summary = {
            "input_file_hash": input_file_hash,
            "original_filename": file.filename,
            "contract_type": analysis.get("contract_type"),
            "risk_level": risk.get("risk_level"),
            "risk_score": risk.get("contract_risk_score"),
            "num_spans": len(analysis.get("extracted_spans", []) or []),
            "num_risky_clauses": len(risk.get("risky_clauses", []) or []),
        }


        audit_summary["output_hash"] = sha256_json(audit_summary)


        db = SessionLocal()
        try:
            log_event(
                db,
                action_type="CONTRACT_ANALYZED",
                actor_id="system",
                contract_id=file.filename,
                payload=audit_summary,
            )
        finally:
            db.close()



        try:
            text = content.decode("utf-8", errors="ignore")

            # Use SAME embed model as the global contract store (avoid dim mismatch)
            embed_model_name = None
            if getattr(model_registry, "CONTRACT_STORE", None) is not None:
                embed_model_name = model_registry.CONTRACT_STORE.embed_model_name
            elif getattr(model_registry, "DUAL_RAG", None) is not None:
                embed_model_name = model_registry.DUAL_RAG.contract_store.embed_model_name

            if not embed_model_name:
                raise RuntimeError("Could not infer embed_model_name from model_registry.")

            upload_store = build_upload_store_from_text(
                contract_text=text,
                filename=file.filename,
                embed_model_name=embed_model_name,
                chunk_words=260,
                overlap_words=40,
            )

            # Cache by uploaded filename
            if not hasattr(model_registry, "UPLOAD_CONTRACT_STORES"):
                model_registry.UPLOAD_CONTRACT_STORES = {}

            model_registry.UPLOAD_CONTRACT_STORES[file.filename] = upload_store
            analysis["upload_index_ready"] = True

        except Exception as e:
            # Don’t fail analysis if indexing fails; just log it.
            logger.exception("Upload FAISS indexing failed for %s", file.filename)
            analysis["upload_index_ready"] = False
            analysis["upload_index_error"] = str(e)

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("POST /contracts/analyze failed")
        raise HTTPException(status_code=500, detail=str(e))
