import React, { useState, useEffect, useRef } from 'react';
import { CONFIG } from '../config';
import { Shield, Check, X, Loader2, Lock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const PasswordChecker = () => {
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [selectedComponents, setSelectedComponents] = useState(['pass_strength_ai', 'zxcvbn', 'haveibeenpwned']);
    const bottomRef = useRef(null);
    const inputRef = useRef(null);
    const [history, setHistory] = useState([]);

    const scrollToBottom = () => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [result, error, loading, history]);

    const components = [
        { id: 'pass_strength_ai', label: 'AI Engine' },
        { id: 'zxcvbn', label: 'zxcvbn' },
        { id: 'haveibeenpwned', label: 'Breach Check' }
    ];

    const toggleComponent = (id) => {
        setSelectedComponents(prev => 
            prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
        );
    };

    const handleAnalyze = async () => {
        if (!password) return;
        setLoading(true);
        setError(null);
        setResult(null);
        setHistory(prev => [...prev, { role: 'user', content: password }]);
        setPassword('');
        scrollToBottom();
        inputRef.current?.focus();

        try {
            const response = await fetch(`${CONFIG.passwordChecker.baseUrl}${CONFIG.passwordChecker.endpoints.score}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    password,
                    components: selectedComponents
                })
            });

            if (response.ok) {
                const data = await response.json();
                setResult(data);
                setHistory(prev => [...prev, { role: 'system', content: `Score ${data.normalized_score}/100` }]);
            } else {
                const err = await response.json();
                setError(err.detail || 'Analysis failed');
                setHistory(prev => [...prev, { role: 'error', content: err.detail || 'Analysis failed' }]);
            }
        } catch (e) {
            setError(e.message);
            setHistory(prev => [...prev, { role: 'error', content: e.message }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 md:space-y-6 custom-scrollbar">
                {history.length === 0 && (
                    <div className="text-center py-8 md:py-10">
                        <div className="inline-flex items-center justify-center w-12 h-12 md:w-16 md:h-16 rounded-full bg-neon-dim mb-4">
                            <Shield className="w-6 h-6 md:w-8 md:h-8 text-neon" />
                        </div>
                        <h2 className="text-xl md:text-2xl font-bold text-white mb-2">Password Security Analysis</h2>
                        <p className="text-gray-400 max-w-md mx-auto">
                            Analyze password strength using multiple security engines including AI analysis, entropy calculation, and breach detection.
                        </p>
                        
                        <div className="flex flex-wrap justify-center gap-2 mt-6">
                            {components.map(comp => (
                                <button
                                    key={comp.id}
                                    onClick={() => toggleComponent(comp.id)}
                                    className={`px-4 py-2 rounded-full text-xs font-medium transition-all duration-300 border ${
                                        selectedComponents.includes(comp.id)
                                        ? 'bg-neon-dim border-neon text-neon shadow-[0_0_10px_rgba(0,255,136,0.2)]'
                                        : 'bg-dark-panel border-dark-border text-gray-500 hover:border-gray-500'
                                    }`}
                                >
                                    {comp.label}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {history.length > 0 && (
                    <div className="space-y-4">
                        {history.map((entry, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex gap-3 ${entry.role === 'user' ? 'flex-row-reverse' : ''}`}
                            >
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                                    entry.role === 'user' ? 'bg-neon text-black' :
                                    entry.role === 'error' ? 'bg-red-500 text-white' : 'bg-dark-panel border border-dark-border text-neon'
                                }`}>
                                    <Shield className="w-5 h-5" />
                                </div>
                                <div className={`max-w-[80%] rounded-2xl p-3 text-sm ${
                                    entry.role === 'user'
                                    ? 'bg-neon/10 border border-neon/20 text-white'
                                    : entry.role === 'error'
                                    ? 'bg-red-500/10 border border-red-500/20 text-red-200'
                                    : 'bg-dark-panel border border-dark-border text-gray-200'
                                }`}>
                                    <div className="whitespace-pre-wrap leading-relaxed break-words">
                                        {entry.role === 'user' ? `Password: ${entry.content}` : entry.content}
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}

                <AnimatePresence>
                    {result && (
                        <motion.div 
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="bg-dark-panel border border-dark-border rounded-xl p-6 backdrop-blur-md"
                        >
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-lg font-semibold text-neon">Analysis Complete</h3>
                                <div className="text-right">
                                    <div className="text-sm text-gray-400">Overall Score</div>
                                    <div className="text-3xl font-bold text-white">{result.normalized_score}<span className="text-lg text-gray-500">/100</span></div>
                                </div>
                            </div>

                            <div className="space-y-4">
                                {result.components.map((comp, idx) => (
                                    <div key={idx} className="bg-black/20 rounded-lg p-4 border border-white/5">
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                {comp.success ? <Check className="w-4 h-4 text-neon" /> : <X className="w-4 h-4 text-red-500" />}
                                                <span className="font-medium text-white">{comp.label}</span>
                                            </div>
                                            <span className="text-neon font-mono">{comp.normalized_score || 'N/A'}</span>
                                        </div>
                                        {comp.error && <p className="text-xs text-red-400 mt-1">{comp.error}</p>}
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                    
                    {error && (
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-center"
                        >
                            {error}
                        </motion.div>
                    )}
                </AnimatePresence>
                <div ref={bottomRef} />
            </div>

            <div className="p-4 md:p-6 border-t backdrop-blur-md">
                <div className="flex gap-3 md:gap-4">
                    <div className="relative flex-1">
                        <input
                            ref={inputRef}
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                            placeholder="Enter password to analyze..."
                            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 md:px-5 py-3 md:py-4 pl-11 md:pl-12 text-white placeholder-gray-600 focus:outline-none focus:border-neon/50 focus:ring-1 focus:ring-neon/50 transition-all"
                        />
                        <Lock className="absolute left-3 md:left-4 top-1/2 -translate-y-1/2 w-4 h-4 md:w-5 md:h-5 text-gray-600" />
                    </div>
                    <button
                        onClick={handleAnalyze}
                        disabled={loading || !password}
                        className="bg-neon text-black font-bold rounded-xl px-4 md:px-6 hover:bg-[#00dd77] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center min-w-[48px] md:min-w-[60px]"
                    >
                        {loading ? <Loader2 className="w-5 h-5 md:w-6 md:h-6 animate-spin" /> : <Shield className="w-5 h-5 md:w-6 md:h-6" />}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PasswordChecker;
