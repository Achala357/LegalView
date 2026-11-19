from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from .schemas import (
    AuditLogRequest,
    AuditBlockOut,
    AuditBlockUiOut,
    VerifyResult,
    AnchorOut,
    AuditProofOut,
    InclusionVerifyResult,
)
from .service import append_audit_block, verify_chain
from .db import get_db

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.post("/log", response_model=AuditBlockOut)
def log_action(req: AuditLogRequest, db: Session = Depends(get_db)):
    block = append_audit_block(db, req)
    return block


@router.get("/verify", response_model=VerifyResult)
def verify(db: Session = Depends(get_db)):
    ok, msg, broken_at = verify_chain(db)
    return VerifyResult(ok=ok, message=msg, broken_at_index=broken_at)


#  UI chain endpoint (includes anchoring metadata + proof length)
@router.get("/chain", response_model=list[AuditBlockUiOut])
def get_chain(db: Session = Depends(get_db), limit: int = 200):
    limit = max(1, min(limit, 5000))

    # We use SQL so we can safely return new anchoring columns
    rows = db.execute(
        text(
            """
            SELECT
                block_index,
                timestamp,
                action_type,
                actor_id,
                contract_id,
                payload,
                previous_hash,
                current_hash,
                anchor_id,
                leaf_index,
                merkle_proof,
                anchored_at
            FROM audit_chain
            ORDER BY block_index ASC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()

    out: list[AuditBlockUiOut] = []
    for r in rows:
        payload = r["payload"]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload) if payload else {}
            except json.JSONDecodeError:
                payload = {"_raw": payload}

        proof_len = None
        mp = r.get("merkle_proof")
        if mp:
            if isinstance(mp, str):
                # stored as JSON text
                try:
                    mp_list = json.loads(mp)
                    if isinstance(mp_list, list):
                        proof_len = len(mp_list)
                except Exception:
                    proof_len = None
            elif isinstance(mp, list):
                proof_len = len(mp)

        out.append(
            AuditBlockUiOut(
                block_index=r["block_index"],
                timestamp=r["timestamp"],
                action_type=r["action_type"],
                actor_id=r["actor_id"],
                contract_id=r["contract_id"],
                payload=payload,
                previous_hash=r["previous_hash"],
                current_hash=r["current_hash"],
                anchor_id=r.get("anchor_id"),
                leaf_index=r.get("leaf_index"),
                anchored_at=r.get("anchored_at"),
                proof_len=proof_len,
            )
        )
    return out


#  list anchors (for UI)
@router.get("/anchors", response_model=list[AnchorOut])
def list_anchors(db: Session = Depends(get_db), limit: int = 50):
    limit = max(1, min(limit, 500))

    rows = db.execute(
        text(
            """
            SELECT
                anchor_id,
                merkle_root,
                tx_hash,
                network,
                contract_address,
                created_at,
                block_start,
                block_end
            FROM anchors
            ORDER BY anchor_id DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()

    return [AnchorOut(**dict(r)) for r in rows]


#  proof bundle for one block (for UI “view proof”)
@router.get("/proof/{block_index}", response_model=AuditProofOut)
def get_proof(block_index: int, db: Session = Depends(get_db)):
    blk = db.execute(
        text(
            """
            SELECT
                block_index,
                current_hash,
                anchor_id,
                leaf_index,
                merkle_proof,
                anchored_at
            FROM audit_chain
            WHERE block_index = :idx
            """
        ),
        {"idx": block_index},
    ).mappings().first()

    if not blk:
        raise HTTPException(status_code=404, detail="Audit block not found.")

    if blk["anchor_id"] is None:
        raise HTTPException(status_code=400, detail="This audit block is not anchored yet.")

    anc = db.execute(
        text(
            """
            SELECT
                anchor_id,
                merkle_root,
                tx_hash,
                network,
                contract_address
            FROM anchors
            WHERE anchor_id = :aid
            """
        ),
        {"aid": blk["anchor_id"]},
    ).mappings().first()

    if not anc:
        raise HTTPException(status_code=500, detail="Anchor metadata missing for this block.")

    proof = blk["merkle_proof"]
    if isinstance(proof, str):
        proof = json.loads(proof) if proof else []
    if proof is None:
        proof = []

    return AuditProofOut(
        block_index=blk["block_index"],
        current_hash=blk["current_hash"],
        anchor_id=blk["anchor_id"],
        leaf_index=blk["leaf_index"],
        merkle_proof=proof,
        merkle_root=anc["merkle_root"],
        tx_hash=anc.get("tx_hash"),
        network=anc.get("network"),
        contract_address=anc.get("contract_address"),
        anchored_at=blk.get("anchored_at"),
    )

@router.get("/verify-inclusion/{block_index}", response_model=InclusionVerifyResult)
def verify_inclusion(block_index: int, db: Session = Depends(get_db)):
    """
    Recompute Merkle root from:
      leaf = keccak(current_hash_bytes)
      + stored merkle_proof (sortPairs=True)
    Then compare with anchors.merkle_root.
    """
    try:
        from eth_hash.auto import keccak  # uses eth-hash backend you installed
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Keccak backend missing. Install: python -m pip install \"eth-hash[pycryptodome]\". ({e})",
        )

    blk = db.execute(
        text(
            """
            SELECT block_index, current_hash, anchor_id, leaf_index, merkle_proof
            FROM audit_chain
            WHERE block_index = :idx
            """
        ),
        {"idx": block_index},
    ).mappings().first()

    if not blk:
        raise HTTPException(status_code=404, detail="Audit block not found.")

    if blk["anchor_id"] is None:
        return InclusionVerifyResult(
            ok=False,
            block_index=block_index,
            message="This audit block is not anchored yet.",
        )

    anc = db.execute(
        text(
            """
            SELECT merkle_root
            FROM anchors
            WHERE anchor_id = :aid
            """
        ),
        {"aid": blk["anchor_id"]},
    ).mappings().first()

    if not anc:
        return InclusionVerifyResult(
            ok=False,
            block_index=block_index,
            anchor_id=blk["anchor_id"],
            message="Anchor metadata missing.",
        )

    expected_root_hex = anc["merkle_root"]

    # ---- helpers ----
    def hx_to_bytes(h: str) -> bytes:
        h = h.strip()
        if h.startswith("0x"):
            h = h[2:]
        return bytes.fromhex(h)

    def bytes_to_hx(b: bytes) -> str:
        return "0x" + b.hex()

    def parent_hash(a: bytes, b: bytes) -> bytes:
        # merkletreejs sortPairs:true => lexicographically sort pair before hashing
        if a > b:
            a, b = b, a
        return keccak(a + b)

    # ---- parse proof ----
    proof = blk["merkle_proof"]
    if isinstance(proof, str):
        proof = json.loads(proof) if proof else []
    if proof is None:
        proof = []

    # ---- leaf definition (locked-in from your verified run) ----
    # leaf = keccak(current_hash_bytes)
    try:
        leaf = keccak(hx_to_bytes(blk["current_hash"]))
    except Exception as e:
        return InclusionVerifyResult(
            ok=False,
            block_index=block_index,
            anchor_id=blk["anchor_id"],
            message=f"Failed to compute leaf from current_hash: {e}",
        )

    # ---- recompute root ----
    h = leaf
    for sib_hex in proof:
        sib = hx_to_bytes(sib_hex)
        h = parent_hash(h, sib)

    computed_root_hex = bytes_to_hx(h)

    ok = computed_root_hex.lower() == expected_root_hex.lower()

    return InclusionVerifyResult(
        ok=ok,
        block_index=block_index,
        anchor_id=blk["anchor_id"],
        leaf_index=blk["leaf_index"],
        proof_len=len(proof),
        expected_root=expected_root_hex,
        computed_root=computed_root_hex,
        leaf_mode="leaf=keccak(current_hash_bytes)",
        message=("Inclusion verified." if ok else "Inclusion verification FAILED (roots differ)."),
    )
