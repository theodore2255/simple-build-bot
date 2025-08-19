@echo off
REM Development Environment Setup Script
REM This script sets up the development environment for the RAG system

echo 🔧 Setting up RAG System Development Environment...

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    exit /b 1
) else (
    echo ✅ Node.js is installed
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.11+ first.
    exit /b 1
) else (
    echo ✅ Python is installed
)

REM Setup Frontend
echo 📦 Installing frontend dependencies...
npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install frontend dependencies
    exit /b 1
)

REM Setup Backend
echo 🐍 Setting up backend environment...
cd backend

REM Create virtual environment
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
echo Installing backend dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

REM Setup environment files
if not exist ".env" (
    echo Creating backend .env file...
    echo DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/rag_documents > .env
    echo GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE >> .env
    echo HOST=127.0.0.1 >> .env
    echo PORT=8000 >> .env
    echo CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000 >> .env
    echo MAX_DOCUMENT_SIZE_MB=10 >> .env
    echo MAX_DOCUMENTS_PER_USER=20 >> .env
    echo MAX_PAGES_PER_DOCUMENT=1000 >> .env
    echo CHUNK_SIZE=1000 >> .env
    echo CHUNK_OVERLAP=200 >> .env
    echo EMBEDDING_MODEL=all-MiniLM-L6-v2 >> .env
    echo CHROMA_PERSIST_DIRECTORY=./chroma_db >> .env
    echo.
    echo 📝 Please edit backend\.env and set your GEMINI_API_KEY
)

deactivate
cd ..

REM Setup frontend environment
if not exist ".env.local" (
    echo Creating frontend .env.local file...
    echo VITE_API_URL=http://localhost:8000 > .env.local
    echo VITE_GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE >> .env.local
    echo.
    echo 📝 Please edit .env.local and set your VITE_GEMINI_API_KEY
)

echo.
echo 🎉 Development environment setup complete!
echo.
echo 🚀 To start development:
echo.
echo Frontend:
echo   npm run dev
echo.
echo Backend:
echo   cd backend
echo   venv\Scripts\activate.bat
echo   uvicorn main:app --reload --host 127.0.0.1 --port 8000
echo.
echo 📝 Don't forget to:
echo   1. Set your GEMINI_API_KEY in backend\.env
echo   2. Set your VITE_GEMINI_API_KEY in .env.local
echo   3. Start a PostgreSQL database or use Docker
echo.
pause
