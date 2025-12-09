'use client';

import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

export default function Hero() {
    return (
        <div className="relative pt-32 pb-16 overflow-hidden">
            {/* Background Elements */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full z-0 pointer-events-none">
                <div className="absolute top-[20%] left-[20%] w-96 h-96 bg-primary-500/10 rounded-full blur-3xl animate-pulseSlow" />
                <div className="absolute top-[30%] right-[20%] w-72 h-72 bg-accent-purple/10 rounded-full blur-3xl animate-pulseSlow" style={{ animationDelay: '1s' }} />
            </div>

            <div className="relative z-10 max-w-4xl mx-auto px-4 text-center">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                >
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-surface border border-surfaceHighlight mb-6 backdrop-blur-sm">
                        <Sparkles size={14} className="text-accent-cyan" />
                        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                            Powered by RAG & GenAI
                        </span>
                    </div>

                    <h1 className="text-5xl md:text-7xl font-bold text-white tracking-tight mb-6">
                        Future-Proof Your <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-400 to-accent-cyan">
                            Career Path
                        </span>
                    </h1>

                    <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
                        Analyze real-time market data to uncover widely demanded skills,
                        emerging trends, and personalized growth opportunities.
                    </p>
                </motion.div>
            </div>
        </div>
    );
}
