# LMI Agent - Labor Market Intelligence Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)

> An AI-powered Retrieval-Augmented Generation (RAG) system that provides real-time labor market intelligence and skill gap analysis based on actual job postings.

## 🎯 Project Overview

The LMI Agent is a production-ready, zero-cost MLOps project that demonstrates advanced technical skills in:

- **RAG Architecture**: Advanced retrieval with pgvector and semantic search
- **Generative AI**: Skill analysis using Groq's fast LLM inference
- **Full-Stack Development**: FastAPI backend + Next.js frontend
- **MLOps/GenAIOps**: Automated CI/CD pipeline with GitHub Actions
- **Zero-Cost Deployment**: Strategic use of free-tier services

### Key Features

✅ **Real-time Job Market Analysis** - Analyze current job requirements and trends  
✅ **Skill Gap Identification** - Identify mandatory vs. desired skills with necessity scores  
✅ **Actionable Recommendations** - Get personalized career development advice  
✅ **Citation & Transparency** - Every insight backed by real job postings  
✅ **Emerging Trends Detection** - Identify up-and-coming skills in your field  

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Next.js UI    │────────▶│  FastAPI Backend │────────▶│ Neon PostgreSQL │
│   (Vercel)      │         │   (Railway)      │         │   + pgvector    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │   Groq API       │
                            │  (LLM Inference) │
                            └──────────────────┘
```

### Tech Stack

**Backend:**
- FastAPI (Python 3.11)
- SQLAlchemy + pgvector
- Sentence Transformers (embeddings)
- Groq API (LLM inference)
- Scrapy (data collection)

**Frontend:**
- Next.js 14 (React)
- TypeScript
- Tailwind CSS
- Recharts (visualization)

**Infrastructure:**
- Neon (PostgreSQL + pgvector)
- Railway (backend hosting)
- Vercel (frontend hosting)
- GitHub Actions (CI/CD)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL with pgvector (or Neon account)
- Groq API key ([Get one free](https://console.groq.com))

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/lmi-agent.git
cd lmi-agent
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOL
DATABASE_URL=postgresql://user:password@host:5432/dbname
GROQ_API_KEY=your_groq_api_key_here
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EOL

# Initialize database
python scripts/setup_db.py setup

# Ingest sample data (using RemoteOK API)
python scripts/ingest_data.py api --search-terms "Machine Learning Engineer" "Data Scientist"

# Run the server
uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
cat > .env.local << EOL
NEXT_PUBLIC_API_URL=http://localhost:8000
EOL

# Run development server
npm run dev
```

Visit `http://localhost:3000` to see the application!

## 📊 Data Ingestion

### Using Public APIs (Recommended)

```bash
# RemoteOK API (no API key required)
python scripts/ingest_data.py api --api-source remoteok --search-terms "MLOps Engineer"

# Adzuna API (requires free API key)
export ADZUNA_APP_ID=your_app_id
export ADZUNA_APP_KEY=your_app_key
python scripts/ingest_data.py api --api-source adzuna --search-terms "Data Scientist"
```

### From JSON File

```bash
python scripts/ingest_data.py json --file path/to/jobs.json
```

### Update Embeddings

```bash
python scripts/ingest_data.py update-embeddings
```

### View Statistics

```bash
python scripts/ingest_data.py stats
```

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```env
# Required
DATABASE_URL=postgresql://user:pass@host/db
GROQ_API_KEY=gsk_xxx

# Optional
GROQ_MODEL=mixtral-8x7b-32768
GROQ_TEMPERATURE=0.3
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=512
CHUNK_OVERLAP=100
RETRIEVAL_TOP_K=5
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

## 🚢 Deployment

### Backend Deployment (Railway)

1. Create a Railway account at [railway.app](https://railway.app)
2. Create a new project
3. Connect your GitHub repository
4. Add environment variables
5. Deploy automatically on push to main

### Frontend Deployment (Vercel)

1. Create a Vercel account at [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Select `frontend` as the root directory
4. Add environment variables
5. Deploy automatically on push to main

### Database Setup (Neon)

1. Create account at [neon.tech](https://neon.tech)
2. Create a new project
3. Enable pgvector extension in SQL editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Copy connection string to `DATABASE_URL`

## 📈 API Documentation

### Analyze Skills
```http
POST /api/v1/analyze
Content-Type: application/json

{
  "query": "Machine Learning Engineer",
  "job_role": "Senior ML Engineer",
  "location": "Remote",
  "use_cache": true
}
```

### Compare Roles
```http
POST /api/v1/compare
Content-Type: application/json

{
  "role_a": "Data Scientist",
  "role_b": "ML Engineer",
  "location": "US"
}
```

### Get Trending Skills
```http
GET /api/v1/trending?category=all&days=30
```

### Search Jobs
```http
GET /api/v1/jobs/search?query=python&location=remote&limit=10
```

### Get Statistics
```http
GET /api/v1/stats
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test
```

## 📊 Performance Optimization

### Caching Strategy
- Analysis results cached for 24 hours
- Reduces LLM API calls and costs
- Automatic cache invalidation

### Vector Search Optimization
- HNSW indexing for fast similarity search
- Optimized chunk size (512 tokens)
- Metadata filtering for precise retrieval

### Async Processing
- Non-blocking LLM inference
- Batch embedding generation
- Rate limiting compliance

## 🔐 Security & Ethics

### Web Scraping Ethics
- Respects robots.txt
- Rate limiting (2 sec delay)
- Proper user agent identification
- Prefers official APIs over scraping

### Data Privacy
- No personal data collected
- Public job postings only
- Transparent data sources
- Citation of all sources

## 📝 Documentation

- [Technical Retrospective](docs/TECHNICAL_RETROSPECTIVE.md) - Deep dive into technical decisions
- [Decision Log](docs/DECISION_LOG.md) - Architectural decision records
- [API Reference](docs/API.md) - Complete API documentation

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.


## 🙏 Acknowledgments

- Groq for fast LLM inference
- Neon for PostgreSQL hosting
- Railway for backend deployment
- Vercel for frontend hosting
- RemoteOK for job data API

## 📧 Contact

**Your Name**  
- LinkedIn: [your-profile](https://linkedin.com/in/your-profile)
- Email: your.email@example.com
- Portfolio: [your-website.com](https://your-website.com)

---

⭐ **Star this repo if you find it useful!**

Built with ❤️ as a portfolio project showcasing RAG, MLOps, and Full-Stack AI development.