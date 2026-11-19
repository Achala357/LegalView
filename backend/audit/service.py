import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import AuditBlock
from .schemas import AuditLogRequest

GENESIS_PREV_HASH = "0" * 64

def _canonical_dumps(obj) -> str:
    """
    Deterministic JSON serialization: stable ordering + stable formatting.
    This is essential so the same block data always produces the same hash.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def compute_block_hash(
    block_index: int,
    timestamp: datetime,
    action_type: str,
    actor_id: str,
    contract_id: str | None,
    payload: dict,
    previous_hash: str,
) -> str:
    block_data = {
        "block_index": block_index,
        "timestamp": timestamp.replace(microsecond=0).isoformat() + "Z",  # stable-ish
        "action_type": action_type,
        "actor_id": actor_id,
        "contract_id": contract_id,
        "payload": payload,
        "previous_hash": previous_hash,
    }
    s = _canonical_dumps(block_data).encode("utf-8")
    return hashlib.sha256(s).hexdigest()

def get_last_block(db: Session) -> AuditBlock | None:
    return db.query(AuditBlock).order_by(AuditBlock.block_index.desc()).first()

def ensure_genesis_block(db: Session) -> AuditBlock:
    """
    Ensures chain exists. Creates index=0 block if empty.
    """
    last = get_last_block(db)
    if last:
        return last

    ts = datetime.utcnow()
    genesis_payload = {"note": "genesis"}
    genesis_hash = compute_block_hash(
        block_index=0,
        timestamp=ts,
        action_type="GENESIS",
        actor_id="system",
        contract_id=None,
        payload=genesis_payload,
        previous_hash=GENESIS_PREV_HASH,
    )

    genesis = AuditBlock(
        block_index=0,
        timestamp=ts,
        action_type="GENESIS",
        actor_id="system",
        contract_id=None,
        payload=genesis_payload,
        previous_hash=GENESIS_PREV_HASH,
        current_hash=genesis_hash,
    )
    db.add(genesis)
    db.commit()
    db.refresh(genesis)
    return genesis

def append_audit_block(db: Session, req: AuditLogRequest) -> AuditBlock:
    """
    Appends a new block, chained to the previous one.
    """
    last = ensure_genesis_block(db)

    new_index = last.block_index + 1
    ts = datetime.utcnow()

    new_hash = compute_block_hash(
        block_index=new_index,
        timestamp=ts,
        action_type=req.action_type,
        actor_id=req.actor_id,
        contract_id=req.contract_id,
        payload=req.payload,
        previous_hash=last.current_hash,
    )

    block = AuditBlock(
        block_index=new_index,
        timestamp=ts,
        action_type=req.action_type,
        actor_id=req.actor_id,
        contract_id=req.contract_id,
        payload=req.payload,
        previous_hash=last.current_hash,
        current_hash=new_hash,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block

def verify_chain(db: Session) -> tuple[bool, str, int | None]:
    """
    Verifies:
    - previous_hash links match
    - current_hash recomputes correctly
    Returns: (ok, message, broken_at_index)
    """
    blocks = db.query(AuditBlock).order_by(AuditBlock.block_index.asc()).all()
    if not blocks:
        return True, "Chain empty (no blocks).", None

    # Genesis rules
    if blocks[0].block_index != 0:
        return False, "First block is not index 0 (missing genesis).", blocks[0].block_index
    if blocks[0].previous_hash != GENESIS_PREV_HASH:
        return False, "Genesis previous_hash is invalid.", 0

    for i, b in enumerate(blocks):
        # Check index continuity (0..N)
        if b.block_index != i:
            return False, f"Index discontinuity: expected {i}, found {b.block_index}.", b.block_index

        # Check link
        if i > 0:
            prev = blocks[i - 1]
            if b.previous_hash != prev.current_hash:
                return False, "Broken previous_hash link.", b.block_index

        # Recompute current hash
        expected = compute_block_hash(
            block_index=b.block_index,
            timestamp=b.timestamp,
            action_type=b.action_type,
            actor_id=b.actor_id,
            contract_id=b.contract_id,
            payload=b.payload,
            previous_hash=b.previous_hash,
        )
        if expected != b.current_hash:
            return False, "Hash mismatch (tampering detected).", b.block_index

    return True, "Chain OK.", None
