'use client';

import { useState } from 'react';
import { Search, MapPin, Briefcase } from 'lucide-react';

interface SearchFormProps {
  onSearch: (query: string, jobRole?: string, location?: string) => void;
  loading: boolean;
}

export default function SearchForm({ onSearch, loading }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [jobRole, setJobRole] = useState('');
  const [location, setLocation] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), jobRole.trim() || undefined, location.trim() || undefined);
    }
  };

  const quickSearches = [
    'Machine Learning Engineer',
    'Data Scientist',
    'MLOps Engineer',
    'AI Engineer',
    'Full Stack Developer'
  ];

  const handleQuickSearch = (term: string) => {
    setQuery(term);
    onSearch(term);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Main Search Input */}
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-slate-700 mb-2">
            What role are you interested in?
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Machine Learning Engineer, Data Scientist..."
              className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>
        </div>

        {/* Optional Filters */}
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="jobRole" className="block text-sm font-medium text-slate-700 mb-2">
              Specific Job Title (Optional)
            </label>
            <div className="relative">
              <Briefcase className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                id="jobRole"
                value={jobRole}
                onChange={(e) => setJobRole(e.target.value)}
                placeholder="Senior ML Engineer"
                className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                disabled={loading}
              />
            </div>
          </div>

          <div>
            <label htmlFor="location" className="block text-sm font-medium text-slate-700 mb-2">
              Location (Optional)
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                id="location"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="San Francisco, Remote"
                className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Analyzing...
            </>
          ) : (
            'Analyze Skills'
          )}
        </button>
      </form>

      {/* Quick Searches */}
      <div className="mt-6 flex flex-wrap gap-2">
        {quickSearches.map((term) => (
          <button
            key={term}
            onClick={() => handleQuickSearch(term)}
            className="px-3 py-1.5 text-sm bg-slate-100 hover:bg-slate-200 rounded-full text-slate-700 transition"
            disabled={loading}
          >
            {term}
          </button>
        ))}
      </div>
    </div>
  );
}
