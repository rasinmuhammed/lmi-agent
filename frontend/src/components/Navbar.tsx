'use client';

import { Briefcase, Github } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Navbar() {
    return (
        <motion.header
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            className="fixed top-0 left-0 right-0 z-50 border-b border-surfaceHighlight bg-background/80 backdrop-blur-md"
        >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    <div className="flex items-center gap-3">
                        <div className="bg-gradient-to-br from-primary-500 to-primary-700 p-2 rounded-lg shadow-lg shadow-primary-500/20">
                            <Briefcase className="text-white" size={24} />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white tracking-tight">
                                LMI <span className="text-primary-400">Agent</span>
                            </h1>
                            <p className="text-xs text-slate-400 font-medium tracking-wide">
                                INTELLIGENCE UNIT
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        <a href="https://github.com" target="_blank" rel="noopener noreferrer"
                            className="text-slate-400 hover:text-white transition-colors">
                            <Github size={20} />
                        </a>
                        <button className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-primary-900/20 hover:shadow-primary-600/30">
                            Sign In
                        </button>
                    </div>
                </div>
            </div>
        </motion.header>
    );
}
