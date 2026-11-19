from __future__ import annotations

import hashlib
import os
import pickle
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from services.rag.faiss_store import FaissStore


# Match what your main.py uses (so dims align: e5-base-v2 => 768)
DEFAULT_EMBED_MODEL = os.getenv("UPLOAD_EMBED_MODEL", "intfloat/e5-base-v2")
DEFAULT_STORE_DIR = os.getenv("UPLOAD_FAISS_DIR", "indexes/uploads")


def _hash_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def _upload_folder(filename: str, store_dir: str = DEFAULT_STORE_DIR) -> str:
    """
    Folder for one uploaded file's FAISS artifacts.
    We hash the upload filename (which includes timestamp) so it's stable + filesystem-safe.
    """
    return os.path.join(store_dir, _hash_id(filename))


def chunk_text_by_words(text: str, chunk_words: int = 220, overlap_words: int = 40) -> List[str]:
    """
    Simple word-based chunking (fast + stable).
    """
    if not text:
        return []

    words = text.split()
    if not words:
        return []

    if chunk_words <= 0:
        chunk_words = 220
    if overlap_words < 0:
        overlap_words = 0
    if overlap_words >= chunk_words:
        overlap_words = max(0, chunk_words // 5)

    chunks: List[str] = []
    step = chunk_words - overlap_words

    i = 0
    while i < len(words):
        chunk = words[i : i + chunk_words]
        if chunk:
            chunks.append(" ".join(chunk))
        i += step

    return chunks


@dataclass
class UploadChunk:
    chunk_index: int
    text: str


# Small cache so we don't reload embedder+index repeatedly for same upload
_UPLOAD_STORE_CACHE: Dict[str, FaissStore] = {}


def build_upload_store_from_text(
    contract_text: str,
    filename: str,
    embed_model_name: str = DEFAULT_EMBED_MODEL,
    store_dir: str = DEFAULT_STORE_DIR,
    chunk_words: int = 220,
    overlap_words: int = 40,
) -> Optional[FaissStore]:
    """
    Build a per-upload FAISS index on disk under:
      indexes/uploads/<hash(filename)>/{index.faiss, meta.pkl}

    Returns a FaissStore (also cached), or None if text is empty.
    """
    if not filename:
        return None

    if not contract_text or not contract_text.strip():
        return None

    folder = _upload_folder(filename, store_dir=store_dir)
    os.makedirs(folder, exist_ok=True)

    index_path = os.path.join(folder, "index.faiss")
    meta_path = os.path.join(folder, "meta.pkl")

    # If already exists, just load it
    if os.path.exists(index_path) and os.path.exists(meta_path):
        store = FaissStore(
            index_path=index_path,
            metadata_path=meta_path,
            embed_model_name=embed_model_name,
            query_prefix="query: ",
            normalize_embeddings=True,
        )
        _UPLOAD_STORE_CACHE[filename] = store
        return store

    # Chunk
    chunks = chunk_text_by_words(contract_text, chunk_words=chunk_words, overlap_words=overlap_words)
    if not chunks:
        return None

    upload_chunks = [UploadChunk(i, c) for i, c in enumerate(chunks)]

    # Embed
    embedder = SentenceTransformer(embed_model_name)
    vecs = embedder.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,  # cosine via inner product
    )
    vecs = np.asarray(vecs, dtype="float32")

    d = vecs.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(vecs)

    # Metadata aligned with vectors
    metadata: List[Dict[str, Any]] = []
    for c in upload_chunks:
        metadata.append(
            {
                "contract_id": filename,        # key we can use for filtering/debug
                "chunk_index": c.chunk_index,
                "text": c.text,
                "source": "upload",
            }
        )

    # Persist
    faiss.write_index(index, index_path)
    with open(meta_path, "wb") as f:
        pickle.dump(metadata, f)

    # Wrap
    store = FaissStore(
        index_path=index_path,
        metadata_path=meta_path,
        embed_model_name=embed_model_name,
        query_prefix="query: ",
        normalize_embeddings=True,
    )
    _UPLOAD_STORE_CACHE[filename] = store
    return store


def get_upload_store(
    filename: str,
    embed_model_name: str = DEFAULT_EMBED_MODEL,
    store_dir: str = DEFAULT_STORE_DIR,
) -> Optional[FaissStore]:
    """
    Load the per-upload FAISS store for a given uploaded filename (if it exists).
    """
    if not filename:
        return None

    if filename in _UPLOAD_STORE_CACHE:
        return _UPLOAD_STORE_CACHE[filename]

    folder = _upload_folder(filename, store_dir=store_dir)
    index_path = os.path.join(folder, "index.faiss")
    meta_path = os.path.join(folder, "meta.pkl")

    if not (os.path.exists(index_path) and os.path.exists(meta_path)):
        return None

    store = FaissStore(
        index_path=index_path,
        metadata_path=meta_path,
        embed_model_name=embed_model_name,
        query_prefix="query: ",
        normalize_embeddings=True,
    )
    _UPLOAD_STORE_CACHE[filename] = store
    return store
