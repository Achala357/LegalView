import argparse
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to audit.db (e.g., backend/audit.db)")
    ap.add_argument("--batch-size", type=int, default=50)
    ap.add_argument("--out", required=True, help="Output JSON path")
    args = ap.parse_args()

    db_path = Path(args.db).resolve()
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Pull earliest unanchored blocks (deterministic)
    cur.execute(
        """
        SELECT id, block_index, current_hash
        FROM audit_chain
        WHERE anchor_id IS NULL
        ORDER BY block_index ASC
        LIMIT ?
        """,
        (args.batch_size,),
    )
    rows = cur.fetchall()
    conn.close()

    blocks = [
        {"id": int(r["id"]), "block_index": int(r["block_index"]), "current_hash": str(r["current_hash"])}
        for r in rows
    ]

    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "batch_size": args.batch_size,
        "count": len(blocks),
        "blocks": blocks,
    }

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Exported {len(blocks)} unanchored blocks -> {out_path}")
    if blocks:
        print(f"Block range: {blocks[0]['block_index']} .. {blocks[-1]['block_index']}")
    else:
        print("No unanchored blocks found (anchor_id is already set for all rows).")


if __name__ == "__main__":
    main()
