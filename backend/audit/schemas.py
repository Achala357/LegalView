from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime



class AuditLogRequest(BaseModel):
    action_type: str = Field(..., min_length=2, max_length=128)
    actor_id: str = Field(..., min_length=1, max_length=128)
    contract_id: Optional[str] = Field(default=None, max_length=128)
    payload: Dict[str, Any] = Field(default_factory=dict)


class AuditBlockOut(BaseModel):
    block_index: int
    timestamp: datetime
    action_type: str
    actor_id: str
    contract_id: Optional[str]
    payload: Dict[str, Any]
    previous_hash: str
    current_hash: str

    class Config:
        from_attributes = True


#  UI-friendly block view (includes anchoring metadata if present)
class AuditBlockUiOut(BaseModel):
    block_index: int
    timestamp: datetime
    action_type: str
    actor_id: str
    contract_id: Optional[str]
    payload: Dict[str, Any]
    previous_hash: str
    current_hash: str

    # anchoring bridge fields (nullable)
    anchor_id: Optional[int] = None
    leaf_index: Optional[int] = None
    anchored_at: Optional[datetime] = None

    # optional convenience for UI
    proof_len: Optional[int] = None


class VerifyResult(BaseModel):
    ok: bool
    message: str
    broken_at_index: Optional[int] = None


class AnchorOut(BaseModel):
    anchor_id: int
    merkle_root: str
    tx_hash: Optional[str] = None
    network: Optional[str] = None
    contract_address: Optional[str] = None
    created_at: Optional[datetime] = None
    block_start: Optional[int] = None
    block_end: Optional[int] = None


class AuditProofOut(BaseModel):
    block_index: int
    current_hash: str
    anchor_id: int
    leaf_index: int
    merkle_proof: List[str]

    merkle_root: str
    tx_hash: Optional[str] = None
    network: Optional[str] = None
    contract_address: Optional[str] = None
    anchored_at: Optional[datetime] = None



class InclusionVerifyResult(BaseModel):
    ok: bool
    block_index: int
    anchor_id: Optional[int] = None
    leaf_index: Optional[int] = None
    proof_len: Optional[int] = None
    expected_root: Optional[str] = None
    computed_root: Optional[str] = None
    leaf_mode: Optional[str] = None
    message: str
