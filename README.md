# RAG Document Assistant

A modern, scalable Retrieval-Augmented Generation (RAG) system built with React, FastAPI, and Google Gemini AI. Upload documents, ask questions, and get intelligent answers based on your document content.

## 🚀 Features

- **Document Upload & Processing**: Support for PDF, DOCX, and TXT files
- **Intelligent Text Chunking**: Smart document segmentation for optimal retrieval
- **Vector Search**: ChromaDB-powered semantic search with sentence transformers
- **AI-Powered Responses**: Google Gemini integration for context-aware answers
- **Modern UI**: React + TypeScript frontend with drag-and-drop file upload
- **Scalable Backend**: FastAPI with PostgreSQL and Redis for production use
- **Docker Support**: Complete containerization for easy deployment
- **Development Tools**: Hot reload, type safety, and comprehensive logging

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │────│  FastAPI Backend │────│   PostgreSQL    │
│   (TypeScript)   │    │    (Python)     │    │   (Documents)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │    ChromaDB     │────│   Google Gemini │
                       │   (Vectors)     │    │   (AI Responses)│
                       └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

### For Docker Deployment (Recommended)
- Docker Desktop
- Docker Compose
- Google Gemini API Key

### For Development
- Node.js 18+
- Python 3.11+
- PostgreSQL (or Docker)
- Google Gemini API Key

## 🚀 Quick Start (Docker)

1. **Clone and setup**:
   ```bash
   git clone <your-repo-url>
   cd rag-document-assistant
   ```

2. **Configure environment**:
   ```bash
   # Windows
   deploy.bat
   
   # Linux/macOS
   ./deploy.sh
   ```

3. **Set your API key** in `backend/.env`:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

4. **Deploy**:
   ```bash
   # Windows
   deploy.bat
   
   # Linux/macOS
   ./deploy.sh
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Backend API: http://localhost:8000

## 🛠️ Development Setup

1. **Setup development environment**:
   ```bash
   # Windows
   setup-dev.bat
   
   # Linux/macOS - coming soon
   ```

2. **Configure API keys**:
   - Edit `backend/.env` and set `GEMINI_API_KEY`
   - Edit `.env.local` and set `VITE_GEMINI_API_KEY`

3. **Start services**:

   **Backend** (Terminal 1):
   ```bash
   cd backend
   # Windows
   venv\Scripts\activate.bat
   # Linux/macOS
   source venv/bin/activate
   
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

   **Frontend** (Terminal 2):
   ```bash
   npm run dev
   ```

4. **Access**:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000/docs

## 📱 Project Structure

```
rag-document-assistant/
├── src/                          # React frontend
│   ├── components/              # React components
│   ├── services/               # API services
│   └── types/                  # TypeScript types
├── backend/                     # FastAPI backend
│   ├── app/                    # Application code
│   │   ├── services/          # Business logic
│   │   ├── models.py          # Database models
│   │   └── schemas.py         # Pydantic schemas
│   ├── main.py                # FastAPI app
│   └── requirements.txt       # Python dependencies
├── docker-compose.yml          # Multi-service orchestration
├── deploy.bat                  # Windows deployment script
└── README.md                   # This file
```

## 🔧 Configuration

### Environment Variables

**Backend (`backend/.env`)**:
```env
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/rag_documents
GEMINI_API_KEY=your_gemini_api_key
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000
MAX_DOCUMENT_SIZE_MB=10
MAX_DOCUMENTS_PER_USER=20
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

**Frontend (`.env.local`)**:
```env
VITE_API_URL=http://localhost:8000
VITE_GEMINI_API_KEY=your_gemini_api_key
```

## 🔌 API Endpoints

### Documents
- `POST /documents/upload` - Upload and process documents
- `GET /documents/` - List all documents
- `DELETE /documents/{document_id}` - Delete a document
- `POST /documents/query` - Query documents with AI

### Health
- `GET /health` - Service health check

For detailed API documentation, visit http://localhost:8000/docs when running.

## 🧪 Testing & Validation

### Running Tests

The project includes comprehensive unit and integration tests:

```bash
# Navigate to backend directory
cd backend

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run unit tests for document retrieval
pytest tests/test_document_retrieval.py -v

# Run integration tests for query handling
pytest tests/test_query_integration.py -v

# Run all tests with coverage
pytest tests/ -v --cov=app
```

### Test Coverage

Our test suite covers:
- ✅ Document upload and processing
- ✅ Document retrieval and listing
- ✅ Document deletion
- ✅ Query handling and response generation
- ✅ Error handling and validation
- ✅ Database operations
- ✅ Vector store operations
- ✅ LLM service integration
- ✅ API endpoint functionality

## 🤖 LLM Provider Configuration

### Google Gemini (Default)

**Setup Instructions:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to environment variables:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

**Model Options:**
- `gemini-pro` (default) - Best for text generation
- `gemini-pro-vision` - For multimodal tasks

**Configuration:**
```python
# In app/services/llm_service.py
class LLMService:
    def __init__(self):
        self.model = "gemini-pro"
        self.temperature = 0.7
        self.max_output_tokens = 1024
```

### OpenAI GPT (Alternative)

**Setup Instructions:**
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to environment variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
# Comment out GEMINI_API_KEY to use OpenAI
```

**Model Options:**
- `gpt-3.5-turbo` - Cost-effective, fast responses
- `gpt-4` - Higher quality, more expensive
- `gpt-4-turbo` - Latest model with improved performance

**Configuration:**
```python
# In app/services/llm_service.py
class LLMService:
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.7
        self.max_tokens = 1024
```

### Switching Between Providers

The system automatically detects available API keys:
1. **Priority Order**: Gemini → OpenAI
2. **Fallback**: If primary fails, switches to secondary
3. **Error Handling**: Graceful degradation with informative messages

## 🧪 Usage Examples

### Upload a Document
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.pdf"
```

### Query Documents
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the document?", "max_results": 5}'
```

### List Documents
```bash
curl -X GET "http://localhost:8000/documents"
```

### Delete Document
```bash
curl -X DELETE "http://localhost:8000/documents/{document_id}"
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# Monitor services
docker-compose ps
```

## 🔍 Troubleshooting

### Common Issues

**Backend not starting**:
- Check if GEMINI_API_KEY is set in `backend/.env`
- Verify PostgreSQL is running and accessible
- Check logs: `docker-compose logs backend`

**Frontend not accessible**:
- Ensure backend is running on port 8000
- Check CORS configuration in backend
- Verify API URL in `.env.local`

**Document processing fails**:
- Check file size limits (default: 10MB)
- Verify file format (PDF, DOCX, TXT supported)
- Check Gemini API quota and limits

### Logs and Monitoring

```bash
# Application logs
docker-compose logs -f

# Database logs
docker-compose logs postgres

# System resources
docker stats

# Health checks
curl http://localhost:8000/health
curl http://localhost:3000
```

## 🚀 Performance Tuning

### Database Optimization
- Adjust PostgreSQL `shared_buffers` and `work_mem`
- Create indexes on frequently queried columns
- Use connection pooling for high load

### Vector Search Optimization
- Tune ChromaDB collection settings
- Adjust chunk size and overlap for your documents
- Consider different embedding models for better accuracy

### API Rate Limiting
- Configure Nginx rate limits in `nginx.conf`
- Implement Redis-based caching for frequent queries
- Use async processing for large document uploads

## 📚 Technical Details

### Technologies Used
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL, ChromaDB
- **AI**: Google Gemini Pro, Sentence Transformers
- **Infrastructure**: Docker, Nginx, Redis

### Document Processing Pipeline
1. File upload and validation
2. Text extraction (PDF/DOCX parsing)
3. Intelligent chunking with overlap
4. Embedding generation using sentence transformers
5. Vector storage in ChromaDB
6. Metadata storage in PostgreSQL

### Query Pipeline
1. User query embedding
2. Similarity search in ChromaDB
3. Context retrieval and ranking
4. Gemini API call with context
5. Response generation and formatting

## 🔮 Roadmap

- [ ] Multi-user authentication and authorization
- [ ] Advanced document search and filtering
- [ ] Real-time collaboration features
- [ ] Integration with cloud storage providers
- [ ] Advanced analytics and usage metrics
- [ ] Support for additional document formats
- [ ] Custom embedding models
- [ ] Export and backup functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
