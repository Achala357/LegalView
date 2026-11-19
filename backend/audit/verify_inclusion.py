import argparse
import json
import sqlite3

# keccak for Ethereum-style hashing (NOT hashlib.sha3_256)
from eth_hash.auto import keccak


def _hx_to_bytes(h: str) -> bytes:
    h = h.strip()
    if h.startswith("0x"):
        h = h[2:]
    return bytes.fromhex(h)


def _bytes_to_hx(b: bytes) -> str:
    return "0x" + b.hex()


def _parent_hash(a: bytes, b: bytes, sort_pairs: bool = True) -> bytes:
    # merkletreejs sortPairs:true means lexicographically sort the pair before hashing
    if sort_pairs and a > b:
        a, b = b, a
    return keccak(a + b)


def compute_root_from_proof(leaf: bytes, proof: list[str]) -> bytes:
    h = leaf
    for sib_hex in proof:
        sib = _hx_to_bytes(sib_hex)
        h = _parent_hash(h, sib, sort_pairs=True)
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to audit.db")
    ap.add_argument("--block-index", type=int, required=True, help="audit_chain.block_index to verify")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    row = cur.execute(
        """
        SELECT block_index, anchor_id, leaf_index, merkle_proof, current_hash
        FROM audit_chain
        WHERE block_index = ?
        """,
        (args.block_index,),
    ).fetchone()

    if not row:
        raise SystemExit(f"No audit block found for block_index={args.block_index}")

    block_index, anchor_id, leaf_index, merkle_proof_json, current_hash = row

    if anchor_id is None or not merkle_proof_json:
        raise SystemExit(
            f"Block {block_index} is not anchored yet (anchor_id/merkle_proof missing)."
        )

    anchor = cur.execute(
        """
        SELECT merkle_root, tx_hash, block_start, block_end, network
        FROM anchors
        WHERE anchor_id = ?
        """,
        (anchor_id,),
    ).fetchone()

    if not anchor:
        raise SystemExit(f"No anchor row found for anchor_id={anchor_id}")

    merkle_root_hex, tx_hash, block_start, block_end, network = anchor
    expected_root = _hx_to_bytes(merkle_root_hex)

    proof = json.loads(merkle_proof_json)
    if not isinstance(proof, list):
        raise SystemExit("merkle_proof is not a JSON list")

    # Try common leaf definitions (because different pipelines define leaves differently)
    candidates = []

    # A) leaf = raw sha256 current_hash bytes (very common: use chain hash as leaf)
    try:
        candidates.append(("leaf=current_hash_bytes", _hx_to_bytes(current_hash)))
    except Exception:
        pass

    # B) leaf = keccak(current_hash_bytes)
    try:
        candidates.append(("leaf=keccak(current_hash_bytes)", keccak(_hx_to_bytes(current_hash))))
    except Exception:
        pass

    # C) leaf = keccak(utf8(current_hash_hex_string))
    try:
        candidates.append(("leaf=keccak(current_hash_utf8)", keccak(current_hash.encode("utf-8"))))
    except Exception:
        pass

    ok = False
    for name, leaf in candidates:
        got_root = compute_root_from_proof(leaf, proof)
        if got_root == expected_root:
            ok = True
            print("INCLUSION OK ")
            print(f"block_index: {block_index}")
            print(f"anchor_id:   {anchor_id}  (range {block_start}..{block_end}, {network})")
            print(f"tx_hash:     {tx_hash}")
            print(f"leaf_index:  {leaf_index}")
            print(f"proof_len:   {len(proof)}")
            print(f"leaf_mode:   {name}")
            print(f"root:        {_bytes_to_hx(got_root)}")
            break

    if not ok:
        print("INCLUSION FAILED ")
        print(f"block_index: {block_index}")
        print(f"anchor_id:   {anchor_id}")
        print(f"expected:    {merkle_root_hex}")
        # show one computed root for debugging (first candidate)
        if candidates:
            demo_name, demo_leaf = candidates[0]
            demo_root = compute_root_from_proof(demo_leaf, proof)
            print(f"example({demo_name}): {_bytes_to_hx(demo_root)}")
        print("If this fails, it means the leaf definition in anchor_batch.ts differs from these candidates.")

    conn.close()


if __name__ == "__main__":
    main()
