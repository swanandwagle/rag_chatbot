
import faiss
import numpy as np
import pickle
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from app.config import settings


class FAISSVectorStore:
    """FAISS-based vector store with metadata storage"""
    
    def __init__(self):
        self.index_dir = Path(settings.faiss_index_dir)
        self.index_path = self.index_dir / "faiss.index"
        self.metadata_path = self.index_dir / "metadata.pkl"
        self.doc_info_path = self.index_dir / "documents.json"
        
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict] = []
        self.document_info: Dict[str, Dict] = {}
        self.dimension: Optional[int] = None
        
        # Track on-disk timestamps to detect external updates
        self._index_mtime: Optional[float] = None
        self._metadata_mtime: Optional[float] = None
        self._docinfo_mtime: Optional[float] = None
        
        # Load existing index if available
        self._load_or_create()
    
    def _load_or_create(self):
        """Load existing index or create new one"""
        if self.index_path.exists() and self.metadata_path.exists():
            self._load()
        else:
            print("No existing index found. Will create on first document addition.")
    
    def _load(self):
        """Load FAISS index and metadata from disk"""
        try:
            self.index = faiss.read_index(str(self.index_path))
            
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
            
            if self.doc_info_path.exists():
                with open(self.doc_info_path, "r") as f:
                    self.document_info = json.load(f)
            
            self.dimension = self.index.d
            print(f"Loaded FAISS index with {self.index.ntotal} vectors, dimension {self.dimension}")
            self._refresh_mtimes()
        except Exception as e:
            print(f"Error loading index: {e}")
            self.index = None
            self.metadata = []
            self.document_info = {}
    
    def _save(self):
        """Save FAISS index and metadata to disk"""
        try:
            faiss.write_index(self.index, str(self.index_path))
            
            with open(self.metadata_path, "wb") as f:
                pickle.dump(self.metadata, f)
            
            with open(self.doc_info_path, "w") as f:
                json.dump(self.document_info, f, indent=2, default=str)
            
            print(f"Saved FAISS index with {self.index.ntotal} vectors")
            self._refresh_mtimes()
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def _get_mtime(self, path: Path) -> Optional[float]:
        try:
            return path.stat().st_mtime if path.exists() else None
        except Exception:
            return None
    
    def _refresh_mtimes(self):
        """Record current mtimes of on-disk artifacts."""
        self._index_mtime = self._get_mtime(self.index_path)
        self._metadata_mtime = self._get_mtime(self.metadata_path)
        self._docinfo_mtime = self._get_mtime(self.doc_info_path)
    
    def _reload_if_changed(self):
        """Reload from disk if files were modified by another process/instance."""
        index_m = self._get_mtime(self.index_path)
        meta_m = self._get_mtime(self.metadata_path)
        doc_m = self._get_mtime(self.doc_info_path)

        # If we don't have an in-memory index yet but the artifacts now exist, load them
        if self.index is None and self.index_path.exists() and self.metadata_path.exists():
            self._load()
            return

        # If any of the files now exist but we have no recorded mtime, treat as changed
        mtime_became_available = (
            (index_m is not None and self._index_mtime is None) or
            (meta_m is not None and self._metadata_mtime is None) or
            (doc_m is not None and self._docinfo_mtime is None)
        )

        # If any of the files are newer than our recorded mtimes, reload
        changed_after = (
            (self._index_mtime is not None and index_m is not None and index_m > self._index_mtime) or
            (self._metadata_mtime is not None and meta_m is not None and meta_m > self._metadata_mtime) or
            (self._docinfo_mtime is not None and doc_m is not None and doc_m > self._docinfo_mtime)
        )

        if mtime_became_available or changed_after:
            self._load()
    
    async def add_documents(
        self, 
        chunks: List[Dict[str, str]], 
        embeddings: List[List[float]],
        document_id: str,
        filename: str
    ):
        """
        Add document chunks and embeddings to vector store
        
        Args:
            chunks: List of chunk dictionaries with content and metadata
            embeddings: List of embedding vectors
            document_id: Unique document identifier
            filename: Original filename
        """
        # Convert embeddings to numpy array and L2-normalize for cosine-like similarity with L2 metric
        embeddings_array = np.array(embeddings, dtype=np.float32)
        if embeddings_array.ndim != 2:
            raise ValueError("Embeddings array must be 2-dimensional")
        # Normalize in-place
        faiss.normalize_L2(embeddings_array)
        
        # Initialize index if this is the first document
        if self.index is None:
            self.dimension = embeddings_array.shape[1]
            # Use HNSW index for better performance
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
            # Improve recall during construction and search
            try:
                self.index.hnsw.efConstruction = 100
                self.index.hnsw.efSearch = 128
            except Exception:
                pass
            print(f"Created new FAISS HNSW index with dimension {self.dimension}")
        
        # Add embeddings to FAISS index
        self.index.add(embeddings_array)
        
        # Add metadata for each chunk
        for chunk in chunks:
            chunk_metadata = {
                "document_id": document_id,
                "filename": filename,
                "content": chunk["content"],
                "chunk_index": chunk["chunk_index"],
                "total_chunks": chunk["total_chunks"],
                "added_at": datetime.utcnow().isoformat()
            }
            self.metadata.append(chunk_metadata)
        
        # Store document info
        self.document_info[document_id] = {
            "filename": filename,
            "upload_date": datetime.utcnow().isoformat(),
            "chunk_count": len(chunks)
        }
        
        # Save to disk
        self._save()
    
    async def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for similar chunks using query embedding
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of similar chunks with metadata and scores
        """
        # Ensure we see the latest index/metadata written by other instances
        self._reload_if_changed()
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Convert to numpy array and L2-normalize
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Tune efSearch based on requested top_k (best-effort)
        try:
            target_ef = max(64, min(512, int(top_k) * 32))
            if hasattr(self.index, "hnsw"):
                # Only increase efSearch; avoid reducing it if already higher
                current = getattr(self.index.hnsw, "efSearch", 64)
                if target_ef > current:
                    self.index.hnsw.efSearch = target_ef
        except Exception:
            pass

        # Search FAISS index
        distances, indices = self.index.search(query_array, min(top_k, self.index.ntotal))
        
        # Prepare results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx is None:
                continue
            # Guard against invalid indices sometimes returned by ANN indices
            if idx >= 0 and idx < len(self.metadata):
                # With L2 on unit vectors, cos = 1 - dist/2; map to [0,1] for readability
                cosine = 1.0 - float(dist) / 2.0
                # Clamp cosine to [-1, 1]
                if cosine > 1.0:
                    cosine = 1.0
                elif cosine < -1.0:
                    cosine = -1.0
                similarity_01 = (cosine + 1.0) / 2.0
                result = {
                    **self.metadata[idx],
                    "similarity_score": similarity_01
                }
                results.append(result)
        
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        # Pick up external updates for accurate counts
        self._reload_if_changed()
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "total_documents": len(self.document_info),
            "documents": list(self.document_info.values())
        }
    
    def get_document_info(self, document_id: str) -> Optional[Dict]:
        """Get information about a specific document"""
        self._reload_if_changed()
        return self.document_info.get(document_id)

