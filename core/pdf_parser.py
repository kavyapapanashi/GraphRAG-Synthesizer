"""
PDF Ingestion and Chunking Module for GraphRAG
Extracts text page-by-page using PyMuPDF, preserving exact page numbers
and paragraph indices, and stores raw chunks in ChromaDB.
"""

import os
import re
import math
import hashlib
from typing import List, Dict, Any, Optional, Union
import io

# Antivirus proxy fix for Windows ssl module
if "SSLKEYLOGFILE" in os.environ and ("aswMonFltProxy" in os.environ["SSLKEYLOGFILE"] or not os.path.exists(os.environ["SSLKEYLOGFILE"])):
    os.environ.pop("SSLKEYLOGFILE", None)

import pymupdf
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings


class GeminiHybridEmbeddingFunction(EmbeddingFunction):
    """
    Embedding function for ChromaDB that utilizes Google Gemini's embedding API
    when an API key is available, and falls back to a deterministic, high-dimensional
    n-gram term frequency vector representation when offline or key is missing.
    """
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._gemini_client = None
        self._vector_dim = 256
        
        if self.api_key and not self.api_key.startswith("your_") and not self.api_key.endswith("...") and len(self.api_key) > 20:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[EmbeddingFunction] Gemini client init notice: {e}. Using deterministic vector fallback.")

    def name(self) -> str:
        return "gemini_hybrid_embedding"

    def get_config(self) -> Dict[str, Any]:
        return {"model": "text-embedding-004", "vector_dim": self._vector_dim}

    def _hash_embed(self, text: str) -> List[float]:
        """Compute deterministic normalized TF vector for text matching."""
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
        vec = [0.0] * self._vector_dim
        if not tokens:
            return vec
        
        # Word and character bigram hashing
        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self._vector_dim
            vec[h] += 1.0
            
            # Character n-grams for subword matching
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    sub = token[i:i+3]
                    h_sub = int(hashlib.sha1(sub.encode("utf-8")).hexdigest(), 16) % self._vector_dim
                    vec[h_sub] += 0.3
        
        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def __call__(self, input: Documents) -> Embeddings:
        """Embed a list of text documents."""
        embeddings: List[List[float]] = []
        
        if self._gemini_client:
            try:
                # Use Gemini text-embedding-004
                for doc in input:
                    # Truncate to reasonable token limit if needed
                    truncated_doc = doc[:4000]
                    res = self._gemini_client.models.embed_content(
                        model="text-embedding-004",
                        contents=truncated_doc
                    )
                    if hasattr(res, "embedding") and hasattr(res.embedding, "values"):
                        embeddings.append(res.embedding.values)
                    elif hasattr(res, "embeddings") and len(res.embeddings) > 0:
                        embeddings.append(res.embeddings[0].values)
                    else:
                        embeddings.append(self._hash_embed(doc))
                return embeddings
            except Exception as e:
                # Fallback gracefully and disable client to prevent retry delays
                self._gemini_client = None
                embeddings = []
        
        # Fallback to deterministic n-gram vector embeddings
        for doc in input:
            embeddings.append(self._hash_embed(doc))
        return embeddings


def parse_pdf(file_input: Union[str, bytes, io.BytesIO], paper_name: str) -> List[Dict[str, Any]]:
    """
    Extracts text page-by-page using PyMuPDF, preserving exact page numbers (1-indexed)
    and paragraph indices with strict citation metadata.
    
    Returns:
        List of chunk dicts: {
            "chunk_id": str,
            "paper_name": str,
            "page_num": int,
            "chunk_idx": int,
            "text": str,
            "char_count": int
        }
    """
    chunks: List[Dict[str, Any]] = []
    clean_paper_name = os.path.basename(paper_name).replace(".pdf", "")
    
    # Open PDF from path, bytes, or stream
    if isinstance(file_input, str):
        doc = pymupdf.open(file_input)
    elif isinstance(file_input, bytes):
        doc = pymupdf.open(stream=file_input, filetype="pdf")
    elif isinstance(file_input, io.BytesIO):
        doc = pymupdf.open(stream=file_input.getvalue(), filetype="pdf")
    else:
        # File-like object (e.g. Streamlit UploadedFile)
        doc = pymupdf.open(stream=file_input.read(), filetype="pdf")
    
    try:
        for page_idx in range(len(doc)):
            page_num = page_idx + 1  # 1-indexed page number
            page = doc[page_idx]
            
            # Extract structured text blocks (x0, y0, x1, y1, text, block_no, block_type)
            blocks = page.get_text("blocks")
            paragraph_idx = 1
            
            for b in blocks:
                # block_type 0 is text
                if len(b) >= 5 and (len(b) < 7 or b[6] == 0):
                    raw_text = b[4].strip()
                    
                    # Clean up text
                    # Remove trailing hyphenated linebreaks (e.g. "com-\nputer" -> "computer")
                    cleaned_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', raw_text)
                    cleaned_text = re.sub(r'\n+', ' ', cleaned_text)
                    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                    
                    # Filter out purely decorative strings or standalone page numbers
                    if len(cleaned_text) < 25 and (cleaned_text.isdigit() or cleaned_text.lower().startswith("page ")):
                        continue
                    
                    if len(cleaned_text) >= 30:  # Minimum meaningful paragraph length
                        chunk_id = f"{clean_paper_name}_p{page_num}_c{paragraph_idx}"
                        chunks.append({
                            "chunk_id": chunk_id,
                            "paper_name": clean_paper_name,
                            "page_num": page_num,
                            "chunk_idx": paragraph_idx,
                            "text": cleaned_text,
                            "char_count": len(cleaned_text)
                        })
                        paragraph_idx += 1
                        
            # If no blocks were extracted (e.g. dense single column layout), fallback to text splitting
            if paragraph_idx == 1:
                page_text = page.get_text().strip()
                if page_text:
                    paragraphs = [p.strip() for p in page_text.split("\n\n") if len(p.strip()) >= 30]
                    for idx, para in enumerate(paragraphs, 1):
                        cleaned_para = re.sub(r'\s+', ' ', para).strip()
                        chunk_id = f"{clean_paper_name}_p{page_num}_c{idx}"
                        chunks.append({
                            "chunk_id": chunk_id,
                            "paper_name": clean_paper_name,
                            "page_num": page_num,
                            "chunk_idx": idx,
                            "text": cleaned_para,
                            "char_count": len(cleaned_para)
                        })
    finally:
        doc.close()
        
    return chunks


def get_chroma_client(persist_directory: str = "./data/chroma_db"):
    """Initialize or load a local persistent ChromaDB client."""
    os.makedirs(persist_directory, exist_ok=True)
    return chromadb.PersistentClient(path=persist_directory)


def store_chunks_in_chromadb(
    chunks: List[Dict[str, Any]], 
    collection_name: str = "research_papers",
    persist_directory: str = "./data/chroma_db",
    api_key: Optional[str] = None,
    client: Optional[chromadb.PersistentClient] = None
) -> Dict[str, Any]:
    """
    Stores raw chunks with citation metadata in a local ChromaDB collection.
    
    Metadata includes:
    - paper_name: Canonical paper title
    - page_num: Exact page number (1-indexed)
    - chunk_id: Unique chunk identifier
    """
    if client is None:
        client = get_chroma_client(persist_directory)
        
    embedding_fn = GeminiHybridEmbeddingFunction(api_key=api_key)
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"description": "GraphRAG Academic Papers Knowledge Base"}
    )
    
    if not chunks:
        return {"status": "empty", "stored_count": 0, "collection_total": collection.count()}
    
    ids = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "paper_name": c["paper_name"],
            "page_num": int(c["page_num"]),
            "chunk_idx": int(c["chunk_idx"]),
            "chunk_id": c["chunk_id"]
        }
        for c in chunks
    ]
    
    # Upsert in batches of 100 to stay well within limits
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        b_ids = ids[i:i+batch_size]
        b_docs = documents[i:i+batch_size]
        b_meta = metadatas[i:i+batch_size]
        collection.upsert(
            ids=b_ids,
            documents=b_docs,
            metadatas=b_meta
        )
        
    return {
        "status": "success",
        "stored_count": len(chunks),
        "collection_total": collection.count(),
        "collection": collection
    }
