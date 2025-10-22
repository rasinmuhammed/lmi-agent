'use client';

import { ExternalLink, Building, Star } from 'lucide-react';

interface CitationCardProps {
  citation: {
    job_id: number;
    title: string;
    company: string;
    source_url: string;
    relevance_score: number;
  };
}

export default function CitationCard({ citation }: CitationCardProps) {
  const relevancePercentage = Math.round(citation.relevance_score * 100);

  return (
    <div className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-all hover:border-blue-300">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h4 className="font-semibold text-slate-900 text-sm mb-1">{citation.title}</h4>
          <p className="text-slate-600 text-xs flex items-center gap-1">
            <Building size={12} />
            {citation.company}
          </p>
        </div>
        <a
          href={citation.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-700 p-2 hover:bg-blue-50 rounded transition-colors"
          title="View original job posting"
        >
          <ExternalLink size={16} />
        </a>
      </div>
      
      <div className="mt-3 flex items-center gap-2">
        <div className="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden">
          <div 
            className="bg-blue-600 h-full rounded-full transition-all"
            style={{ width: `${relevancePercentage}%` }}
          ></div>
        </div>
        <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
          <Star size={12} className="text-blue-600" />
          {relevancePercentage}%
        </span>
      </div>
    </div>
  );
}