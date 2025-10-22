'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Award, BookOpen, ExternalLink, MapPin, Building } from 'lucide-react';
import CitationCard from './CitationCard';

interface ResultsDisplayProps {
  analysis: any;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function ResultsDisplay({ analysis }: ResultsDisplayProps) {
  // Prepare data for charts
  const topSkillsData = analysis.top_skills?.slice(0, 10).map((skill: any) => ({
    name: skill.skill,
    value: typeof skill.frequency === 'string' 
      ? parseInt(skill.frequency.replace('%', '')) 
      : skill.frequency,
    necessity: skill.necessity_level
  })) || [];

  const skillCategoryData = analysis.skill_categories ? [
    { name: 'Technical', value: analysis.skill_categories.technical_skills?.length || 0 },
    { name: 'Soft Skills', value: analysis.skill_categories.soft_skills?.length || 0 },
    { name: 'Tools', value: analysis.skill_categories.tools_and_platforms?.length || 0 },
  ].filter(item => item.value > 0) : [];

  return (
    <div className="space-y-8">
      {/* Summary Card */}
      <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl shadow-lg p-8 text-white">
        <h2 className="text-3xl font-bold mb-4">Analysis Summary</h2>
        <p className="text-blue-100 text-lg leading-relaxed">
          {analysis.summary || 'Comprehensive skill analysis based on current job market data.'}
        </p>
        <div className="mt-6 flex flex-wrap gap-4">
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
            <p className="text-blue-100 text-sm">Jobs Analyzed</p>
            <p className="text-2xl font-bold">{analysis.total_jobs_analyzed || 0}</p>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
            <p className="text-blue-100 text-sm">Skills Identified</p>
            <p className="text-2xl font-bold">{analysis.top_skills?.length || 0}</p>
          </div>
          {analysis.from_cache && (
            <div className="bg-yellow-500/30 backdrop-blur-sm rounded-lg px-4 py-2">
              <p className="text-white text-sm">⚡ Cached Result</p>
            </div>
          )}
        </div>
      </div>

      {/* Top Skills Section */}
      {analysis.top_skills && analysis.top_skills.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <Award className="text-blue-600" size={28} />
            <h3 className="text-2xl font-bold text-slate-900">Top Required Skills</h3>
          </div>

          {/* Skills Chart */}
          <div className="mb-8">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={topSkillsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="name" 
                  angle={-45} 
                  textAnchor="end" 
                  height={120}
                  tick={{ fontSize: 12 }}
                />
                <YAxis />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px'
                  }}
                />
                <Legend />
                <Bar dataKey="value" fill="#3b82f6" name="Frequency (%)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Skills List */}
          <div className="grid md:grid-cols-2 gap-4">
            {analysis.top_skills.map((skill: any, index: number) => (
              <div 
                key={index} 
                className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-slate-900 text-lg">{skill.skill}</h4>
                  <span className={`
                    px-3 py-1 rounded-full text-xs font-medium
                    ${skill.necessity_level === 'mandatory' ? 'bg-red-100 text-red-700' : ''}
                    ${skill.necessity_level === 'highly_desired' ? 'bg-orange-100 text-orange-700' : ''}
                    ${skill.necessity_level === 'nice_to_have' ? 'bg-green-100 text-green-700' : ''}
                  `}>
                    {skill.necessity_level?.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-slate-600 text-sm mb-2">{skill.explanation}</p>
                <p className="text-blue-600 font-medium text-sm">
                  Frequency: {skill.frequency}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skill Categories */}
      {skillCategoryData.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
          <h3 className="text-2xl font-bold text-slate-900 mb-6">Skill Distribution</h3>
          
          <div className="grid md:grid-cols-2 gap-8">
            {/* Pie Chart */}
            <div>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={skillCategoryData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {skillCategoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Category Details */}
            <div className="space-y-4">
              {analysis.skill_categories?.technical_skills && (
                <div>
                  <h4 className="font-semibold text-slate-900 mb-2 flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                    Technical Skills
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.skill_categories.technical_skills.map((skill: string, i: number) => (
                      <span key={i} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {analysis.skill_categories?.soft_skills && (
                <div>
                  <h4 className="font-semibold text-slate-900 mb-2 flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    Soft Skills
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.skill_categories.soft_skills.map((skill: string, i: number) => (
                      <span key={i} className="px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {analysis.skill_categories?.tools_and_platforms && (
                <div>
                  <h4 className="font-semibold text-slate-900 mb-2 flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                    Tools & Platforms
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.skill_categories.tools_and_platforms.map((skill: string, i: number) => (
                      <span key={i} className="px-3 py-1 bg-orange-50 text-orange-700 rounded-full text-sm">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Emerging Trends */}
      {analysis.emerging_trends && analysis.emerging_trends.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="text-green-600" size={28} />
            <h3 className="text-2xl font-bold text-slate-900">Emerging Trends</h3>
          </div>
          <ul className="space-y-3">
            {analysis.emerging_trends.map((trend: string, index: number) => (
              <li key={index} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                <span className="flex-shrink-0 w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  {index + 1}
                </span>
                <p className="text-slate-700">{trend}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {analysis.recommendations && analysis.recommendations.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <BookOpen className="text-purple-600" size={28} />
            <h3 className="text-2xl font-bold text-slate-900">Actionable Recommendations</h3>
          </div>
          <ul className="space-y-3">
            {analysis.recommendations.map((rec: string, index: number) => (
              <li key={index} className="flex items-start gap-3 p-4 bg-purple-50 rounded-lg border-l-4 border-purple-600">
                <span className="text-2xl">💡</span>
                <p className="text-slate-700 flex-1">{rec}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Citations */}
      {analysis.citations && analysis.citations.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
          <h3 className="text-2xl font-bold text-slate-900 mb-4">Data Sources & Citations</h3>
          <p className="text-slate-600 mb-4">
            This analysis is based on {analysis.total_jobs_analyzed} real job postings. 
            Below are the top sources used:
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            {analysis.citations.slice(0, 6).map((citation: any, index: number) => (
              <CitationCard key={index} citation={citation} />
            ))}
          </div>
        </div>
      )}

      {/* Sample Job Postings */}
      {analysis.job_postings_sample && analysis.job_postings_sample.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
          <h3 className="text-2xl font-bold text-slate-900 mb-4">Sample Job Postings</h3>
          <div className="space-y-4">
            {analysis.job_postings_sample.map((job: any, index: number) => (
              <div key={index} className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-slate-900 text-lg">{job.title}</h4>
                  {job.source_url && (
                    <a 
                      href={job.source_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    >
                      <ExternalLink size={16} />
                    </a>
                  )}
                </div>
                <div className="flex items-center gap-4 text-sm text-slate-600 mb-2">
                  <span className="flex items-center gap-1">
                    <Building size={14} />
                    {job.company}
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin size={14} />
                    {job.location}
                  </span>
                </div>
                <p className="text-slate-700 text-sm line-clamp-2">{job.description}</p>
                {job.skills && job.skills.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {job.skills.slice(0, 5).map((skill: string, i: number) => (
                      <span key={i} className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}