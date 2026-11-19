from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    Index,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Anchor(Base):
    """
    Stores one on-chain anchor per batch of audit blocks.

    Each row corresponds to a single Merkle root that was anchored on-chain,
    along with metadata needed to later prove inclusion for any audit block.
    """
    __tablename__ = "anchors"

    anchor_id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    merkle_root = Column(String, nullable=False)          # "0x..." root
    tx_hash = Column(String, nullable=True)               # Hardhat/local optional
    network = Column(String, nullable=False)              # e.g., "localhost-hardhat"
    contract_address = Column(String, nullable=True)      # AuditAnchor deployed address

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Range of audit block_index values included in this Merkle root
    block_start = Column(Integer, nullable=False)
    block_end = Column(Integer, nullable=False)

    # Relationship back to audit blocks
    blocks = relationship("AuditBlock", back_populates="anchor")


class AuditBlock(Base):
    __tablename__ = "audit_chain"

    # Auto-increment DB PK
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Blockchain-like index (0..N)
    block_index = Column(Integer, nullable=False, unique=True, index=True)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # What happened
    action_type = Column(String, nullable=False)

    # Who did it (could be user_id, email, system, service name, etc.)
    actor_id = Column(String, nullable=False)

    # Which contract this relates to (if applicable)
    contract_id = Column(String, nullable=True, index=True)

    # Action payload (outputs, metadata, ids, scores, etc.)
    payload = Column(JSON, nullable=False)

    # Hash links
    previous_hash = Column(String, nullable=False)
    current_hash = Column(String, nullable=False, unique=True)

    # -------------------------------------------------------------------------
    # Phase 2 additions: bridge from off-chain hash-chain ledger -> on-chain root
    # These are nullable so existing logging logic doesn't break.
    # -------------------------------------------------------------------------
    anchor_id = Column(Integer, ForeignKey("anchors.anchor_id"), nullable=True)

    # Position of this audit block in the Merkle tree leaves for that anchor batch
    leaf_index = Column(Integer, nullable=True)

    # JSON string array of hex hashes (Merkle proof)
    # Stored as TEXT for SQLite portability
    merkle_proof = Column(Text, nullable=True)

    # Timestamp when this block became anchored (optional)
    anchored_at = Column(DateTime, nullable=True)

    # Relationship to Anchor
    anchor = relationship("Anchor", back_populates="blocks")

    __table_args__ = (
        Index("ix_audit_contract_time", "contract_id", "timestamp"),
    )
