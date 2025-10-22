'use client';

import { useState } from 'react';
import SearchForm from '../components/SearchForm';
import ResultsDisplay from '../components/ResultDisplay';
import { analyzeSkills, getStats } from '../lib/api';
import { Briefcase, TrendingUp, Users } from 'lucide-react';

export default function Home() {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (query: string, jobRole?: string, location?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await analyzeSkills(query, jobRole, location);
      setAnalysis(result.data);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze skills');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
                <Briefcase className="text-blue-600" size={32} />
                LMI Agent
              </h1>
              <p className="text-slate-600 mt-1">
                Labor Market Intelligence powered by AI
              </p>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg">
                <TrendingUp size={18} className="text-blue-600" />
                <span className="text-slate-700 font-medium">Real-time Analysis</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        {!analysis && !loading && (
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              Discover Your Skill Gap
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Get data-driven insights into job market trends, required skills, 
              and actionable recommendations based on real job postings.
            </p>
          </div>
        )}

        {/* Search Form */}
        <div className="mb-8">
          <SearchForm onSearch={handleSearch} loading={loading} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <p className="text-red-800 font-medium">Error: {error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
            <p className="text-slate-600 text-lg">Analyzing job market data...</p>
            <p className="text-slate-500 text-sm mt-2">
              This may take a moment as we process thousands of job postings
            </p>
          </div>
        )}

        {/* Results Display */}
        {analysis && !loading && (
          <ResultsDisplay analysis={analysis} />
        )}

        {/* Features Section (shown when no results) */}
        {!analysis && !loading && (
          <div className="mt-16 grid md:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="text-blue-600" size={24} />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">
                Real-time Data
              </h3>
              <p className="text-slate-600">
                Analysis based on current job postings from multiple sources, 
                ensuring up-to-date market intelligence.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <Users className="text-green-600" size={24} />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">
                Skill Insights
              </h3>
              <p className="text-slate-600">
                Detailed breakdown of required, desired, and emerging skills with 
                frequency analysis and necessity scores.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <Briefcase className="text-purple-600" size={24} />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">
                Actionable Recommendations
              </h3>
              <p className="text-slate-600">
                Get personalized learning paths and career advice based on data-driven 
                analysis of market demands.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-slate-600">
            <p>Built with Next.js, FastAPI, and Groq AI</p>
            <p className="text-sm mt-2">
              Data sourced from public job postings • Analysis powered by RAG
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}