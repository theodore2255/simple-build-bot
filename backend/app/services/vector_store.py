import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Vector store service using ChromaDB for document chunk storage and retrieval.
    Uses sentence transformers for embedding generation.
    """
    
    def __init__(
        self, 
        collection_name: str = "document_chunks",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(
                name=self.collection_name,
                embedding_function=None  # We'll handle embeddings manually
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                embedding_function=None,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    async def store_document(self, document_id: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Store document chunks in the vector database.
        
        Args:
            document_id: Unique document identifier
            chunks: List of text chunks with metadata
            
        Returns:
            Document ID
        """
        try:
            logger.info(f"Storing {len(chunks)} chunks for document {document_id}")
            
            # Prepare data for ChromaDB
            ids = []
            texts = []
            metadatas = []
            embeddings = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_{i}"
                ids.append(chunk_id)
                texts.append(chunk['text'])
                
                # Add document_id to metadata
                metadata = chunk.get('metadata', {})
                metadata['document_id'] = document_id
                metadatas.append(metadata)
            
            # Generate embeddings for all texts at once (more efficient)
            logger.info("Generating embeddings...")
            chunk_embeddings = await self._generate_embeddings(texts)
            
            # Store in ChromaDB
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=chunk_embeddings.tolist()
            )
            
            logger.info(f"Successfully stored {len(chunks)} chunks for document {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Error storing document {document_id}: {str(e)}")
            raise
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search for relevant chunks.
        
        Args:
            query: Search query
            k: Number of results to return
            document_ids: Optional list of document IDs to filter by
            
        Returns:
            List of relevant chunks with metadata and scores
        """
        try:
            logger.info(f"Performing similarity search: {query[:50]}...")
            
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            
            # Prepare where clause for filtering by document IDs if provided
            where_clause = None
            if document_ids:
                where_clause = {"document_id": {"$in": document_ids}}
            
            # Perform search
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0] 
                distances = results['distances'][0]
                ids = results['ids'][0]
                
                for i, (doc, metadata, distance, chunk_id) in enumerate(zip(
                    documents, metadatas, distances, ids
                )):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity_score = 1 - distance
                    
                    formatted_results.append({
                        'id': chunk_id,
                        'text': doc,
                        'metadata': metadata,
                        'score': similarity_score,
                        'document_id': metadata.get('document_id', ''),
                        'rank': i + 1
                    })
            
            logger.info(f"Found {len(formatted_results)} relevant chunks")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a specific document.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting chunks for document {document_id}")
            
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
            else:
                logger.info(f"No chunks found for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            raise
    
    async def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            NumPy array of embeddings
        """
        try:
            # Run embedding generation in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.embedding_model.encode, 
                texts,
                {"normalize_embeddings": True}
            )
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def reset_collection(self):
        """
        Reset the entire collection (useful for testing).
        WARNING: This will delete all stored chunks!
        """
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                embedding_function=None,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            raise
