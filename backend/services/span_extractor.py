import re
from typing import Dict, List, Optional, Any, Tuple

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForQuestionAnswering

try:
    from sentence_transformers import CrossEncoder
except Exception:
    CrossEncoder = None


class SpanExtractor:
    """
    Production span extractor:
    - loads QA model + tokenizer once
    - extracts one best span per question using sliding-window QA
    - optionally reranks candidates with a CrossEncoder reranker
    """

    def __init__(
        self,
        qa_checkpoint_path: str,
        base_tokenizer_name: str = "microsoft/deberta-v3-large",
        device: Optional[str] = None,
        use_reranker: bool = True,
        reranker_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2",
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # IMPORTANT: for DeBERTa-v3 + sentencepiece warning, prefer use_fast=False for safety.
        # (Fast tokenizer may produce [UNK] where slow would byte-fallback.)
        self.tokenizer = AutoTokenizer.from_pretrained(base_tokenizer_name, use_fast=True)

        self.model = AutoModelForQuestionAnswering.from_pretrained(qa_checkpoint_path)
        self.model.to(self.device)
        self.model.eval()

        self.use_reranker = use_reranker and (CrossEncoder is not None)
        self.reranker = None
        if self.use_reranker:
            self.reranker = CrossEncoder(reranker_name, device=self.device)

    @staticmethod
    def _clean_span(s: str) -> str:
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _best_span_for_question(
        self,
        text: str,
        question: str,
        max_length: int = 512,
        stride: int = 128,
        max_answer_length: int = 320,
    ) -> Optional[Tuple[str, float]]:
        """
        Returns (span_text, raw_score).
        raw_score is start_logit + end_logit for the chosen span (NOT a probability).
        """

        enc = self.tokenizer(
            question,
            text,
            truncation="only_second",
            max_length=max_length,
            stride=stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            padding="max_length",
            return_tensors="pt",
        )

        input_ids = enc["input_ids"].to(self.device)
        attn_mask = enc["attention_mask"].to(self.device)
        token_type_ids = enc.get("token_type_ids")
        if token_type_ids is not None:
            token_type_ids = token_type_ids.to(self.device)

        offsets_all = enc["offset_mapping"]  # on CPU

        best_score = None
        best_span = None

        with torch.no_grad():
            for i in range(input_ids.size(0)):
                batch = {
                    "input_ids": input_ids[i : i + 1],
                    "attention_mask": attn_mask[i : i + 1],
                }
                if token_type_ids is not None:
                    batch["token_type_ids"] = token_type_ids[i : i + 1]

                out = self.model(**batch)
                start_logits = out.start_logits[0].detach().cpu().numpy()
                end_logits = out.end_logits[0].detach().cpu().numpy()

                # Choose best span in this window with a simple constraint:
                # end >= start and length <= max_answer_length (in tokens)
                # (A stronger version would do full n-best search; this is usually enough.)
                start_idx = int(np.argmax(start_logits))
                end_idx = int(np.argmax(end_logits))

                if end_idx < start_idx:
                    continue
                if (end_idx - start_idx) > max_answer_length:
                    continue
                if start_idx >= len(offsets_all[i]) or end_idx >= len(offsets_all[i]):
                    continue

                s_char = int(offsets_all[i][start_idx][0])
                e_char = int(offsets_all[i][end_idx][1])
                if e_char <= s_char:
                    continue

                span = self._clean_span(text[s_char:e_char])
                if not span:
                    continue

                score = float(start_logits[start_idx] + end_logits[end_idx])
                if (best_score is None) or (score > best_score):
                    best_score = score
                    best_span = span

        if best_span is None:
            return None
        return best_span, float(best_score)

    def extract(
        self,
        text: str,
        contract_type: str,
        question_bank: List[str],
        max_per_contract: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract spans for a single contract text.
        Returns list of records with clause_text/question/contract_type/score
        score:
          - if reranker enabled: reranker score
          - else: QA raw score (start+end logits)
        """

        text = text.strip()
        if not text:
            return []

        candidates: List[Dict[str, Any]] = []
        for q in question_bank:
            res = self._best_span_for_question(text, q)
            if not res:
                continue
            span, qa_score = res
            candidates.append(
                {
                    "clause_text": span,
                    "question": q,
                    "contract_type": contract_type,
                    "qa_score": qa_score,
                }
            )

        if not candidates:
            return []

        # Optional rerank (recommended)
        if self.use_reranker and self.reranker is not None:
            pairs = [(c["question"], c["clause_text"]) for c in candidates]
            rr_scores = self.reranker.predict(pairs, batch_size=32)
            for c, sc in zip(candidates, rr_scores):
                c["score"] = float(sc)  # final score used downstream
        else:
            for c in candidates:
                c["score"] = float(c["qa_score"])

        # Sort by final score
        candidates.sort(key=lambda x: x["score"], reverse=True)

        if max_per_contract is not None:
            candidates = candidates[:max_per_contract]

        # Drop internal field unless you want it
        for c in candidates:
            c.pop("qa_score", None)

        return candidates
