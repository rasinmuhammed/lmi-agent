# 🚀 Quick Start - LMI Agent

Get your Labor Market Intelligence Agent running in under 5 minutes!

## Prerequisites

You'll need:
- Python 3.11+
- Node.js 18+
- A Groq API key (free): [console.groq.com](https://console.groq.com)
- A Neon database (free): [neon.tech](https://neon.tech)

## Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/lmi-agent.git
cd lmi-agent

# Make setup script executable
chmod +x setup.sh

# Run automated setup
./setup.sh
```

The script will:
- ✅ Install all dependencies
- ✅ Create configuration files
- ✅ Initialize the database
- ✅ Ingest sample job data
- ✅ Start both servers

## Option 2: Manual Setup

### Step 1: Get API Keys

**Groq API (LLM):**
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Create API key
4. Copy the key (starts with `gsk_`)

**Neon Database:**
1. Go to [neon.tech](https://neon.tech)
2. Sign up (free)
3. Create new project
4. In SQL Editor, run: `CREATE EXTENSION IF NOT EXISTS vector;`
5. Copy connection string from dashboard

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOL
DATABASE_URL=postgresql://your-connection-string
GROQ_API_KEY=gsk_your_api_key_here
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EOL

# Initialize database
python scripts/setup_db.py setup

# Ingest sample data (takes 2-3 minutes)
python scripts/ingest_data.py api \
  --search-terms "Machine Learning Engineer" \
  --api-source remoteok

# Start server
uvicorn app.main:app --reload
```

✅ Backend running at: http://localhost:8000

### Step 3: Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

✅ Frontend running at: http://localhost:3000

### Step 4: Test It Out

1. Open http://localhost:3000
2. Search for "Machine Learning Engineer"
3. View the skill analysis!

## 🧪 Verify Installation

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# Get statistics
curl http://localhost:8000/api/v1/stats

# Test analysis
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"Data Scientist"}'
```

### Test Frontend

Visit: http://localhost:3000
- Should see the landing page
- Search form should be functional
- Results should display with charts

## 📊 Sample Data

The setup includes sample data from RemoteOK API:
- ~20-50 job postings
- Focus on ML/AI roles
- Real-time market data

**Add more data:**
```bash
cd backend
source venv/bin/activate

# Add specific roles
python scripts/ingest_data.py api \
  --search-terms "MLOps Engineer" "AI Engineer" \
  --api-source remoteok

# Check what you have
python scripts/ingest_data.py stats
```

## 🎯 Quick Features Tour

### 1. Skill Analysis
Search: "Machine Learning Engineer"
- See top required skills
- View skill frequency
- Get necessity ratings (mandatory/desired)

### 2. Emerging Trends
- Identifies trending technologies
- Shows market shifts
- Highlights growing skills

### 3. Actionable Recommendations
- Personalized learning paths
- Priority skill suggestions
- Career development advice

### 4. Citations & Transparency
- Every insight linked to source
- View original job postings
- Verify analysis data

## 🔧 Common Issues

### Backend won't start

**Error: "Connection refused"**
```bash
# Check DATABASE_URL is correct
echo $DATABASE_URL  # or check .env

# Test database connection
python -c "from app.database import engine; engine.connect()"
```

**Error: "Module not found"**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend won't connect

**Error: "Network Error"**
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify .env.local has correct URL
cat .env.local
```

### No job data

```bash
# Manually ingest data
cd backend
source venv/bin/activate
python scripts/ingest_data.py api --search-terms "Data Scientist"

# Verify ingestion
python scripts/ingest_data.py stats
```

## 🌐 Deploy to Production

Ready to deploy? See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for:
- Railway backend deployment
- Vercel frontend deployment
- Automated CI/CD setup
- Monitoring configuration

**Quick deploy:**
1. Push to GitHub
2. Connect Railway (backend)
3. Connect Vercel (frontend)
4. Add environment variables
5. Done! ✅

## 📚 Learn More

- **README.md** - Full project documentation
- **DEPLOYMENT_GUIDE.md** - Production deployment
- **docs/TECHNICAL_RETROSPECTIVE.md** - Technical deep dive
- **docs/DECISION_LOG.md** - Architecture decisions

## 💡 Pro Tips

1. **Use cache for faster results:**
   - Analysis results cached for 24 hours
   - Reduces API calls and costs

2. **Batch your data ingestion:**
   - Ingest multiple search terms at once
   - Better for embedding generation

3. **Monitor your free tier limits:**
   - Groq: 14,400 requests/day
   - Neon: 512 MB storage
   - Railway: $5 credit/month

4. **Schedule data updates:**
   - Use GitHub Actions for automation
   - Daily updates keep data fresh

## 🎉 What's Next?

1. **Customize search terms** - Add roles relevant to you
2. **Explore the API** - Build custom integrations
3. **Deploy to production** - Share with the world
4. **Add features** - Salary analysis, geographic trends
5. **Share on LinkedIn** - Showcase your project

## 🆘 Need Help?

- **Issues?** Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) troubleshooting
- **Questions?** Open a GitHub issue
- **Improvements?** Submit a pull request

---

**Happy analyzing!** 📊 

If this project helps you, please ⭐ star the repository!