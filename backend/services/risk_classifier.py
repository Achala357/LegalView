# risk_classifier.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification


DEFAULT_MODEL_NAME = "models/legalbert-risk-classifier"


@dataclass
class ClauseInput:
    clause_text: str
    question: str
    contract_type: str  # m_and_a / employment / nda


@dataclass
class ClausePrediction:
    p_risky: float
    p_safe: float
    predicted_label: str  # "safe" or "risky"
    confidence: float     # max prob


class RiskClassifier:
    """
    Production wrapper for a fine-tuned LegalBERT (sequence classification) model.

    Input text formulation:
      [contract_type] + question + clause_text

    This is deliberate:
    - question ~ clause semantic identity (“What is the non-compete clause?”)
    - clause_text carries the legal specifics
    - contract_type gives domain context (employment vs nda vs m&a)
    """

    def __init__(
        self,
        model_dir_or_name: str = DEFAULT_MODEL_NAME,
        device: Optional[str] = None,
        max_length: int = 256,
    ):
        self.model_dir_or_name = model_dir_or_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir_or_name, local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir_or_name, local_files_only=True)


        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model.to(self.device)
        self.model.eval()

        self.max_length = max_length
        # You trained with labels: safe=0, risky=1
        self.id2label = {0: "safe", 1: "risky"}
        self.label2id = {"safe": 0, "risky": 1}

    def _build_text(self, ci: ClauseInput) -> str:
        # compact and stable formatting
        return f"[{ci.contract_type}] {ci.question} {ci.clause_text}"

    @torch.inference_mode()
    def predict(self, clauses: List[ClauseInput], batch_size: int = 16) -> List[ClausePrediction]:
        preds: List[ClausePrediction] = []

        for i in range(0, len(clauses), batch_size):
            batch = clauses[i:i+batch_size]
            texts = [self._build_text(ci) for ci in batch]

            enc = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            ).to(self.device)

            out = self.model(**enc)
            logits = out.logits
            probs = torch.softmax(logits, dim=-1).detach().cpu().numpy()

            for p in probs:
                p_safe, p_risky = float(p[0]), float(p[1])
                if p_risky >= p_safe:
                    label = "risky"
                    conf = p_risky
                else:
                    label = "safe"
                    conf = p_safe
                preds.append(
                    ClausePrediction(
                        p_risky=p_risky,
                        p_safe=p_safe,
                        predicted_label=label,
                        confidence=conf,
                    )
                )

        return preds

    def save(self, out_dir: str) -> None:
        self.model.save_pretrained(out_dir)
        self.tokenizer.save_pretrained(out_dir)

    @staticmethod
    def load(model_dir: str, device: Optional[str] = None, max_length: int = 256) -> "RiskClassifier":
        return RiskClassifier(model_dir_or_name=model_dir, device=device, max_length=max_length)
