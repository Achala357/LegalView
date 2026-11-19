from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
import hashlib
import json

from audit.schemas import AuditLogRequest
from audit.service import append_audit_block


def canonical_json(obj: Any) -> str:
    """
    Deterministic JSON serialization (stable order, no whitespace noise).
    This is important so hashes don't change between runs.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def log_event(
    db: Session,
    action_type: str,
    actor_id: str = "system",
    contract_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
):
    req = AuditLogRequest(
        action_type=action_type,
        actor_id=actor_id,
        contract_id=contract_id,
        payload=payload or {},
    )
    return append_audit_block(db, req)
