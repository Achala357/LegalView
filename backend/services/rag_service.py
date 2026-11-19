from typing import List, Dict
from services.llm_client import generate_answer

def build_rag_context(
    extracted_spans: List[Dict],
    risk_clauses: List[Dict],
    risk_assessment: Dict
) -> str:
    context_parts = []

    context_parts.append("=== CONTRACT RISK SUMMARY ===")
    context_parts.append(f"Overall risk level: {risk_assessment['risk_level']}")
    context_parts.append(f"Risk score: {risk_assessment['contract_risk_score']}")
    context_parts.append("")

    context_parts.append("=== IDENTIFIED CLAUSES ===")
    for clause in risk_clauses:
        context_parts.append(
            f"- Clause type: {clause['clause_type']}\n"
            f"  Risk: {clause['risk_label']} ({clause['risk_confidence']})\n"
            f"  Text: {clause['clause_text']}"
        )

    if risk_assessment.get("missing_clauses"):
        context_parts.append("")
        context_parts.append("=== MISSING CLAUSES ===")
        for mc in risk_assessment["missing_clauses"]:
            context_parts.append(f"- {mc}")

    return "\n\n".join(context_parts)


def answer_question(question: str, rag_context: str) -> str:
    prompt = f"""
You are a legal contract analysis assistant.

Answer the user's question using ONLY the information below.
If the information is not present, say so explicitly.

CONTEXT:
{rag_context}

QUESTION:
{question}

ANSWER:
"""

    return generate_answer(prompt)
