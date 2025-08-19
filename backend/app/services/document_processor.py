import os
import asyncio
from typing import List, Dict, Any
import logging
from pathlib import Path

# Document processing imports
import PyPDF2
import docx
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Document processor that handles text extraction and chunking.
    Supports PDF, DOCX, and TXT files with intelligent chunking.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.supported_extensions = {'.pdf', '.docx', '.txt'}
        
    async def process_document(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """
        Process a document and return chunks with metadata.
        
        Args:
            file_path: Path to the document file
            filename: Original filename
            
        Returns:
            List of chunks with metadata
        """
        try:
            logger.info(f"Processing document: {filename}")
            
            # Extract text based on file type
            file_extension = Path(filename).suffix.lower()
            
            if file_extension == '.pdf':
                text = await self._extract_pdf_text(file_path)
            elif file_extension == '.docx':
                text = await self._extract_docx_text(file_path)
            elif file_extension == '.txt':
                text = await self._extract_txt_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            if not text or len(text.strip()) == 0:
                raise ValueError("No text content extracted from document")
            
            # Validate document size (approximate page limit)
            estimated_pages = len(text) // 2500  # Assuming ~2500 chars per page
            if estimated_pages > 1000:
                raise ValueError(f"Document too large: estimated {estimated_pages} pages (max 1000)")
            
            # Create chunks
            chunks = self._create_chunks(text, filename)
            
            logger.info(f"Created {len(chunks)} chunks from {filename}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            raise
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check page count
                if len(pdf_reader.pages) > 1000:
                    raise ValueError(f"PDF has {len(pdf_reader.pages)} pages (max 1000 allowed)")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\\n[Page {page_num + 1}]\\n{page_text}\\n"
                
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise
    
    async def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            raise
    
    async def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read().strip()
                
        except Exception as e:
            logger.error(f"Error extracting TXT text: {str(e)}")
            raise
    
    def _create_chunks(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """
        Create overlapping chunks from text.
        
        Args:
            text: Full document text
            filename: Document filename
            
        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = []
        sentences = text.split('.')
        current_chunk = ""
        current_position = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) + 1 > self.chunk_size and current_chunk:
                # Create chunk
                chunk_data = {
                    'id': f"{filename}_{chunk_index}",
                    'text': current_chunk.strip(),
                    'metadata': {
                        'document_name': filename,
                        'chunk_index': chunk_index,
                        'start_char': current_position - len(current_chunk),
                        'end_char': current_position,
                        'chunk_size': len(current_chunk)
                    }
                }
                chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                current_chunk = overlap_text + " " + sentence + "."
                chunk_index += 1
            else:
                current_chunk += " " + sentence + "."
            
            current_position += len(sentence) + 1
        
        # Add final chunk if it has content
        if current_chunk.strip():
            chunk_data = {
                'id': f"{filename}_{chunk_index}",
                'text': current_chunk.strip(),
                'metadata': {
                    'document_name': filename,
                    'chunk_index': chunk_index,
                    'start_char': current_position - len(current_chunk),
                    'end_char': current_position,
                    'chunk_size': len(current_chunk)
                }
            }
            chunks.append(chunk_data)
        
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get the last overlap_size characters of text for chunk overlap."""
        if len(text) <= overlap_size:
            return text
        
        # Try to break at sentence boundary
        overlap_text = text[-overlap_size:]
        last_period = overlap_text.rfind('.')
        
        if last_period > overlap_size // 2:
            return overlap_text[last_period + 1:].strip()
        else:
            return overlap_text.strip()
