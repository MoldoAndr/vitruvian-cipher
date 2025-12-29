import React, { useState, useRef, useEffect } from 'react';
import { CONFIG } from '../config';
import { BrainCircuit, Send, Loader2, Bot, User } from 'lucide-react';
import { motion } from 'framer-motion';

const CryptoExpert = ({ inputValue = '', onInputChange }) => {
    const [query, setQuery] = useState(inputValue);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState(null);
    const chatEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        setQuery(inputValue);
    }, [inputValue]);

    useEffect(scrollToBottom, [messages, loading]);

    const handleSend = async () => {
        if (!query.trim()) return;
        
        const userMsg = { role: 'user', content: query };
        setMessages(prev => [...prev, userMsg]);
        setQuery('');
        if (onInputChange) onInputChange('');
        setLoading(true);
        scrollToBottom();
        inputRef.current?.focus();

        try {
            const payload = { query: userMsg.content };
            if (conversationId) payload.conversation_id = conversationId;

            const response = await fetch(`${CONFIG.theorySpecialist.baseUrl}${CONFIG.theorySpecialist.endpoints.generate}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                setConversationId(data.conversation_id);
                setMessages(prev => [...prev, { 
                    role: 'system', 
                    content: data.answer,
                    sources: data.sources 
                }]);
            } else {
                setMessages(prev => [...prev, { role: 'error', content: 'Failed to get response from the expert.' }]);
            }
        } catch (e) {
            setMessages(prev => [...prev, { role: 'error', content: e.message }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 md:space-y-6 custom-scrollbar">
                {messages.length === 0 && (
                    <div className="text-center py-12 md:py-20">
                        <BrainCircuit className="w-12 h-12 md:w-16 md:h-16 mx-auto mb-4 text-neon" />
                        <h2 className="text-lg md:text-xl font-bold text-white">Cryptography Expert</h2>
                        <p className="text-sm text-gray-400 mt-2">Ask about algorithms, protocols, and security proofs.</p>
                    </div>
                )}
                
                {messages.map((msg, idx) => (
                    <motion.div 
                        key={idx}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex gap-3 md:gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                            msg.role === 'user' ? 'bg-neon text-black' : 
                            msg.role === 'error' ? 'bg-red-500 text-white' : 'bg-dark-panel border border-dark-border text-neon'
                        }`}>
                            {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                        </div>
                        
                        <div className={`max-w-[80%] rounded-2xl p-3 md:p-4 ${
                            msg.role === 'user' 
                            ? 'bg-neon/10 border border-neon/20 text-white' 
                            : msg.role === 'error'
                            ? 'bg-red-500/10 border border-red-500/20 text-red-200'
                            : 'bg-dark-panel border border-dark-border text-gray-200'
                        }`}>
                            <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                            
                            {msg.sources && msg.sources.length > 0 && (
                                <div className="mt-4 pt-4 border-t border-white/5">
                                    <div className="text-xs font-bold text-gray-500 mb-2 uppercase tracking-wider">Sources</div>
                                    <div className="space-y-2">
                                        {msg.sources.map((source, sIdx) => {
                                            const metadata = source.metadata || {};
                                            let name = metadata.source || 'Unknown Source';
                                            try { name = decodeURIComponent(name); } catch (e) {}
                                            
                                            return (
                                                <div key={sIdx} className="text-xs text-gray-400 bg-black/20 p-2 rounded border border-white/5">
                                                    <span className="text-neon">• {name}</span>
                                                    {metadata.source_page && <span className="opacity-50"> (Page {metadata.source_page})</span>}
                                                    {source.relevance_score && <span className="float-right opacity-50">{(source.relevance_score * 100).toFixed(1)}%</span>}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    </motion.div>
                ))}
                
                {loading && (
                    <div className="flex gap-3 md:gap-4">
                        <div className="w-8 h-8 rounded-full bg-dark-panel border border-dark-border flex items-center justify-center">
                            <Bot className="w-5 h-5 text-neon" />
                        </div>
                        <div className="bg-dark-panel border border-dark-border rounded-2xl p-3 md:p-4 flex items-center gap-2">
                            <span className="text-sm text-gray-400">Thinking</span>
                            <div className="flex gap-1">
                                <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1 }} className="w-1 h-1 bg-neon rounded-full" />
                                <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} className="w-1 h-1 bg-neon rounded-full" />
                                <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} className="w-1 h-1 bg-neon rounded-full" />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            <div className="p-4 md:p-6 border-t backdrop-blur-md">
                <div className="flex gap-3 md:gap-4">
                    <textarea
                        ref={inputRef}
                        value={query}
                        onChange={(e) => {
                            setQuery(e.target.value);
                            if (onInputChange) onInputChange(e.target.value);
                        }}
                        onKeyPress={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        placeholder="Ask about cryptography..."
                        className="flex-1 bg-dark-bg border border-dark-border rounded-xl px-4 md:px-5 py-3 md:py-4 text-white placeholder-gray-600 focus:outline-none focus:border-neon/50 focus:ring-1 focus:ring-neon/50 transition-all resize-none h-12 md:h-[60px] custom-scrollbar"
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading || !query.trim()}
                        className="bg-neon text-black font-bold rounded-xl px-4 md:px-6 hover:bg-[#00dd77] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center min-w-[48px] md:min-w-[60px]"
                    >
                        {loading ? <Loader2 className="w-5 h-5 md:w-6 md:h-6 animate-spin" /> : <Send className="w-5 h-5 md:w-6 md:h-6" />}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CryptoExpert;
