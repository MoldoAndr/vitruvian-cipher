import React, { useState, useRef, useEffect } from 'react';
import { CONFIG } from '../config';
import { Split, ArrowRight, Loader2, Target, Layers } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ChoiceMaker = () => {
    const [text, setText] = useState('');
    const [mode, setMode] = useState('both');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [history, setHistory] = useState([]);
    const bottomRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [result, error, loading]);

    const handleAnalyze = async () => {
        const prompt = text.trim();
        if (!prompt) return;
        
        setLoading(true);
        setError(null);
        setResult(null);
        setHistory(prev => [...prev, { role: 'user', content: prompt }]);
        setText('');
        scrollToBottom();
        inputRef.current?.focus();

        try {
            const callChoiceMaker = async (operation) => {
                const response = await fetch(`${CONFIG.choiceMaker.baseUrl}${CONFIG.choiceMaker.endpoints.extract}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: prompt, operation })
                });
                
                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    throw new Error(err.message || err.detail || `HTTP ${response.status}`);
                }
                
                const data = await response.json();
                if (data.status !== 'ok') throw new Error(data.message || 'Error response');
                return data;
            };

            let intentData = null;
            let entityData = null;

            if (mode === 'both') {
                [intentData, entityData] = await Promise.all([
                    callChoiceMaker('intent_extraction'),
                    callChoiceMaker('entity_extraction')
                ]);
            } else if (mode === 'intent_extraction') {
                intentData = await callChoiceMaker('intent_extraction');
            } else {
                entityData = await callChoiceMaker('entity_extraction');
            }

            const combinedResult = { intent: intentData?.result, entities: entityData?.result };
            setResult(combinedResult);
            setHistory(prev => [...prev, { role: 'system', content: combinedResult }]);

        } catch (e) {
            setError(e.message);
            setHistory(prev => [...prev, { role: 'error', content: e.message }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                {history.length === 0 && (
                    <div className="text-center py-10">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-neon-dim mb-4">
                            <Split className="w-8 h-8 text-neon" />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Choice Maker</h2>
                        <p className="text-gray-400 max-w-md mx-auto">
                            Describe a task and let the AI classify the intent and extract relevant entities.
                        </p>

                        <div className="flex justify-center gap-2 mt-6">
                            {[
                                { id: 'intent_extraction', label: 'Intent Only' },
                                { id: 'entity_extraction', label: 'Entities Only' },
                                { id: 'both', label: 'Both' }
                            ].map(m => (
                                <button
                                    key={m.id}
                                    onClick={() => setMode(m.id)}
                                    className={`px-4 py-2 rounded-full text-xs font-medium transition-all duration-300 border ${
                                        mode === m.id
                                        ? 'bg-neon-dim border-neon text-neon shadow-[0_0_10px_rgba(0,255,136,0.2)]'
                                        : 'bg-dark-panel border-dark-border text-gray-500 hover:border-gray-500'
                                    }`}
                                >
                                    {m.label}
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
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex gap-4 ${entry.role === 'user' ? 'flex-row-reverse' : ''}`}
                            >
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                                    entry.role === 'user' ? 'bg-neon text-black' :
                                    entry.role === 'error' ? 'bg-red-500 text-white' : 'bg-dark-panel border border-dark-border text-neon'
                                }`}>
                                    <Split className="w-5 h-5" />
                                </div>
                                <div className={`max-w-[80%] rounded-2xl p-4 ${
                                    entry.role === 'user'
                                    ? 'bg-neon/10 border border-neon/20 text-white'
                                    : entry.role === 'error'
                                    ? 'bg-red-500/10 border border-red-500/20 text-red-200'
                                    : 'bg-dark-panel border border-dark-border text-gray-200'
                                }`}>
                                    {entry.role === 'system' && entry.content
                                        ? (
                                            <div className="space-y-3 text-sm">
                                                {entry.content.intent && (
                                                    <div>
                                                        <div className="text-neon font-semibold flex items-center gap-2">
                                                            <Target className="w-4 h-4" /> Intent
                                                        </div>
                                                        <div className="mt-1 text-white">
                                                            {entry.content.intent.intent?.label || entry.content.intent.label || 'Unknown'}
                                                            <span className="text-xs text-gray-400 ml-2">
                                                                {((entry.content.intent.intent?.score || entry.content.intent.score || 0) * 100).toFixed(1)}%
                                                            </span>
                                                        </div>
                                                    </div>
                                                )}
                                                {entry.content.entities && (
                                                    <div>
                                                        <div className="text-neon font-semibold flex items-center gap-2">
                                                            <Layers className="w-4 h-4" /> Entities
                                                        </div>
                                                        {(() => {
                                                            const entities = entry.content.entities.entities?.entities || entry.content.entities.entities || entry.content.entities;
                                                            const list = Array.isArray(entities) ? entities : [];
                                                            if (!list.length) return <div className="text-gray-500">No entities detected</div>;
                                                            return (
                                                                <div className="space-y-1 mt-1">
                                                                    {list.map((entity, i2) => (
                                                                        <div key={i2} className="flex items-center justify-between bg-black/20 p-2 rounded border border-white/5 text-xs">
                                                                            <div>
                                                                                <span className="text-neon font-medium mr-2">{entity.entity}</span>
                                                                                <span className="text-gray-300">"{entity.text}"</span>
                                                                            </div>
                                                                            <span className="text-gray-400">{(entity.score * 100).toFixed(1)}%</span>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            );
                                                        })()}
                                                    </div>
                                                )}
                                            </div>
                                        ) : (
                                            <div className="whitespace-pre-wrap text-sm leading-relaxed">{entry.content}</div>
                                        )
                                    }
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}

                <div ref={bottomRef} />
            </div>

            <div className="p-6 border-t backdrop-blur-md">
                <div className="flex gap-4">
                    <textarea
                        ref={inputRef}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onKeyPress={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleAnalyze();
                            }
                        }}
                        placeholder="Describe what you want to do (e.g. 'crack this SHA-256 hash')..."
                        className="flex-1 bg-dark-bg border border-dark-border rounded-xl px-5 py-4 text-white placeholder-gray-600 focus:outline-none focus:border-neon/50 focus:ring-1 focus:ring-neon/50 transition-all resize-none h-[60px] custom-scrollbar"
                    />
                    <button
                        onClick={handleAnalyze}
                        disabled={loading || !text.trim()}
                        className="bg-neon text-black font-bold rounded-xl px-6 hover:bg-[#00dd77] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center min-w-[60px]"
                    >
                        {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : <ArrowRight className="w-6 h-6" />}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChoiceMaker;
