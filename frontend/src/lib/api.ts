import axios from 'axios';

// API base URL - update this when deploying
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes timeout for LLM generation
});

export interface SkillAnalysisRequest {
  query: string;
  job_role?: string;
  location?: string;
  use_cache?: boolean;
}

export interface CompareRolesRequest {
  role_a: string;
  role_b: string;
  location?: string;
}

export const analyzeSkills = async (
  query: string,
  jobRole?: string,
  location?: string,
  useCache: boolean = true
) => {
  const response = await api.post('/api/v1/analyze', {
    query,
    job_role: jobRole,
    location,
    use_cache: useCache,
  });
  return response.data;
};

export const compareRoles = async (
  roleA: string,
  roleB: string,
  location?: string
) => {
  const response = await api.post('/api/v1/compare', {
    role_a: roleA,
    role_b: roleB,
    location,
  });
  return response.data;
};

export const getTrendingSkills = async (
  category: string = 'all',
  days: number = 30
) => {
  const response = await api.get('/api/v1/trending', {
    params: { category, days },
  });
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/api/v1/stats');
  return response.data;
};

export const searchJobs = async (
  query: string,
  location?: string,
  limit: number = 10
) => {
  const response = await api.get('/api/v1/jobs/search', {
    params: { query, location, limit },
  });
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;