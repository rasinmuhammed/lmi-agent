#!/bin/bash
# One-command startup script for LMI Agent

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    LMI Agent Startup                      ║"
echo "║          Labor Market Intelligence Platform               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    echo "   Current: $(pwd)"
    echo "   Expected: /path/to/lmi-agent/"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python $(python3 --version | cut -d' ' -f2)"

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Node.js $(node --version)"

# Check if backend is already running
if check_port 8000; then
    echo -e "${YELLOW}⚠️  Backend already running on port 8000${NC}"
    read -p "Kill existing backend? (y/n): " KILL_BACKEND
    if [ "$KILL_BACKEND" = "y" ]; then
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Stopped existing backend"
    fi
fi

# Check if frontend is already running
if check_port 3000; then
    echo -e "${YELLOW}⚠️  Frontend already running on port 3000${NC}"
    read -p "Kill existing frontend? (y/n): " KILL_FRONTEND
    if [ "$KILL_FRONTEND" = "y" ]; then
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Stopped existing frontend"
    fi
fi

# Check backend setup
echo ""
echo "Checking backend setup..."

if [ ! -f "backend/.env" ]; then
    echo -e "${RED}❌ backend/.env not found${NC}"
    echo "   Creating from template..."
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}⚠️  Please edit backend/.env with your API keys:${NC}"
    echo "   - HUGGINGFACE_API_KEY (https://huggingface.co/settings/tokens)"
    echo "   - GROQ_API_KEY (https://console.groq.com)"
    echo "   - DATABASE_URL (https://neon.tech)"
    read -p "Press Enter after updating .env..."
fi

if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "   Creating..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    cd ..
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi

# Run quick health check
echo ""
echo "Running health checks..."
cd backend
source venv/bin/activate
python scripts/troubleshoot.py --quick
HEALTH_STATUS=$?
cd ..

if [ $HEALTH_STATUS -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Health checks failed!${NC}"
    echo "   Run for detailed diagnosis:"
    echo "   cd backend && python scripts/troubleshoot.py"
    exit 1
fi

# Check frontend setup
echo ""
echo "Checking frontend setup..."

if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Node modules not found${NC}"
    echo "   Installing..."
    cd frontend
    npm install > /dev/null 2>&1
    cd ..
    echo -e "${GREEN}✓${NC} Node modules installed"
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "   Creating .env.local..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local
    echo -e "${GREEN}✓${NC} Frontend environment configured"
fi

# Start backend
echo ""
echo -e "${GREEN}Starting backend server...${NC}"
cd backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
cd ..

echo "   Backend PID: $BACKEND_PID"
echo "   Logs: backend.log"

# Wait for backend to be ready
echo "   Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend failed to start${NC}"
        echo "   Check logs: tail -f backend.log"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
done

# Start frontend
echo ""
echo -e "${GREEN}Starting frontend server...${NC}"
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
cd ..

echo "   Frontend PID: $FRONTEND_PID"
echo "   Logs: frontend.log"

# Wait for frontend to be ready
echo "   Waiting for frontend to start..."
sleep 3

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   🎉 SUCCESS! 🎉                          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Your LMI Agent is now running!"
echo ""
echo "📱 Frontend:  http://localhost:3000"
echo "🔧 Backend:   http://localhost:8000"
echo "📖 API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop servers:"
echo "   ./stop.sh"
echo "   or manually: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Try to open browser
if command -v open &> /dev/null; then
    echo "Opening browser..."
    sleep 2
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    echo "Opening browser..."
    sleep 2
    xdg-open http://localhost:3000
fi

echo "Press Ctrl+C to view logs (servers will keep running)"
echo ""

# Show live logs (can be interrupted)
tail -f backend.log frontend.log 2>/dev/null || true