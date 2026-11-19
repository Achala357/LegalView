from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os
import json
import pickle
import re

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


@dataclass
class SearchHit:
    score: float
    text: str
    meta: Dict[str, Any]


def _load_metadata(path: str) -> List[Dict[str, Any]]:
    """
    Supports:
    - pickle (.pkl / .pickle)
    - json  (.json)    -> list[dict]
    - jsonl (.jsonl)   -> one dict per line
    """
    ext = os.path.splitext(path)[1].lower()

    if ext in [".pkl", ".pickle"]:
        with open(path, "rb") as f:
            data = pickle.load(f)
        if not isinstance(data, list):
            raise ValueError(f"Expected list in pickle metadata: {path}")
        return data

    if ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"Expected list in JSON metadata: {path}")
        return data

    if ext == ".jsonl":
        rows: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows

    raise ValueError(f"Unsupported metadata format: {path}. Use .pkl, .json, or .jsonl")


def extract_contract_id_from_upload_filename(filename: str) -> Optional[str]:
    """
    Upload filenames look like:
      20260207_185546_000000037.txt

    Index metadata contract_id usually looks like:
      000000037.txt

    This extracts the trailing NNNNNNNNN.txt part.
    """
    if not filename:
        return None
    m = re.search(r"(\d{6,12}\.txt)$", filename)
    return m.group(1) if m else filename  # fallback


def _meta_matches(meta: Dict[str, Any], where: Dict[str, Any]) -> bool:
    """
    Simple exact-match filter:
      where={"contract_id": "000000037.txt"}
    """
    for k, v in where.items():
        if v is None:
            continue
        if meta.get(k) != v:
            return False
    return True


class FaissStore:
    """
    Minimal production wrapper around:
    - SentenceTransformer embedder
    - FAISS index
    - metadata list (parallel to vectors)
    """

    def __init__(
        self,
        index_path: str,
        metadata_path: str,
        embed_model_name: str,
        query_prefix: str = "query: ",
        normalize_embeddings: bool = True,
    ):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.embed_model_name = embed_model_name
        self.query_prefix = query_prefix
        self.normalize_embeddings = normalize_embeddings

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found: {index_path}")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")

        self.embedder = SentenceTransformer(embed_model_name)
        self.index = faiss.read_index(index_path)

        self.metadata: List[Dict[str, Any]] = _load_metadata(metadata_path)

        if len(self.metadata) != self.index.ntotal:
            raise ValueError(
                f"Metadata length ({len(self.metadata)}) != index.ntotal ({self.index.ntotal})"
            )

        # Dimension sanity check
        test_vec = self.embedder.encode(
            ["query: dimension check"],
            convert_to_numpy=True,
            normalize_embeddings=self.normalize_embeddings,
        )
        test_vec = np.asarray(test_vec, dtype="float32")
        if test_vec.shape[1] != self.index.d:
            raise ValueError(
                f"Embedding dim mismatch: embedder='{embed_model_name}' gives d={test_vec.shape[1]} "
                f"but FAISS index expects d={self.index.d}. "
                f"Use the SAME embedding model you used when building the index."
            )

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        fetch_k: Optional[int] = None,
        dedupe: bool = True,
    ) -> List[SearchHit]:
        """
        FAISS retrieval + optional metadata filtering.

        - If `where` is None: behaves like old version (top_k fetch).
        - If `where` is provided: fetch more candidates then filter down to top_k.
        """

        q_text = f"{self.query_prefix}{query}" if self.query_prefix else query

        q_emb = self.embedder.encode(
            [q_text],
            convert_to_numpy=True,
            normalize_embeddings=self.normalize_embeddings,
        )
        q_emb = np.asarray(q_emb, dtype="float32")

        # Old behavior: if no filtering and no explicit fetch_k, just fetch top_k
        if where is None and fetch_k is None:
            k = top_k
        else:
            k = fetch_k or max(top_k * 25, 50)

        distances, indices = self.index.search(q_emb, k)

        hits: List[SearchHit] = []
        seen: set = set()

        for score, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue

            meta = self.metadata[idx]

            if where and not _meta_matches(meta, where):
                continue

            text = meta.get("text") or meta.get("chunk_text") or ""

            if dedupe:
                contract_id = meta.get("contract_id", "")
                chunk_index = meta.get("chunk_index", None)
                key = (contract_id, chunk_index, text[:80])
                if key in seen:
                    continue
                seen.add(key)

            hits.append(SearchHit(score=float(score), text=text, meta=meta))
            if len(hits) >= top_k:
                break

        return hits
