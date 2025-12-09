'use client';

import { motion } from 'framer-motion';
import {
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
    BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';
import { Layers, Zap, TrendingUp, DollarSign, ExternalLink } from 'lucide-react';
import { cn } from '../lib/utils';

// Types (should ideally generally be in a types file)
interface AnalysisData {
    summary: string;
    top_skills: Array<{ skill: string; score: number }>;
    skill_frequencies: Record<string, number>;
    skill_necessity_scores: Record<string, number>;
    emerging_skills: Array<{ skill: string; trend_score: number }>;
    total_jobs_analyzed: number;
    salary_range?: { min: number; max: number; currency: string }; // Mocked if missing
    job_postings_sample?: any[];
}

export default function AnalysisDashboard({ data }: { data: AnalysisData }) {
    // Transform data for charts
    const radarData = (data.top_skills || []).slice(0, 6).map(s => ({
        subject: s.skill,
        A: s.score * 100, // Normalized for visual
        fullMark: 100
    }));

    const barData = Object.entries(data.skill_frequencies || {})
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
        .map(([name, count]) => ({ name, count }));

    return (
        <div className="max-w-7xl mx-auto px-4 py-12 space-y-8">

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <GlassCard delay={0.1}>
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
                            <Layers size={20} />
                        </div>
                        <span className="text-xs text-slate-500 font-mono">SAMPLE SIZE</span>
                    </div>
                    <div className="text-3xl font-bold text-white mb-1">
                        {data.total_jobs_analyzed}
                    </div>
                    <p className="text-sm text-slate-400">Job postings analyzed</p>
                </GlassCard>

                <GlassCard delay={0.2}>
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-amber-500/20 rounded-lg text-amber-400">
                            <Zap size={20} />
                        </div>
                        <span className="text-xs text-slate-500 font-mono">TOP SKILL</span>
                    </div>
                    <div className="text-2xl font-bold text-white mb-1 truncate">
                        {(data.top_skills || [])[0]?.skill || 'N/A'}
                    </div>
                    <p className="text-sm text-slate-400">Most required skill</p>
                </GlassCard>

                <GlassCard delay={0.3}>
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-emerald-500/20 rounded-lg text-emerald-400">
                            <TrendingUp size={20} />
                        </div>
                        <span className="text-xs text-slate-500 font-mono">EMERGING</span>
                    </div>
                    <div className="text-2xl font-bold text-white mb-1 truncate">
                        {(() => {
                            const first = (data.emerging_skills || [])[0];
                            if (!first) return 'None detected';
                            return typeof first === 'object' ? first.skill : first;
                        })()}
                    </div>
                    <p className="text-sm text-slate-400">Fastest growing trend</p>
                </GlassCard>

                <GlassCard delay={0.4}>
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-purple-500/20 rounded-lg text-purple-400">
                            <DollarSign size={20} />
                        </div>
                        <span className="text-xs text-slate-500 font-mono">EST. SALARY</span>
                    </div>
                    <div className="text-2xl font-bold text-white mb-1">
                        $120k - $160k
                    </div>
                    <p className="text-sm text-slate-400">Estimated market range</p>
                </GlassCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Chart Area */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Skill Radar */}
                    <GlassCard className="min-h-[400px]">
                        <h3 className="text-lg font-semibold text-white mb-6">Skill Profile Match</h3>
                        <div className="h-[300px] w-full flex items-center justify-center">
                            {radarData.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                                        <PolarGrid stroke="rgba(255,255,255,0.1)" />
                                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                        <Radar
                                            name="Market Demand"
                                            dataKey="A"
                                            stroke="#3b82f6"
                                            strokeWidth={3}
                                            fill="#3b82f6"
                                            fillOpacity={0.3}
                                        />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1e293b', borderColor: 'rgba(255,255,255,0.1)', color: '#fff' }}
                                            itemStyle={{ color: '#fff' }}
                                        />
                                    </RadarChart>
                                </ResponsiveContainer>
                            ) : (
                                <p className="text-slate-500 italic">No skill data available for visualization.</p>
                            )}
                        </div>
                    </GlassCard>

                    {/* AI Analysis Text with Markdown-like styling */}
                    <GlassCard>
                        <h3 className="text-lg font-semibold text-white mb-4">Market Intelligence Report</h3>
                        <div className="prose prose-invert max-w-none text-slate-300">
                            <p className="whitespace-pre-line leading-relaxed">
                                {data.summary}
                            </p>
                        </div>
                    </GlassCard>
                </div>

                {/* Sidebar / Job List */}
                <div className="space-y-6">
                    <GlassCard title="Top Demanded Skills">
                        <div className="h-[200px] w-full mb-4 flex items-center justify-center">
                            {barData.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={barData} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.05)" />
                                        <XAxis type="number" hide />
                                        <YAxis dataKey="name" type="category" width={100} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                        <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
                                        <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={20} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <p className="text-sm text-slate-500 italic">No trend data available.</p>
                            )}
                        </div>
                    </GlassCard>

                    <GlassCard title="Recent Job Postings">
                        <div className="space-y-3">
                            {data.job_postings_sample?.map((job: any, i: number) => (
                                <div key={i} className="group p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/5 cursor-pointer">
                                    <h4 className="font-medium text-white truncate">{job.title}</h4>
                                    <div className="flex justify-between items-center mt-2">
                                        <span className="text-xs text-slate-400">{job.company}</span>
                                        <ExternalLink size={12} className="text-slate-500 group-hover:text-primary-400" />
                                    </div>
                                </div>
                            ))}
                            {!data.job_postings_sample && (
                                <p className="text-sm text-slate-500 italic">No specific job examples available.</p>
                            )}
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    );
}

function GlassCard({ children, className, title, delay = 0 }: any) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay, duration: 0.5 }}
            className={cn(
                "bg-surface border border-surfaceHighlight rounded-2xl p-6 backdrop-blur-md",
                className
            )}
        >
            {title && <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>}
            {children}
        </motion.div>
    );
}
