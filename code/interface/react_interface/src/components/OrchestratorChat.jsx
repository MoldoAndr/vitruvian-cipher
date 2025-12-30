import React, { useRef, useState, useEffect } from 'react';
import { CONFIG } from '../config';
import { MessageSquare, Send, Loader2, Sparkles, PlugZap, Layers, Target, RefreshCcw, ChevronDown, ChevronUp, Settings, MessageCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const PROVIDERS = [
    { id: 'openai', label: 'OpenAI' },
    { id: 'anthropic', label: 'Anthropic' },
    { id: 'gemini', label: 'Gemini' },
    { id: 'ollama_local', label: 'Ollama Local' },
    { id: 'ollama_cloud', label: 'Ollama Cloud' },
];

const MODEL_OPTIONS = [
    'deepseek-v3.2:cloud',
    'gpt-oss:120b-cloud',
    'kimi-k2-thinking:cloud',
];

const OrchestratorChat = ({ inputValue = '', onInputChange }) => {
    const [input, setInput] = useState(inputValue);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [provider, setProvider] = useState('openai');
    const [apiKey, setApiKey] = useState('');
    const [fallbackEnabled, setFallbackEnabled] = useState(false);
    const [fallbackProviders, setFallbackProviders] = useState('');
    const [plannerProfile, setPlannerProfile] = useState('planner');
    const [responderProfile, setResponderProfile] = useState('responder');
    const [modelOverride, setModelOverride] = useState('');
    const [plannerModelOverride, setPlannerModelOverride] = useState('');
    const [summary, setSummary] = useState('');
    const [debug, setDebug] = useState(false);
    const [theoryConversationId, setTheoryConversationId] = useState('');
    const [extraKeys, setExtraKeys] = useState({
        openai: '',
        anthropic: '',
        gemini: '',
        ollama_local: '',
        ollama_cloud: '',
    });
    const [showConfig, setShowConfig] = useState(false);
    const [showAdvanced, setShowAdvanced] = useState(false);

    const bottomRef = useRef(null);
    const [conversationId, setConversationId] = useState(() => `conv_${Math.random().toString(36).slice(2, 10)}`);

    useEffect(() => {
        setInput(inputValue);
    }, [inputValue]);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [history, loading]);

    const buildContext = () => {
        const recent = history
            .filter(item => item.role === 'user' || item.role === 'assistant')
            .slice(-8)
            .map(item => ({ role: item.role, content: item.content }));

        const context = {};
        if (recent.length) context.history = recent;
        if (summary.trim()) context.summary = summary.trim();
        if (theoryConversationId.trim()) {
            context.state = { ...context.state, theory_conversation_id: theoryConversationId.trim() };
        }
        return Object.keys(context).length ? context : undefined;
    };

    const buildAPIKeys = () => {
        const map = {};
        Object.entries(extraKeys).forEach(([key, value]) => {
            if (value && value.trim()) {
                map[key] = value.trim();
            }
        });
        return Object.keys(map).length ? map : undefined;
    };

    const handleSend = async () => {
        const text = input.trim();
        if (!text || loading) return;

        setHistory(prev => [...prev, { role: 'user', content: text }]);
        setInput('');
        if (onInputChange) onInputChange('');
        setLoading(true);

        const payload = {
            conversation_id: conversationId,
            text,
            llm: {
                provider,
                profile: responderProfile,
                planner_profile: plannerProfile,
                model: modelOverride.trim() || undefined,
                planner_model: plannerModelOverride.trim() || undefined,
                api_key: apiKey.trim() || undefined,
                api_keys: buildAPIKeys(),
                allow_fallback: fallbackEnabled,
                fallback_providers: fallbackProviders
                    .split(',')
                    .map(p => p.trim())
                    .filter(Boolean),
            },
            context: buildContext(),
            preferences: debug ? { debug: true } : undefined,
        };

        try {
            const response = await fetch(`${CONFIG.orchestrator.baseUrl}${CONFIG.orchestrator.endpoints.orchestrate}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.error || err.message || `HTTP ${response.status}`);
            }

            const data = await response.json();
            setHistory(prev => [...prev, {
                role: 'assistant',
                content: data.reply || '(No response)',
                meta: {
                    executionPath: data.execution_path,
                    agents: data.agents_used || [],
                    intent: data.intent,
                    entities: data.entities || [],
                    sources: data.sources || [],
                    agentConversations: data.agent_conversations || {},
                    clarification: data.clarification,
                },
            }]);
        } catch (err) {
            setHistory(prev => [...prev, { role: 'error', content: err.message }]);
        } finally {
            setLoading(false);
        }
    };

    const resetConversation = () => {
        setHistory([]);
        setConversationId(`conv_${Math.random().toString(36).slice(2, 10)}`);
    };

    return (
        <div className="flex flex-col h-full">
            {/* Chat Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 custom-scrollbar">
                {history.length === 0 && (
                    <div className="flex items-center justify-center h-full">
                        {/* Clean empty state - minimal, no text */}
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-neon/20 to-neon/5 flex items-center justify-center">
                            <MessageCircle className="w-8 h-8 text-neon/50" />
                        </div>
                    </div>
                )}

                {history.map((entry, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex gap-3 md:gap-4 ${entry.role === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                        <div className={`w-8 h-8 md:w-9 md:h-9 rounded-full flex items-center justify-center flex-shrink-0 ${
                            entry.role === 'user'
                                ? 'bg-neon text-black'
                                : entry.role === 'error'
                                ? 'bg-red-500 text-white'
                                : 'bg-dark-panel border border-dark-border text-neon'
                        }`}>
                            <MessageSquare className="w-4 h-4 md:w-5 md:h-5" />
                        </div>
                        <div className={`max-w-[85%] md:max-w-[80%] rounded-2xl p-3 md:p-4 ${
                            entry.role === 'user'
                                ? 'bg-neon/10 border border-neon/20 text-white'
                                : entry.role === 'error'
                                ? 'bg-red-500/10 border border-red-500/20 text-red-200'
                                : 'bg-dark-panel border border-dark-border text-gray-200'
                        }`}>
                            <div className="whitespace-pre-wrap text-sm leading-relaxed">{entry.content}</div>
                            {entry.meta && (
                                <div className="mt-3 md:mt-4 space-y-2 md:space-y-3 text-xs text-gray-400">
                                    <div className="flex flex-wrap gap-3">
                                        <span className="flex items-center gap-1 text-neon">
                                            <Sparkles className="w-3 h-3" /> {entry.meta.executionPath || 'fast'} path
                                        </span>
                                        {entry.meta.agents?.length > 0 && (
                                            <span className="flex items-center gap-1">
                                                <PlugZap className="w-3 h-3" /> {entry.meta.agents.join(', ')}
                                            </span>
                                        )}
                                        {entry.meta.clarification && (
                                            <span className="text-yellow-300">Clarification requested</span>
                                        )}
                                    </div>
                                    {entry.meta.intent && (
                                        <div className="flex items-center gap-2 text-gray-300">
                                            <Target className="w-3 h-3 text-neon" />
                                            <span className="font-semibold">{entry.meta.intent.label || 'unknown'}</span>
                                            <span className="text-gray-500">{((entry.meta.intent.confidence || 0) * 100).toFixed(1)}%</span>
                                        </div>
                                    )}
                                    {entry.meta.entities?.length > 0 && (
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2 text-neon">
                                                <Layers className="w-3 h-3" /> Entities
                                            </div>
                                            <div className="space-y-1">
                                                {entry.meta.entities.map((entity, index) => (
                                                    <div key={index} className="flex items-center justify-between bg-black/20 p-2 rounded border border-white/5">
                                                        <span>{entity.type}: "{entity.value}"</span>
                                                        <span>{((entity.confidence || 0) * 100).toFixed(1)}%</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {entry.meta.sources?.length > 0 && (
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2 text-neon">
                                                <Layers className="w-3 h-3" /> Sources
                                            </div>
                                            <div className="space-y-2">
                                                {entry.meta.sources.map((source, index) => (
                                                    <div key={index} className="bg-black/30 rounded border border-white/5 p-2 space-y-1">
                                                        <div className="flex items-center justify-between text-gray-400">
                                                            <span>{source.chunk_id || 'chunk'}</span>
                                                            <span>{((source.relevance_score || 0) * 100).toFixed(1)}%</span>
                                                        </div>
                                                        <div className="text-gray-300 text-xs leading-relaxed">
                                                            {source.preview}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {entry.meta.agentConversations && entry.meta.agentConversations.theory_specialist && (
                                        <div className="text-xs text-gray-500">
                                            Theory conversation: <span className="text-gray-300 font-mono">{entry.meta.agentConversations.theory_specialist}</span>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </motion.div>
                ))}
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

export default OrchestratorChat;
