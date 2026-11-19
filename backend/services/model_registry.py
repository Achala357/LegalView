# services/model_registry.py
from __future__ import annotations

from typing import Dict, Optional

from services.rag.faiss_store import FaissStore
from services.rag.dual_rag_service import DualRAGService

SPAN_EXTRACTOR = None
QUESTION_BANKS = None
RISK_CLASSIFIER = None
RISK_ENGINE = None
# RAG
CONTRACT_STORE = None
CASELAW_STORE = None
DUAL_RAG = None

DUAL_RAG: Optional[DualRAGService] = None

# 🔥 NEW: per-upload (per file) in-memory FAISS stores
UPLOAD_CONTRACT_STORES: Dict[str, FaissStore] = {}
