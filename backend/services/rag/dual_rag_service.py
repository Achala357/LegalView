from __future__ import annotations

from typing import Any, Dict, List, Optional
import os

from dotenv import load_dotenv
from openai import OpenAI

from services.rag.faiss_store import FaissStore
from services.rag.upload_faiss_builder import get_upload_store


CASE_LAW_TRIGGERS = [
    "sri lanka", "sri lankan", "law", "legal", "court", "precedent",
    "damages", "breach", "liability", "interpret", "held", "according to",
]


def needs_case_law(question: str) -> bool:
    q = (question or "").lower()
    return any(t in q for t in CASE_LAW_TRIGGERS)


def _safe_text(x: Any, max_chars: int = 2000) -> str:
    if x is None:
        return ""
    s = str(x)
    if len(s) > max_chars:
        return s[:max_chars] + "…"
    return s


def build_structured_context_block(
    extracted_spans: Optional[List[Dict[str, Any]]],
    risk_clauses: Optional[List[Dict[str, Any]]],
    risk_assessment: Optional[Dict[str, Any]],
    contract_type: Optional[str] = None,
    max_items: int = 10,
) -> str:
    parts: List[str] = []

    if contract_type:
        parts.append(f"Contract Type: {contract_type}")

    if risk_assessment:
        parts.append("Contract Risk Summary:")
        parts.append(_safe_text(risk_assessment, max_chars=1500))

    if risk_clauses:
        risky_first = sorted(
            risk_clauses,
            key=lambda c: (
                0 if c.get("risk_label") == "risky" else 1,
                -(float(c.get("p_risky", 0.0) or 0.0)),
            ),
        )
        parts.append("\nTop Clause-Level Risk Signals:")
        for c in risky_first[:max_items]:
            clause_type = c.get("clause_type", "unknown")
            label = c.get("risk_label", "unknown")
            conf = c.get("risk_confidence", None)
            p_risky = c.get("p_risky", None)

            line = f"- {clause_type} | label={label}"
            if conf is not None:
                line += f" | confidence={conf}"
            if p_risky is not None:
                line += f" | p_risky={p_risky}"

            xai = c.get("xai")
            if isinstance(xai, dict) and xai.get("narrative"):
                line += f"\n  xai: {_safe_text(xai.get('narrative'), max_chars=400)}"

            parts.append(line)

    if extracted_spans:
        parts.append("\nExtracted Clause Spans (high-level):")
        for s in extracted_spans[:max_items]:
            q = s.get("question", "unknown question")
            txt = s.get("clause_text") or s.get("text") or ""
            parts.append(f"- Q: {_safe_text(q, 160)}\n  span: {_safe_text(txt, 300)}")

    return "\n".join(parts).strip() if parts else ""


def build_prompt(
    question: str,
    contract_hits,
    case_hits,
    structured_block: str = "",
) -> str:
    if contract_hits:
        contract_block = "\n\n".join(
            f"[Contract Evidence]\n{h.text}" for h in contract_hits
        )
    else:
        contract_block = "(no retrieved contract evidence available for this uploaded contract)"

    case_block = ""
    if case_hits:
        case_block = "\n\nSri Lankan Supreme Court References:\n"
        for h in case_hits:
            case_id = h.meta.get("case_id", "UNKNOWN_CASE")
            p1 = h.meta.get("page_start", "?")
            p2 = h.meta.get("page_end", "?")
            case_block += f"- {case_id} (pp. {p1}-{p2})\n"

    structured_section = ""
    if structured_block.strip():
        structured_section = (
            "\n\nStructured Context (from the contract analysis pipeline):\n"
            + structured_block
            + "\n"
        )

    return f"""
You are a legal assistant analysing contracts under Sri Lankan law.

Question:
{question}

Primary Contract Evidence (retrieved):
{contract_block}
{structured_section}
{case_block}

Instructions:
- Base the answer primarily on the contract evidence (retrieved + structured context).
- Use Sri Lankan case law only to explain legal principles (not to invent facts).
- Cite cases by case ID and page range when used.
- If the contract does not contain enough information, say what is missing.
- Do not invent legal authorities or citations.
""".strip()


class DualRAGService:
    def __init__(
        self,
        contract_store: FaissStore,
        case_law_store: FaissStore,
        openai_model: str = "gpt-4o-mini",
    ):
        load_dotenv()
        self.client = None
        self.openai_model = openai_model

        self.contract_store = contract_store
        self.case_law_store = case_law_store

    def answer(
        self,
        question: str,
        extracted_spans: Optional[List[Dict[str, Any]]] = None,
        risk_clauses: Optional[List[Dict[str, Any]]] = None,
        risk_assessment: Optional[Dict[str, Any]] = None,
        top_k_contract: int = 5,
        top_k_case: int = 3,
        structured_context: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
        contract_store_override: Optional[FaissStore] = None,
    ) -> Dict[str, Any]:

        # Merge structured_context (if provided)
        contract_type = None
        if structured_context:
            extracted_spans = extracted_spans or structured_context.get("extracted_spans")
            risk_clauses = risk_clauses or structured_context.get("risk_clauses")
            risk_assessment = risk_assessment or structured_context.get("risk_assessment")
            contract_type = structured_context.get("contract_type")
            filename = filename or structured_context.get("filename")

        extracted_spans = extracted_spans or []
        risk_clauses = risk_clauses or []
        risk_assessment = risk_assessment or {}

        # -----------------------------
        # Contract retrieval source selection
        # -----------------------------
        upload_store = get_upload_store(filename) if filename else None
        used_upload_index = bool(upload_store)
        used_global_fallback = False

        contract_hits = []

        if upload_store:
            contract_hits = upload_store.search(question, top_k=top_k_contract)
        elif contract_store_override:
            # Explicit override (debug use)
            contract_hits = contract_store_override.search(question, top_k=top_k_contract)
            used_global_fallback = True
        else:
            # IMPORTANT: if filename is provided but upload store is missing,
            # do NOT query the global contract index (it will leak other contracts).
            if filename:
                contract_hits = []
            else:
                contract_hits = self.contract_store.search(question, top_k=top_k_contract)
                used_global_fallback = True

        # Case law retrieval (optional)
        case_hits = []
        if needs_case_law(question) and top_k_case > 0:
            case_hits = self.case_law_store.search(question, top_k=top_k_case)

        structured_block = build_structured_context_block(
            contract_type=contract_type,
            extracted_spans=extracted_spans,
            risk_clauses=risk_clauses,
            risk_assessment=risk_assessment,
        )

        prompt = build_prompt(
            question=question,
            contract_hits=contract_hits,
            case_hits=case_hits,
            structured_block=structured_block,
        )


        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not configured. "
                    "Set this environment variable to use Dual RAG answers."
                )

            self.client = OpenAI(api_key=api_key)






        resp = self.client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": "You are a careful legal assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        answer_text = resp.choices[0].message.content

        return {
            "answer": answer_text,
            "contract_evidence": [
                {"text": h.text, "meta": h.meta, "score": h.score} for h in contract_hits
            ],
            "sri_lanka_precedents": [
                {
                    "case_id": h.meta.get("case_id"),
                    "page_start": h.meta.get("page_start"),
                    "page_end": h.meta.get("page_end"),
                    "score": h.score,
                }
                for h in case_hits
            ],
            "used_case_law": bool(case_hits),
            "used_structured_context": bool(structured_block.strip()),
            "used_upload_index": used_upload_index,
            "used_global_fallback": used_global_fallback,
        }
