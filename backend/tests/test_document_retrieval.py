import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from io import BytesIO

from app.database import Base, get_db
from app.models import Document
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreService
from main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestDocumentRetrieval:
    """Test class for document retrieval functionality"""
    
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
    def sample_pdf_file(self):
        """Create a sample PDF file for testing"""
        content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        return BytesIO(content)
    
    @pytest.fixture
    def sample_text_file(self):
        """Create a sample text file for testing"""
        content = "This is a test document with sample content for RAG processing."
        return BytesIO(content.encode())
    
    def test_document_upload_success(self, client, sample_text_file):
        """Test successful document upload"""
        with patch('app.services.document_processor.DocumentProcessor.process_document') as mock_process, \
             patch('app.services.vector_store.VectorStoreService.store_document') as mock_store:
            
            mock_process.return_value = AsyncMock(return_value=[
                {"content": "Test content chunk 1", "metadata": {"page": 1}},
                {"content": "Test content chunk 2", "metadata": {"page": 1}}
            ])
            mock_store.return_value = AsyncMock(return_value="test-doc-id")
            
            response = client.post(
                "/documents/upload",
                files={"file": ("test.txt", sample_text_file, "text/plain")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == "test.txt"
            assert data["status"] == "processed"
            assert data["chunk_count"] == 2
    
    def test_document_upload_unsupported_type(self, client):
        """Test upload with unsupported file type"""
        fake_file = BytesIO(b"fake content")
        
        response = client.post(
            "/documents/upload",
            files={"file": ("test.xyz", fake_file, "application/xyz")}
        )
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    def test_document_upload_limit_exceeded(self, client, sample_text_file):
        """Test document upload when limit is exceeded"""
        db = next(override_get_db())
        
        # Add 20 dummy documents to exceed limit
        for i in range(20):
            doc = Document(
                id=f"test-doc-{i}",
                filename=f"test{i}.txt",
                file_path=f"/tmp/test{i}.txt",
                file_size=100,
                content_type="text/plain",
                chunk_count=1,
                status="processed"
            )
            db.add(doc)
        db.commit()
        db.close()
        
        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", sample_text_file, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Maximum document limit (20) reached" in response.json()["detail"]
    
    def test_list_documents(self, client):
        """Test listing all documents"""
        db = next(override_get_db())
        
        # Add test documents
        doc1 = Document(
            id="doc1",
            filename="test1.txt",
            file_path="/tmp/test1.txt",
            file_size=100,
            content_type="text/plain",
            chunk_count=1,
            status="processed"
        )
        doc2 = Document(
            id="doc2",
            filename="test2.txt",
            file_path="/tmp/test2.txt",
            file_size=200,
            content_type="text/plain",
            chunk_count=2,
            status="processed"
        )
        
        db.add(doc1)
        db.add(doc2)
        db.commit()
        db.close()
        
        response = client.get("/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["filename"] == "test1.txt"
        assert data[1]["filename"] == "test2.txt"
    
    def test_delete_document_success(self, client):
        """Test successful document deletion"""
        db = next(override_get_db())
        
        # Add test document
        doc = Document(
            id="test-doc-delete",
            filename="delete_test.txt",
            file_path="/tmp/delete_test.txt",
            file_size=100,
            content_type="text/plain",
            chunk_count=1,
            status="processed"
        )
        db.add(doc)
        db.commit()
        db.close()
        
        with patch('app.services.vector_store.VectorStoreService.delete_document') as mock_delete, \
             patch('os.path.exists') as mock_exists, \
             patch('os.remove') as mock_remove:
            
            mock_delete.return_value = AsyncMock()
            mock_exists.return_value = True
            
            response = client.delete("/documents/test-doc-delete")
            
            assert response.status_code == 200
            assert "deleted successfully" in response.json()["message"]
            mock_delete.assert_called_once_with("test-doc-delete")
            mock_remove.assert_called_once_with("/tmp/delete_test.txt")
    
    def test_delete_document_not_found(self, client):
        """Test deletion of non-existent document"""
        response = client.delete("/documents/non-existent-doc")
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_document_processor_process_document(self):
        """Test document processor functionality"""
        processor = DocumentProcessor()
        
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("This is a test document.\nIt has multiple lines.\nFor testing purposes.")
            temp_file_path = temp_file.name
        
        try:
            chunks = await processor.process_document(temp_file_path, "test.txt")
            
            assert isinstance(chunks, list)
            assert len(chunks) > 0
            assert all("content" in chunk for chunk in chunks)
            assert all("metadata" in chunk for chunk in chunks)
            
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_vector_store_operations(self):
        """Test vector store operations"""
        vector_store = VectorStoreService()
        
        # Mock chunks for testing
        test_chunks = [
            {"content": "This is test content 1", "metadata": {"page": 1}},
            {"content": "This is test content 2", "metadata": {"page": 2}}
        ]
        
        with patch.object(vector_store, 'store_document') as mock_store, \
             patch.object(vector_store, 'similarity_search') as mock_search, \
             patch.object(vector_store, 'delete_document') as mock_delete:
            
            # Test store_document
            mock_store.return_value = AsyncMock(return_value="test-doc-id")
            doc_id = await vector_store.store_document("test-doc", test_chunks)
            assert doc_id == "test-doc-id"
            mock_store.assert_called_once_with("test-doc", test_chunks)
            
            # Test similarity_search
            mock_search.return_value = AsyncMock(return_value=[
                {"content": "relevant content", "score": 0.9, "document_id": "test-doc"}
            ])
            results = await vector_store.similarity_search("test query", k=5)
            assert len(results) == 1
            assert results[0]["score"] == 0.9
            
            # Test delete_document
            mock_delete.return_value = AsyncMock()
            await vector_store.delete_document("test-doc")
            mock_delete.assert_called_once_with("test-doc")

if __name__ == "__main__":
    pytest.main([__file__])
