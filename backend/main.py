from fastapi import FastAPI, File, UploadFile, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from docx import Document
from datetime import datetime
import json
import os
from uuid import uuid4
from services.span_extractor import SpanExtractor
from services import model_registry
from audit.logger import log_event
from audit.db import SessionLocal
from services.risk_classifier import RiskClassifier
from services.risk_engine import RiskEngine
from services.rag.faiss_store import FaissStore
from services.rag.dual_rag_service import DualRAGService
from dotenv import load_dotenv
import logging
load_dotenv()
logger = logging.getLogger(__name__)







# Create FastAPI app
app = FastAPI()


QUESTION_BANKS = {
    "nda": [
        "What is the definition of confidential information?",
        "What are the exclusions from confidentiality?",
        "What is the non-use clause?",
        "What are the obligations of the receiving party?",
        "What is the return or destruction of materials clause?",
        "What is the residual knowledge clause?",
        "What is the no-license-granted clause?",
        "What is the non-disclosure of existence clause?",
        "What is the permitted disclosure clause?",
        "What is the duration or survival of confidentiality obligations?",
        "What is the remedies clause for breach of confidentiality?",
        "What is the limitation of liability clause?",
        "What is the indemnification clause (if present)?",
        "What is the dispute resolution or arbitration clause?",
        "What is the governing law clause?",
        "What is the waiver clause?",
        "What is the assignment clause?",
        "What is the amendment or modification clause?",
        "What is the notices clause?",
        "What is the severability clause?",
        "What is the entire agreement or integration clause?",
        "What is the non-solicitation clause (if present)?"
    ],
    "m_and_a": [
        "What is the purchase price clause?",
        "What is the closing conditions clause?",
        "What is the representations and warranties clause?",
        "What is the seller representations clause?",
        "What is the buyer representations clause?",
        "What is the material adverse effect (MAE) clause?",
        "What is the working capital adjustment clause?",
        "What is the escrow or holdback clause?",
        "What is the earn-out or contingent payment clause?",
        "What is the termination fee or breakup fee clause?",
        "What is the indemnification clause?",
        "What is the indemnity basket and cap clause?",
        "What is the post-closing obligations clause?",
        "What is the employee transition or retention clause?",
        "What is the intellectual property transfer clause?",
        "What is the non-compete clause?",
        "What is the non-solicitation clause?",
        "What is the regulatory approvals clause?",
        "What is the confidentiality clause?",
        "What is the dispute resolution or arbitration clause?",
        "What is the governing law clause?",
        "What is the assignment clause?",
        "What is the integration or entire agreement clause?",
        "What is the waiver clause?",
        "What is the severability clause?"
    ],
    "employment": [
        "What is the termination clause?",
        "What is the employment term clause?",
        "What is the probation period clause?",
        "What are the duties and responsibilities clauses?",
        "What is the compensation clause?",
        "What is the bonus or commission clause?",
        "What is the benefits clause?",
        "What is the working hours clause?",
        "What is the overtime clause?",
        "What is the confidentiality clause?",
        "What is the IP assignment or ownership clause?",
        "What is the non-compete clause?",
        "What is the non-solicitation clause?",
        "What is the performance review clause?",
        "What is the notice period clause?",
        "What is the termination for cause clause?",
        "What is the termination without cause clause?",
        "What is the severance clause?",
        "What is the dispute resolution or arbitration clause?",
        "What is the governing law clause?",
        "What is the assignment clause?",
        "What is the amendment or modification clause?",
        "What is the waiver clause?",
        "What is the entire agreement or integration clause?"
    ],
    "other": [],
}
@app.on_event("startup")
def startup():
    model_registry.SPAN_EXTRACTOR = SpanExtractor(
        qa_checkpoint_path="models/span_extractor",
        use_reranker=True,
    )

    #  Load risk classifier + engine once at startup
    model_registry.RISK_CLASSIFIER = RiskClassifier(
        model_dir_or_name="models/legalbert_risk_classifier"
    )
    model_registry.RISK_ENGINE = RiskEngine(
        classifier=model_registry.RISK_CLASSIFIER,
        priors=None,       # we can plug real priors later
        v2_weights=None
    )

    model_registry.QUESTION_BANKS = QUESTION_BANKS

    model_registry.CONTRACT_STORE = FaissStore(
    index_path="models/rag/contract/contracts_15k_merged.faiss.index",
    metadata_path="models/rag/contract/contracts_15k_merged.metadata.jsonl",
    embed_model_name="intfloat/e5-base-v2",
    )

    model_registry.CASELAW_STORE = FaissStore(
        index_path="models/rag/case_law/case_law.faiss.index",
        metadata_path="models/rag/case_law/case_law.metadata.jsonl",
        embed_model_name="intfloat/e5-base-v2",
    )

    model_registry.DUAL_RAG = DualRAGService(
        contract_store=model_registry.CONTRACT_STORE,
        case_law_store=model_registry.CASELAW_STORE,
        openai_model="gpt-4o-mini",
    )

# Create router
router = APIRouter()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory setup
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
METADATA_FILE = BASE_DIR / "upload_metadata.json"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Static file CORS override
from starlette.responses import Response
class CORSEnabledStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

app.mount("/uploads", CORSEnabledStaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Upload endpoint
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file bytes
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Generate unique stored filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = file.filename
        ext = Path(original_name).suffix or ".txt"
        file_id = str(uuid4())[:8]
        filename = f"{timestamp}_{file_id}{ext}"

        # ✅ FIX: define the variable you're using later
        unique_filename = filename

        save_path = UPLOAD_DIR / unique_filename
        save_path.write_bytes(content)

        # Update upload_metadata.json
        metadata = {
            "filename": unique_filename,
            "original_name": original_name,
            "timestamp": timestamp,
        }
        if METADATA_FILE.exists():
            with open(METADATA_FILE, "r+", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                data.append(metadata)
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
        else:
            with open(METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump([metadata], f, indent=2)



        # Audit log (off-chain hash chain)
        db = SessionLocal()
        try:
            log_event(
                db=db,
                action_type="upload",
                actor_id="system",
                contract_id=unique_filename,
                payload=metadata,
            )
        finally:
            db.close()


        return {
            "message": "Upload successful",
            "filename": unique_filename,
            "original_name": original_name,
            "timestamp": timestamp,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=str(e))




# Get uploaded metadata
@app.get("/api/uploads")
async def get_uploads():
    if not METADATA_FILE.exists():
        return []
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# Preview file (txt/docx)
@app.get("/api/file/{filename}")
async def preview_file(filename: str):
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        if filename.endswith(".txt"):
            return JSONResponse(content={"content": path.read_text(encoding="utf-8")})
        elif filename.endswith(".docx"):
            doc = Document(str(path))
            full_text = "\n".join([para.text for para in doc.paragraphs])
            return JSONResponse(content={"content": full_text})
        else:
            return JSONResponse(status_code=400, content={"error": "Unsupported file type"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Internal error: {str(e)}"})


@router.delete("/api/uploads/{filename}")
def delete_uploaded_file(filename: str):
    uploads_dir = UPLOAD_DIR
    metadata_path = METADATA_FILE
    file_path = uploads_dir / filename

    # Load metadata
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            try:
                metadata = json.load(f)
            except json.JSONDecodeError:
                metadata = []
    else:
        metadata = []

    # Find metadata entry
    deleted_meta = next((m for m in metadata if m.get("filename") == filename), None)

    # Try remove file (don't fail if already missing)
    file_existed = file_path.exists()
    if file_existed:
        file_path.unlink()

    # Remove metadata entry (ALWAYS attempt this)
    if deleted_meta:
        metadata = [m for m in metadata if m.get("filename") != filename]
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    else:
        # If neither file nor metadata exists, it's basically already deleted
        if not file_existed:
            raise HTTPException(status_code=404, detail="No such upload (file and metadata missing)")

    # Audit log
    db = SessionLocal()
    try:
        log_event(
            db=db,
            action_type="delete_upload",
            actor_id="system",
            contract_id=filename,
            payload={
                "stored_filename": filename,
                "original_filename": (deleted_meta["original_name"] if deleted_meta else None),
                "upload_timestamp": (deleted_meta["timestamp"] if deleted_meta else None),
                "file_existed": file_existed,  # <-- helpful for debugging
            },
        )
    finally:
        db.close()

    return {
        "message": "Upload removed successfully",
        "filename": filename,
        "file_existed": file_existed,
        "metadata_existed": bool(deleted_meta),
    }


app.include_router(router)

from audit.router import router as audit_router
app.include_router(audit_router, prefix="/api")

from audit.db import engine
from audit.models import Base
Base.metadata.create_all(bind=engine)

from routers.contracts import router as contracts_router
app.include_router(contracts_router, prefix="/api")

from routers.qa import router as qa_router
app.include_router(qa_router, prefix="/api")
