#!/bin/bash
# ARGO v10.11 - Unified Start Script
# Starts backend and frontend together

set -e  # Exit on error

echo "=================================================="
echo "ARGO v10.11 - Enterprise PMO Platform"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0.32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found${NC}"
    echo "Please copy .env.example to .env and add your API keys"
    echo ""
    echo "Required environment variables:"
    echo "  - OPENAI_API_KEY (required)"
    echo "  - ANTHROPIC_API_KEY (optional)"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}ERROR: node not found${NC}"
    echo "Please install Node.js 16 or higher"
    exit 1
fi

echo -e "${YELLOW}Checking dependencies...${NC}"

# Check Python dependencies
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check Node dependencies (frontend)
if [ ! -d "frontend/client/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend/client && npm install && cd ../..
fi

echo -e "${GREEN}✓ Dependencies OK${NC}"
echo ""

# Create data directory if it doesn't exist
mkdir -p data

echo -e "${YELLOW}Starting ARGO services...${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down ARGO..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${YELLOW}[1/2] Starting Backend (FastAPI)...${NC}"
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 3

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo -e "${RED}ERROR: Backend failed to start${NC}"
    echo "Check backend/logs for details"
    exit 1
fi

echo -e "${GREEN}✓ Backend started on http://localhost:8000${NC}"
echo ""

# Start frontend
echo -e "${YELLOW}[2/2] Starting Frontend (React)...${NC}"
cd frontend/client
npm run dev &
FRONTEND_PID=$!
cd ../..

# Wait for frontend to be ready
echo "Waiting for frontend to start..."
sleep 3

# Check if frontend is running
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${RED}ERROR: Frontend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✓ Frontend started on http://localhost:5173${NC}"
echo ""

echo "=================================================="
echo -e "${GREEN}✓ ARGO is running!${NC}"
echo "=================================================="
echo ""
echo "Backend API:  http://localhost:8000"
echo "Frontend UI:  http://localhost:5173"
echo "API Docs:     http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
