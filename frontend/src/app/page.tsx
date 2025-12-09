'use client';

import { useState } from 'react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import SearchInterface from '../components/SearchInterface';
import AnalysisDashboard from '../components/AnalysisDashboard';
import { analyzeSkills } from '../lib/api';
import { AnimatePresence, motion } from 'framer-motion';

export default function Home() {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Persistent search state
  const [searchState, setSearchState] = useState({
    query: '',
    location: '',
    liveFetch: false
  });

  const handleSearch = async (query: string, jobRole?: string, location?: string, liveFetch?: boolean) => {
    // Update local state to persist across views
    setSearchState({ query, location: location || '', liveFetch: liveFetch || false });

    setLoading(true);
    setError(null);
    setAnalysis(null); // Reset previous analysis to show transition

    try {
      const result = await analyzeSkills(query, jobRole, location, true, liveFetch);
      setAnalysis(result.data);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze skills');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-background text-white selection:bg-primary-500/30">
      <Navbar />

      <div className="relative min-h-[calc(100vh-4rem)] flex flex-col justify-start pt-10">

        {/* Animated layout transition */}
        <AnimatePresence mode="wait">
          {!analysis && (
            <motion.div
              key="landing"
              exit={{ opacity: 0, y: -20, transition: { duration: 0.4 } }}
              className="flex-1 flex flex-col justify-center pb-32"
            >
              <Hero />
              <SearchInterface
                onSearch={handleSearch}
                loading={loading}
                initialQuery={searchState.query}
                initialLocation={searchState.location}
                initialLiveFetch={searchState.liveFetch}
              />

              {error && (
                <motion.div
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="text-red-400 bg-red-900/20 border border-red-900/50 px-4 py-2 rounded-lg mx-auto mt-6 text-sm"
                >
                  {error}
                </motion.div>
              )}
            </motion.div>
          )}

          {analysis && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              {/* Compact Search Bar for specific results mode */}
              <div className="border-b border-surfaceHighlight bg-background/50 backdrop-blur-sm sticky top-16 z-40 py-4">
                <SearchInterface
                  onSearch={handleSearch}
                  loading={loading}
                  initialQuery={searchState.query}
                  initialLocation={searchState.location}
                  initialLiveFetch={searchState.liveFetch}
                />
              </div>
              <AnalysisDashboard data={analysis} />
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </main>
  );
}