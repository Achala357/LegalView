import sqlite3
from pathlib import Path


#  Change this to your actual SQLite DB file
DB_PATH = Path("backend/audit.db")  # <-- update if your db file name/path differs


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cur.fetchone() is not None


def get_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}  # row[1] = column name


def add_column_if_missing(conn: sqlite3.Connection, table: str, col: str, ddl: str) -> None:
    cols = get_columns(conn, table)
    if col not in cols:
        print(f"➕ Adding column {table}.{col}")
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
    else:
        print(f" Column exists {table}.{col}")


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB file not found: {DB_PATH.resolve()}")

    print(f" Migrating DB: {DB_PATH.resolve()}")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys=ON")

        # ---------------------------------------------------------------------
        # 1) Create anchors table
        # ---------------------------------------------------------------------
        if not table_exists(conn, "anchors"):
            print(" Creating table: anchors")
            conn.execute(
                """
                CREATE TABLE anchors (
                    anchor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    merkle_root TEXT NOT NULL,
                    tx_hash TEXT,
                    network TEXT NOT NULL,
                    contract_address TEXT,
                    created_at TEXT NOT NULL,
                    block_start INTEGER NOT NULL,
                    block_end INTEGER NOT NULL
                );
                """
            )
        else:
            print(" Table exists: anchors")

        # ---------------------------------------------------------------------
        # 2) Add columns to audit_chain (existing table)
        # ---------------------------------------------------------------------
        if not table_exists(conn, "audit_chain"):
            raise RuntimeError(
                "Expected table 'audit_chain' not found. "
                "If your audit table has a different name, update this script."
            )

        add_column_if_missing(conn, "audit_chain", "anchor_id", "anchor_id INTEGER")
        add_column_if_missing(conn, "audit_chain", "leaf_index", "leaf_index INTEGER")
        add_column_if_missing(conn, "audit_chain", "merkle_proof", "merkle_proof TEXT")
        add_column_if_missing(conn, "audit_chain", "anchored_at", "anchored_at TEXT")

        conn.commit()
        print(" Migration complete.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
