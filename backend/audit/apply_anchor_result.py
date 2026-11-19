import argparse
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to audit.db (e.g., backend/audit.db)")
    ap.add_argument("--infile", required=True, help="Path to anchor_result.json")
    args = ap.parse_args()

    db_path = Path(args.db).resolve()
    in_path = Path(args.infile).resolve()

    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")
    if not in_path.exists():
        raise FileNotFoundError(f"Result JSON not found: {in_path}")

    data = json.loads(in_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()

    merkle_root = data["merkle_root"]
    tx_hash = data.get("tx_hash")
    network = data.get("network", "localhost-hardhat")
    contract_address = data.get("contract_address")
    block_start = data.get("block_start")
    block_end = data.get("block_end")
    blocks = data.get("blocks", [])

    if not blocks:
        print("No blocks in anchor_result.json; nothing to apply.")
        return

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Insert anchor row
    cur.execute(
        """
        INSERT INTO anchors (merkle_root, tx_hash, network, contract_address, created_at, block_start, block_end)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (merkle_root, tx_hash, network, contract_address, now, block_start, block_end),
    )
    anchor_id = cur.lastrowid

    # Update each audit block with anchor metadata
    for b in blocks:
        proof_json = json.dumps(b["merkle_proof"])
        cur.execute(
            """
            UPDATE audit_chain
            SET anchor_id = ?, leaf_index = ?, merkle_proof = ?, anchored_at = ?
            WHERE id = ?
            """,
            (anchor_id, b["leaf_index"], proof_json, now, b["id"]),
        )

    conn.commit()
    conn.close()

    print(f"Applied anchor_id={anchor_id} to {len(blocks)} audit blocks.")
    print(f"Anchored root: {merkle_root}")
    print(f"Block range: {block_start} .. {block_end}")


if __name__ == "__main__":
    main()
