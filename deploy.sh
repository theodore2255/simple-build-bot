#!/bin/bash

# RAG System Deployment Script
# This script handles the deployment of the entire RAG system using Docker Compose

set -e  # Exit on any error

echo "🚀 Starting RAG System Deployment..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Backend .env file not found. Creating from template..."
    cp backend/.env.template backend/.env
    echo "📝 Please edit backend/.env with your configuration before proceeding."
    echo "   Especially set your GEMINI_API_KEY"
    exit 1
fi

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose build --no-cache

echo "🔄 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec postgres pg_isready -U rag_user -d rag_documents; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
    docker-compose logs postgres
    exit 1
fi

# Check Backend
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend is ready"
else
    echo "❌ Backend is not ready"
    docker-compose logs backend
    exit 1
fi

# Check Frontend
if curl -f http://localhost:3000 &> /dev/null; then
    echo "✅ Frontend is ready"
else
    echo "❌ Frontend is not ready"
    docker-compose logs frontend
    exit 1
fi

echo "🎉 RAG System deployed successfully!"
echo ""
echo "📋 Service URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "🔧 Management commands:"
echo "   View logs: docker-compose logs -f [service_name]"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart [service_name]"
echo "   Update: docker-compose pull && docker-compose up -d"
echo ""
echo "📊 Monitor with: docker-compose ps"
