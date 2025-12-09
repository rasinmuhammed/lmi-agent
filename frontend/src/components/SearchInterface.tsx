'use client';

import { useState } from 'react';
import { Search, MapPin, Briefcase } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../lib/utils';

interface SearchFormProps {
    onSearch: (query: string, jobRole?: string, location?: string, liveFetch?: boolean) => void;
    loading: boolean;
    initialQuery?: string;
    initialLocation?: string;
    initialLiveFetch?: boolean;
}

export default function SearchInterface({
    onSearch,
    loading,
    initialQuery = '',
    initialLocation = '',
    initialLiveFetch = false
}: SearchFormProps) {
    const [query, setQuery] = useState(initialQuery);
    const [location, setLocation] = useState(initialLocation);
    const [liveFetch, setLiveFetch] = useState(initialLiveFetch);
    const [showFilters, setShowFilters] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;
        onSearch(query, undefined, location, liveFetch);
    };

    return (
        <div className="w-full max-w-2xl mx-auto px-4">
            <motion.form
                onSubmit={handleSubmit}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className={cn(
                    "relative group transition-all duration-300",
                    loading ? "opacity-80 pointer-events-none" : ""
                )}
            >
                <div className="relative flex items-center bg-surface border border-surfaceHighlight rounded-2xl p-2 shadow-2xl shadow-black/20 backdrop-blur-xl focus-within:ring-2 focus-within:ring-primary-500/50 focus-within:border-primary-500/50 transition-all">
                    <Search className="ml-4 text-slate-400" size={20} />
                    <input
                        type="text"
                        name="query"
                        id="search-query"
                        autoComplete="off"
                        className="w-full bg-transparent border-none text-white placeholder-slate-500 focus:outline-none focus:ring-0 px-4 py-3 text-lg"
                        placeholder="Job Title (e.g. AI Engineer)"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />

                    <div className="h-8 w-px bg-slate-700 mx-2" />

                    <MapPin className="text-slate-400 ml-2" size={20} />
                    <input
                        type="text"
                        name="location"
                        id="search-location"
                        autoComplete="off"
                        className="w-1/3 min-w-[150px] bg-transparent border-none text-white placeholder-slate-500 focus:outline-none focus:ring-0 px-4 py-3 text-lg"
                        placeholder="Location"
                        value={location}
                        onChange={(e) => setLocation(e.target.value)}
                    />

                    <button
                        type="submit"
                        className="bg-primary-600 hover:bg-primary-500 text-white px-8 py-3 rounded-xl font-medium transition-all shadow-lg shadow-primary-600/20 whitespace-nowrap"
                    >
                        {loading ? 'Scanning...' : 'Analyze'}
                    </button>
                </div>

                {/* Quick Filters / Recent */}
                <div className="mt-4 flex flex-wrap gap-2 justify-center items-center">
                    <div className="mr-4 flex items-center space-x-2 bg-white/5 px-3 py-1.5 rounded-full border border-white/5">
                        <label className="text-xs text-slate-400 cursor-pointer flex items-center select-none">
                            <input
                                type="checkbox"
                                className="mr-2 accent-primary-500 rounded bg-white/10 border-white/10"
                                checked={liveFetch}
                                onChange={(e) => setLiveFetch(e.target.checked)}
                            />
                            Live Web Search
                        </label>
                    </div>

                    {['Salesforce Developer', 'Data Scientist', 'React Native'].map((tag) => (
                        <button
                            key={tag}
                            type="button"
                            onClick={() => {
                                setQuery(tag);
                                onSearch(tag, undefined, undefined, liveFetch);
                            }}
                            className="text-xs text-slate-400 hover:text-white bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-full transition-colors border border-white/5"
                        >
                            {tag}
                        </button>
                    ))}
                </div>
            </motion.form>
        </div>
    );
}
