import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from io import BytesIO

from app.database import Base, get_db
from app.models import Document
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStoreService
from main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestQueryIntegration:
    """Integration tests for query handling functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup test database before each test"""
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents in the database"""
        db = next(override_get_db())
        
        doc1 = Document(
            id="doc1",
            filename="artificial_intelligence.txt",
            file_path="/tmp/ai.txt",
            file_size=1500,
            content_type="text/plain",
            chunk_count=5,
            status="processed"
        )
        
        doc2 = Document(
            id="doc2",
            filename="machine_learning.pdf",
            file_path="/tmp/ml.pdf",
            file_size=2500,
            content_type="application/pdf",
            chunk_count=8,
            status="processed"
        )
        
        db.add(doc1)
        db.add(doc2)
        db.commit()
        
        yield [doc1, doc2]
        
        db.close()
    
    def test_query_with_relevant_results(self, client, sample_documents):
        """Test query processing with relevant document chunks"""
        mock_chunks = [
            {
                "content": "Artificial Intelligence (AI) is the simulation of human intelligence processes by machines.",
                "score": 0.95,
                "document_id": "doc1",
                "id": "chunk1"
            },
            {
                "content": "Machine learning is a subset of AI that focuses on algorithms and statistical models.",
                "score": 0.88,
                "document_id": "doc2", 
                "id": "chunk2"
            }
        ]
        
        mock_response = "Based on the documents, Artificial Intelligence (AI) refers to the simulation of human intelligence processes by machines, while machine learning is a specific subset of AI that focuses on algorithms and statistical models."
        
        with patch('app.services.vector_store.VectorStoreService.similarity_search') as mock_search, \
             patch('app.services.llm_service.LLMService.generate_response') as mock_llm:
            
            mock_search.return_value = AsyncMock(return_value=mock_chunks)
            mock_llm.return_value = AsyncMock(return_value=mock_response)
            
            query_data = {
                "question": "What is artificial intelligence?",
                "max_results": 5
            }
            
            response = client.post("/query", json=query_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["question"] == "What is artificial intelligence?"
            assert data["answer"] == mock_response
            assert len(data["sources"]) == 2
            assert data["sources"][0]["document_name"] == "artificial_intelligence.txt"
            assert data["sources"][1]["document_name"] == "machine_learning.pdf"
            assert data["confidence"] == 0.95  # Max score from chunks
    
    def test_query_no_relevant_results(self, client, sample_documents):
        """Test query processing when no relevant chunks are found"""
        with patch('app.services.vector_store.VectorStoreService.similarity_search') as mock_search:
            mock_search.return_value = AsyncMock(return_value=[])
            
            query_data = {
                "question": "What is quantum computing?",
                "max_results": 5
            }
            
            response = client.post("/query", json=query_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["question"] == "What is quantum computing?"
            assert "couldn't find any relevant information" in data["answer"]
            assert data["sources"] == []
            assert data["confidence"] == 0.0
    
    def test_query_no_processed_documents(self, client):
        """Test query when no processed documents are available"""
        query_data = {
            "question": "What is artificial intelligence?",
            "max_results": 5
        }
        
        response = client.post("/query", json=query_data)
        
        assert response.status_code == 400
        assert "No processed documents available for querying" in response.json()["detail"]
    
    def test_query_invalid_request_format(self, client, sample_documents):
        """Test query with invalid request format"""
        # Missing required 'question' field
        query_data = {
            "max_results": 5
        }
        
        response = client.post("/query", json=query_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_query_with_custom_max_results(self, client, sample_documents):
        """Test query with custom max_results parameter"""
        mock_chunks = [
            {"content": f"Content chunk {i}", "score": 0.9 - (i * 0.1), "document_id": "doc1", "id": f"chunk{i}"}
            for i in range(10)
        ]
        
        with patch('app.services.vector_store.VectorStoreService.similarity_search') as mock_search, \
             patch('app.services.llm_service.LLMService.generate_response') as mock_llm:
            
            mock_search.return_value = AsyncMock(return_value=mock_chunks)
            mock_llm.return_value = AsyncMock(return_value="Test response")
            
            query_data = {
                "question": "Test question",
                "max_results": 3
            }
            
            response = client.post("/query", json=query_data)
            
            assert response.status_code == 200
            
            # Verify similarity_search was called with correct k parameter
            mock_search.assert_called_once_with("Test question", k=3)
    
    def test_query_sources_limitation(self, client, sample_documents):
        """Test that sources are limited to top 5 even with more chunks"""
        # Create 10 mock chunks but expect only 5 sources in response
        mock_chunks = [
            {"content": f"Content {i}", "score": 0.9 - (i * 0.05), "document_id": "doc1", "id": f"chunk{i}"}
            for i in range(10)
        ]
        
        with patch('app.services.vector_store.VectorStoreService.similarity_search') as mock_search, \
             patch('app.services.llm_service.LLMService.generate_response') as mock_llm:
            
            mock_search.return_value = AsyncMock(return_value=mock_chunks)
            mock_llm.return_value = AsyncMock(return_value="Test response")
            
            query_data = {
                "question": "Test question with many results",
                "max_results": 10
            }
            
            response = client.post("/query", json=query_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have maximum 5 sources despite 10 chunks
            assert len(data["sources"]) == 5
    
    @pytest.mark.asyncio
    async def test_llm_service_integration(self):
        """Test LLM service integration"""
        llm_service = LLMService()
        
        test_chunks = [
            {"content": "Python is a programming language.", "metadata": {"source": "doc1"}},
            {"content": "It's widely used for data science and web development.", "metadata": {"source": "doc2"}}
        ]
        
        with patch.object(llm_service, 'generate_response') as mock_generate:
            mock_generate.return_value = AsyncMock(return_value="Python is a versatile programming language used in many domains.")
            
            response = await llm_service.generate_response("What is Python?", test_chunks)
            
            assert isinstance(response, str)
            assert "Python" in response
            mock_generate.assert_called_once_with("What is Python?", test_chunks)
    
    @pytest.mark.asyncio 
    async def test_vector_store_similarity_search_integration(self):
        """Test vector store similarity search integration"""
        vector_store = VectorStoreService()
        
        with patch.object(vector_store, 'similarity_search') as mock_search:
            mock_search.return_value = AsyncMock(return_value=[
                {"content": "Relevant content", "score": 0.85, "document_id": "test-doc"}
            ])
            
            results = await vector_store.similarity_search("test query", k=5)
            
            assert len(results) == 1
            assert results[0]["score"] == 0.85
            assert results[0]["document_id"] == "test-doc"
            mock_search.assert_called_once_with("test query", k=5)
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "RAG Document Processing API"
        assert data["version"] == "1.0.0"
    
    def test_query_error_handling(self, client, sample_documents):
        """Test error handling in query endpoint"""
        with patch('app.services.vector_store.VectorStoreService.similarity_search') as mock_search:
            # Simulate an error in vector store
            mock_search.side_effect = Exception("Vector store error")
            
            query_data = {
                "question": "What is AI?",
                "max_results": 5
            }
            
            response = client.post("/query", json=query_data)
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__])
