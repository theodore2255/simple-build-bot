import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class LLMService:
    """
    LLM service for generating responses using Google Gemini.
    Integrates with the RAG pipeline for context-aware responses.
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        
        # Configure Gemini API
        api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyCyjfH5GrYf0gaCv0Hb_KIYR6nPEAWrDCs"
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        logger.info(f"Initialized LLM service with model: {model_name}")
    
    async def generate_response(
        self, 
        question: str, 
        relevant_chunks: List[Dict[str, Any]],
        max_context_length: int = 4000
    ) -> str:
        """
        Generate a response using the LLM with relevant document chunks as context.
        
        Args:
            question: User's question
            relevant_chunks: List of relevant document chunks with metadata
            max_context_length: Maximum length of context to include
            
        Returns:
            Generated response string
        """
        try:
            logger.info(f"Generating response for question: {question[:100]}...")
            
            # Build context from relevant chunks
            context = self._build_context(relevant_chunks, max_context_length)
            
            # Create the prompt
            prompt = self._create_rag_prompt(question, context)
            
            # Generate response using Gemini
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._generate_with_gemini,
                prompt
            )
            
            logger.info("Successfully generated response")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def _generate_with_gemini(self, prompt: str) -> str:
        """
        Generate response using Gemini model (synchronous).
        
        Args:
            prompt: Complete prompt with context and question
            
        Returns:
            Generated response
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2000,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            if response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"Error with Gemini generation: {str(e)}")
            raise
    
    def _build_context(
        self, 
        relevant_chunks: List[Dict[str, Any]], 
        max_length: int
    ) -> str:
        """
        Build context string from relevant chunks, respecting length limits.
        
        Args:
            relevant_chunks: List of relevant chunks with metadata
            max_length: Maximum context length
            
        Returns:
            Context string
        """
        if not relevant_chunks:
            return "No relevant context found."
        
        context_parts = []
        current_length = 0
        
        for i, chunk in enumerate(relevant_chunks):
            chunk_text = chunk.get('text', '')
            metadata = chunk.get('metadata', {})
            document_name = metadata.get('document_name', 'Unknown Document')
            
            # Format chunk with metadata
            formatted_chunk = f"[Source: {document_name}]\\n{chunk_text}\\n"
            
            # Check if adding this chunk would exceed the limit
            if current_length + len(formatted_chunk) > max_length:
                if i == 0:  # Always include at least one chunk, even if it's long
                    context_parts.append(formatted_chunk[:max_length])
                break
            
            context_parts.append(formatted_chunk)
            current_length += len(formatted_chunk)
        
        return "\\n---\\n".join(context_parts)
    
    def _create_rag_prompt(self, question: str, context: str) -> str:
        """
        Create a RAG prompt with context and question.
        
        Args:
            question: User's question
            context: Relevant context from documents
            
        Returns:
            Complete prompt for the LLM
        """
        prompt = f"""You are a helpful AI assistant that answers questions based on provided document context. Please follow these guidelines:

1. Answer questions using ONLY the information provided in the context below
2. If the context doesn't contain enough information to answer the question, say so clearly
3. Quote specific parts of the documents when relevant
4. Be accurate, concise, and helpful
5. If multiple sources provide different information, acknowledge this
6. Always base your response on the provided context

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
        
        return prompt
    
    async def generate_summary(self, text: str, max_length: int = 500) -> str:
        """
        Generate a summary of the provided text.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
            
        Returns:
            Summary string
        """
        try:
            prompt = f"""Please provide a concise summary of the following text in no more than {max_length} characters:

TEXT:
{text[:4000]}  # Limit input text length

SUMMARY:"""
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._generate_with_gemini,
                prompt
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise
    
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract key terms from the provided text.
        
        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of keywords
        """
        try:
            prompt = f"""Extract the {max_keywords} most important keywords or phrases from the following text. Return them as a comma-separated list:

TEXT:
{text[:2000]}

KEYWORDS:"""
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._generate_with_gemini,
                prompt
            )
            
            # Parse the response to extract keywords
            keywords = []
            if response:
                keywords = [kw.strip() for kw in response.split(',')]
                keywords = [kw for kw in keywords if kw]  # Remove empty strings
            
            return keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
