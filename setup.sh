#!/bin/bash

# LMI Agent - Quick Setup Script
# This script helps you set up the project quickly

set -e  # Exit on error

echo "🚀 LMI Agent Setup Script"
echo "=========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
else
    print_error "Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check Git
if command -v git &> /dev/null; then
    print_success "Git found"
else
    print_error "Git not found. Please install Git"
    exit 1
fi

echo ""
echo "Setting up backend..."
echo "===================="

# Backend setup
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
print_success "Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_info "Creating .env file..."
    cp .env.example .env
    print_warning "Please update .env with your credentials:"
    print_warning "  - DATABASE_URL (Neon PostgreSQL)"
    print_warning "  - GROQ_API_KEY (from console.groq.com)"
    echo ""
    read -p "Press Enter to continue after updating .env..."
else
    print_warning ".env file already exists"
fi

# Check if DATABASE_URL is set
if grep -q "your-neon-connection-string" .env 2>/dev/null || ! grep -q "DATABASE_URL=" .env 2>/dev/null; then
    print_error "DATABASE_URL not configured in .env"
    print_info "Get your connection string from: https://neon.tech"
    read -p "Enter your DATABASE_URL: " DB_URL
    if [ ! -z "$DB_URL" ]; then
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DB_URL|g" .env
        print_success "DATABASE_URL updated"
    fi
fi

# Check if GROQ_API_KEY is set
if grep -q "your_groq_api_key" .env 2>/dev/null || ! grep -q "GROQ_API_KEY=" .env 2>/dev/null; then
    print_error "GROQ_API_KEY not configured in .env"
    print_info "Get your API key from: https://console.groq.com"
    read -p "Enter your GROQ_API_KEY: " GROQ_KEY
    if [ ! -z "$GROQ_KEY" ]; then
        sed -i "s|GROQ_API_KEY=.*|GROQ_API_KEY=$GROQ_KEY|g" .env
        print_success "GROQ_API_KEY updated"
    fi
fi

# Setup database
print_info "Setting up database..."
python scripts/setup_db.py setup
print_success "Database initialized"

# Ingest sample data
echo ""
read -p "Would you like to ingest sample job data? (y/n): " INGEST_DATA
if [ "$INGEST_DATA" = "y" ] || [ "$INGEST_DATA" = "Y" ]; then
    print_info "Fetching sample job data..."
    print_warning "This may take a few minutes..."
    python scripts/ingest_data.py api --search-terms "Machine Learning Engineer" "Data Scientist" --api-source remoteok
    print_success "Sample data ingested"
    
    # Show stats
    python scripts/ingest_data.py stats
fi

cd ..

echo ""
echo "Setting up frontend..."
echo "====================="

# Frontend setup
cd frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    print_info "Installing Node.js dependencies..."
    npm install > /dev/null 2>&1
    print_success "Dependencies installed"
else
    print_warning "node_modules already exists, skipping install"
fi

# Create .env.local file
if [ ! -f ".env.local" ]; then
    print_info "Creating .env.local file..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
    print_success ".env.local created"
else
    print_warning ".env.local already exists"
fi

cd ..

echo ""
echo "================================"
echo "✅ Setup completed successfully!"
echo "================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open your browser to:"
echo "   http://localhost:3000"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Project overview"
echo "   - DEPLOYMENT_GUIDE.md - Deployment instructions"
echo ""
echo "Need help? Check the documentation or open an issue on GitHub."
echo ""

# Ask if user wants to start servers
read -p "Would you like to start the servers now? (y/n): " START_SERVERS
if [ "$START_SERVERS" = "y" ] || [ "$START_SERVERS" = "Y" ]; then
    print_info "Starting backend server..."
    cd backend
    source venv/bin/activate
    
    # Start backend in background
    uvicorn app.main:app --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    print_success "Backend started (PID: $BACKEND_PID)"
    
    cd ..
    
    # Start frontend
    print_info "Starting frontend server..."
    cd frontend
    npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    print_success "Frontend started (PID: $FRONTEND_PID)"
    
    echo ""
    print_success "Both servers are running!"
    echo ""
    echo "Backend: http://localhost:8000"
    echo "Frontend: http://localhost:3000"
    echo ""
    echo "Logs:"
    echo "  Backend: backend/backend.log"
    echo "  Frontend: frontend/frontend.log"
    echo ""
    echo "To stop servers:"
    echo "  kill $BACKEND_PID $FRONTEND_PID"
    echo ""
    
    # Save PIDs
    echo "$BACKEND_PID" > .backend.pid
    echo "$FRONTEND_PID" > .frontend.pid
    
    print_info "Opening browser..."
    sleep 3
    
    # Try to open browser
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000
    elif command -v open &> /dev/null; then
        open http://localhost:3000
    fi
fi