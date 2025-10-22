# Deployment Guide - LMI Agent

This guide walks you through deploying the LMI Agent on zero-cost infrastructure.

## 📋 Prerequisites

Before deployment, ensure you have:

- [ ] GitHub account
- [ ] Groq API key (free at [console.groq.com](https://console.groq.com))
- [ ] Neon PostgreSQL account (free at [neon.tech](https://neon.tech))
- [ ] Railway account (free at [railway.app](https://railway.app))
- [ ] Vercel account (free at [vercel.com](https://vercel.com))

## 🗄️ Step 1: Setup Database (Neon)

### 1.1 Create Neon Project

1. Go to [neon.tech](https://neon.tech) and sign up
2. Click "Create Project"
3. Choose:
   - **Region**: Closest to your users
   - **Postgres Version**: 15 or 16
   - **Project Name**: `lmi-agent-db`

### 1.2 Enable pgvector Extension

1. In your Neon dashboard, go to **SQL Editor**
2. Run the following SQL:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 1.3 Get Connection String

1. In Neon dashboard, click **Connection Details**
2. Copy the connection string (format: `postgresql://user:pass@host/db`)
3. Save this for later use

**Example:**
```
postgresql://username:password@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb
```

## 🚂 Step 2: Deploy Backend (Railway)

### 2.1 Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Choose "Deploy from GitHub repo"
4. Connect your GitHub account and select your repository

### 2.2 Configure Root Directory

1. In Railway project settings:
   - Click on the service
   - Go to **Settings** tab
   - Set **Root Directory**: `backend`
   - Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 2.3 Add Environment Variables

In Railway, go to **Variables** tab and add:

```env
DATABASE_URL=postgresql://your-neon-connection-string
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=mixtral-8x7b-32768
GROQ_TEMPERATURE=0.3
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=512
CHUNK_OVERLAP=100
RETRIEVAL_TOP_K=5
```

### 2.4 Deploy

1. Railway will automatically deploy on push to main branch
2. Wait for deployment to complete (5-10 minutes first time)
3. Once deployed, you'll get a public URL like: `https://your-app.railway.app`
4. Test the health endpoint: `https://your-app.railway.app/health`

### 2.5 Initialize Database

Use Railway's CLI or run locally with production DATABASE_URL:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# Run setup
railway run python scripts/setup_db.py setup
```

## 🎨 Step 3: Deploy Frontend (Vercel)

### 3.1 Import Repository

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository
4. Vercel will auto-detect Next.js

### 3.2 Configure Project

1. **Root Directory**: `frontend`
2. **Framework Preset**: Next.js
3. **Build Command**: `npm run build`
4. **Output Directory**: `.next`

### 3.3 Add Environment Variables

In Vercel project settings, add:

```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### 3.4 Deploy

1. Click "Deploy"
2. Wait for deployment (2-3 minutes)
3. You'll get a URL like: `https://your-app.vercel.app`

## 📊 Step 4: Initial Data Ingestion

### 4.1 Local Data Ingestion (Recommended)

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Set production DATABASE_URL
export DATABASE_URL="your-neon-connection-string"
export GROQ_API_KEY="your-groq-api-key"

# Ingest from RemoteOK API
python scripts/ingest_data.py api \
  --search-terms "Machine Learning Engineer" "Data Scientist" "MLOps Engineer" \
  --api-source remoteok

# Verify data
python scripts/ingest_data.py stats
```

### 4.2 Using GitHub Actions (Automated)

1. Add secrets to your GitHub repository:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Add:
     - `DATABASE_URL`: Your Neon connection string
     - `GROQ_API_KEY`: Your Groq API key

2. Trigger the workflow:
   - Go to **Actions** tab
   - Select "Data Ingestion Pipeline"
   - Click "Run workflow"
   - Enter search terms (optional)

## ✅ Step 5: Verification

### 5.1 Test Backend

```bash
# Health check
curl https://your-backend.railway.app/health

# Get statistics
curl https://your-backend.railway.app/api/v1/stats

# Test analysis (replace with your URL)
curl -X POST https://your-backend.railway.app/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Machine Learning Engineer"}'
```

### 5.2 Test Frontend

1. Visit `https://your-app.vercel.app`
2. Enter a job search query
3. Verify results display correctly
4. Check citations link to actual job postings

## 🔄 Step 6: Setup CI/CD

### 6.1 Enable Auto-Deployment

**Railway (Backend):**
- Already configured! Deploys automatically on push to `main` branch

**Vercel (Frontend):**
- Already configured! Deploys automatically on push to `main` branch

### 6.2 Configure GitHub Actions

1. The workflows are already in `.github/workflows/`
2. Add repository secrets (if not already done):
   ```
   DATABASE_URL
   GROQ_API_KEY
   API_URL (your Railway backend URL)
   ```

3. Workflows will run:
   - On push to main (for backend/frontend)
   - Daily at 2 AM UTC (for data ingestion)
   - Manually via workflow dispatch

## 📈 Step 7: Monitoring & Maintenance

### 7.1 Monitor Railway Logs

1. Go to Railway dashboard
2. Click on your service
3. View **Deployments** tab for logs
4. Check for errors or warnings

### 7.2 Monitor Neon Database

1. Go to Neon dashboard
2. Check **Monitoring** tab
3. Monitor:
   - Storage usage (max 512 MB on free tier)
   - Connection count
   - Query performance

### 7.3 Update Job Data

Schedule regular data updates:

```bash
# Manually trigger data pipeline
curl -X POST https://api.github.com/repos/yourusername/lmi-agent/actions/workflows/data-pipeline.yml/dispatches \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"ref":"main"}'
```

Or use GitHub Actions UI:
1. Go to **Actions** tab
2. Select "Data Ingestion Pipeline"
3. Click "Run workflow"

## 🐛 Troubleshooting

### Backend Issues

**Problem: App fails to start**
```bash
# Check Railway logs
railway logs

# Common issues:
# 1. Missing environment variables
# 2. Database connection failed
# 3. Python dependencies not installed
```

**Problem: Database connection timeout**
```bash
# Verify DATABASE_URL format
# Should be: postgresql://user:pass@host:5432/dbname

# Test connection locally
python -c "from app.database import engine; engine.connect()"
```

**Problem: Groq API errors**
```bash
# Verify API key
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"

# Check rate limits
# Free tier: 14,400 requests/day
```

### Frontend Issues

**Problem: Cannot connect to backend**
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify CORS settings in backend
- Test backend health endpoint directly

**Problem: Build fails on Vercel**
```bash
# Check Node.js version (should be 18+)
# Verify all dependencies in package.json
# Check build logs in Vercel dashboard
```

### Database Issues

**Problem: pgvector not installed**
```sql
-- Run in Neon SQL editor
CREATE EXTENSION IF NOT EXISTS vector;
```

**Problem: Storage limit exceeded**
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('neondb'));

-- Find largest tables
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🔒 Security Best Practices

### 1. Environment Variables
- ✅ Never commit `.env` files to Git
- ✅ Use different credentials for dev/prod
- ✅ Rotate API keys periodically

### 2. Database Security
- ✅ Use Neon's IP allowlist (if available)
- ✅ Enable SSL connections
- ✅ Limit database user permissions

### 3. API Security
- ✅ Implement rate limiting
- ✅ Add API key authentication for production
- ✅ Monitor for unusual traffic patterns

## 📊 Cost Monitoring

### Free Tier Limits

**Neon:**
- Storage: 512 MB
- Compute: 0.25 vCPU
- Connections: Unlimited

**Railway:**
- $5 credit/month
- ~500 hours of uptime
- Unmetered bandwidth

**Vercel:**
- 100 GB bandwidth/month
- 6,000 build minutes/month
- Unlimited deployments

**Groq:**
- 14,400 requests/day
- ~30 requests/minute

### Optimization Tips

1. **Enable caching** to reduce LLM API calls
2. **Batch embeddings** when ingesting data
3. **Archive old jobs** to save database space
4. **Use indexes** for faster queries

## 🚀 Scaling Beyond Free Tier

When you outgrow free tier:

### Database (Neon)
- Scale Plan: $19/month (3 GB storage)
- Pro Plan: $69/month (unlimited storage)

### Backend (Railway)
- Hobby Plan: $5/month for additional resources
- Pro Plan: $20/month for team features

### Frontend (Vercel)
- Pro Plan: $20/month/user
- More bandwidth and build minutes

### LLM (Groq)
- Contact for enterprise pricing
- Alternative: Use local models or other providers

## 📝 Post-Deployment Checklist

- [ ] Backend health check passes
- [ ] Database contains job data
- [ ] Frontend loads successfully
- [ ] Search returns results
- [ ] Citations link correctly
- [ ] CI/CD pipelines running
- [ ] Monitoring setup complete
- [ ] Documentation updated
- [ ] README has live URLs
- [ ] LinkedIn post about project

## 🎉 Next Steps

1. **Add more data sources**: Integrate additional job APIs
2. **Enhance analytics**: Add geographic trends, salary insights
3. **User accounts**: Save searches and analyses
4. **Email alerts**: Notify users of new opportunities
5. **Mobile app**: React Native version

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review Railway/Vercel/Neon logs
3. Open an issue on GitHub
4. Contact via email or LinkedIn

---

## Quick Reference Commands

```bash
# Local development
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev

# Database setup
python scripts/setup_db.py setup
python scripts/setup_db.py check

# Data ingestion
python scripts/ingest_data.py api --search-terms "ML Engineer"
python scripts/ingest_data.py stats

# Deploy
git add .
git commit -m "Update: description"
git push origin main  # Auto-deploys to Railway & Vercel

# View logs
railway logs --follow
vercel logs your-deployment-url

# Health checks
curl https://your-backend.railway.app/health
curl https://your-backend.railway.app/api/v1/stats
```

## 🌟 Success Metrics

After deployment, track:

- ✅ Uptime (aim for 99%+)
- ✅ Average response time (<5 seconds)
- ✅ Number of job postings indexed
- ✅ Analysis queries per day
- ✅ User engagement (if tracking analytics)

---

**Congratulations!** 🎊 Your LMI Agent is now live and helping people understand the job market!