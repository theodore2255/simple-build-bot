@echo off
REM RAG System Deployment Script for Windows
REM This script handles the deployment of the entire RAG system using Docker Compose

echo 🚀 Starting RAG System Deployment...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Check if backend .env file exists
if not exist "backend\.env" (
    echo ⚠️  Backend .env file not found. Creating from template...
    if exist "backend\.env.template" (
        copy "backend\.env.template" "backend\.env"
    ) else (
        echo Creating basic .env file...
        echo DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/rag_documents > backend\.env
        echo GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE >> backend\.env
        echo HOST=0.0.0.0 >> backend\.env
        echo PORT=8000 >> backend\.env
    )
    echo 📝 Please edit backend\.env with your configuration before proceeding.
    echo    Especially set your GEMINI_API_KEY
    pause
    exit /b 1
)

REM Build and start services
echo 🏗️  Building Docker images...
docker-compose build --no-cache

echo 🔄 Starting services...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 30 /nobreak

REM Check service health
echo 🔍 Checking service health...

REM Check Backend
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend is ready
) else (
    echo ❌ Backend is not ready, checking logs...
    docker-compose logs backend
)

REM Check Frontend
curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend is ready
) else (
    echo ❌ Frontend is not ready, checking logs...
    docker-compose logs frontend
)

echo.
echo 🎉 RAG System deployment started!
echo.
echo 📋 Service URLs:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8000
echo    API Documentation: http://localhost:8000/docs
echo    PostgreSQL: localhost:5432
echo    Redis: localhost:6379
echo.
echo 🔧 Management commands:
echo    View logs: docker-compose logs -f [service_name]
echo    Stop services: docker-compose down
echo    Restart: docker-compose restart [service_name]
echo    Update: docker-compose pull ^&^& docker-compose up -d
echo.
echo 📊 Monitor with: docker-compose ps
echo.
pause
