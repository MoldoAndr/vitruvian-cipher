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
                    <div className="text-center py-8 md:py-12">
                        <div className="inline-flex items-center justify-center w-12 h-12 md:w-16 md:h-16 rounded-full bg-neon-dim mb-4">
                            <MessageCircle className="w-6 h-6 md:w-8 md:h-8 text-neon" />
                        </div>
                        <h2 className="text-xl md:text-2xl font-bold text-white mb-2">Orchestrator Console</h2>
                        <p className="text-gray-400 max-w-md mx-auto text-sm md:text-base">
                            Talk naturally. The orchestrator extracts intent/entities, routes to agents, and responds using your chosen LLM.
                        </p>
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

            {/* Input and Controls Area */}
            <div className="border-t border-dark-border bg-dark-bg/80 backdrop-blur-md">
                {/* Quick Config Bar */}
                <div className="px-4 py-3 border-b border-dark-border/50">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                            <select
                                value={provider}
                                onChange={(e) => setProvider(e.target.value)}
                                className="bg-dark-panel border border-dark-border text-xs md:text-sm rounded-lg px-2 py-1.5 md:px-3 md:py-2 min-w-0"
                            >
                                {PROVIDERS.map(item => (
                                    <option key={item.id} value={item.id}>{item.label}</option>
                                ))}
                            </select>
                            <input
                                type="password"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="API key"
                                className="bg-dark-panel border border-dark-border rounded-lg px-2 py-1.5 md:px-4 md:py-2 text-xs md:text-sm w-24 md:w-auto flex-1"
                            />
                        </div>
                        <button
                            onClick={() => setShowConfig(!showConfig)}
                            className="p-2 rounded-lg bg-dark-panel border border-dark-border text-gray-400 hover:text-neon hover:border-neon/50 transition-all"
                        >
                            <Settings className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Collapsible Configuration */}
                <AnimatePresence>
                    {showConfig && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="border-b border-dark-border/50 overflow-hidden"
                        >
                            <div className="p-4 space-y-4">
                                {/* Basic Configuration */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                    <div className="space-y-3">
                                        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                                            <label className="text-xs uppercase tracking-wider text-gray-500 whitespace-nowrap">Models</label>
                                            <div className="flex gap-2 flex-1">
                                                <input
                                                    value={modelOverride}
                                                    onChange={(e) => setModelOverride(e.target.value)}
                                                    placeholder="Responder model"
                                                    list="model-options"
                                                    className="flex-1 bg-dark-panel border border-dark-border rounded-lg px-2 py-1.5 text-xs"
                                                />
                                                <input
                                                    value={plannerModelOverride}
                                                    onChange={(e) => setPlannerModelOverride(e.target.value)}
                                                    placeholder="Planner model"
                                                    list="model-options"
                                                    className="flex-1 bg-dark-panel border border-dark-border rounded-lg px-2 py-1.5 text-xs"
                                                />
                                            </div>
                                        </div>
                                        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                                            <label className="text-xs uppercase tracking-wider text-gray-500 whitespace-nowrap">Profiles</label>
                                            <div className="flex gap-2 flex-1">
                                                <input
                                                    value={responderProfile}
                                                    onChange={(e) => setResponderProfile(e.target.value)}
                                                    placeholder="Responder"
                                                    className="flex-1 bg-dark-panel border border-dark-border rounded-lg px-2 py-1.5 text-xs"
                                                />
                                                <input
                                                    value={plannerProfile}
                                                    onChange={(e) => setPlannerProfile(e.target.value)}
                                                    placeholder="Planner"
                                                    className="flex-1 bg-dark-panel border border-dark-border rounded-lg px-2 py-1.5 text-xs"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        <textarea
                                            value={summary}
                                            onChange={(e) => setSummary(e.target.value)}
                                            placeholder="Conversation summary (optional)"
                                            className="w-full bg-dark-panel border border-dark-border rounded-lg px-3 py-2 text-xs h-20 resize-none"
                                        />
                                        <input
                                            value={theoryConversationId}
                                            onChange={(e) => setTheoryConversationId(e.target.value)}
                                            placeholder="Theory conversation ID (optional)"
                                            className="w-full bg-dark-panel border border-dark-border rounded-lg px-3 py-2 text-xs"
                                        />
                                    </div>
                                </div>

                                {/* Advanced Options Toggle */}
                                <button
                                    onClick={() => setShowAdvanced(!showAdvanced)}
                                    className="flex items-center gap-2 text-xs text-gray-400 hover:text-neon transition-colors"
                                >
                                    {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                    Advanced Options
                                </button>

                                {/* Advanced Options */}
                                <AnimatePresence>
                                    {showAdvanced && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            transition={{ duration: 0.2 }}
                                            className="space-y-4 overflow-hidden"
                                        >
                                            <div className="flex flex-wrap items-center gap-3 text-xs">
                                                <label className="flex items-center gap-2">
                                                    <input
                                                        type="checkbox"
                                                        checked={fallbackEnabled}
                                                        onChange={(e) => setFallbackEnabled(e.target.checked)}
                                                    />
                                                    <span className="text-gray-400">Fallback</span>
                                                </label>
                                                {fallbackEnabled && (
                                                    <input
                                                        value={fallbackProviders}
                                                        onChange={(e) => setFallbackProviders(e.target.value)}
                                                        placeholder="Providers (comma-separated)"
                                                        className="bg-dark-panel border border-dark-border rounded-lg px-2 py-1.5 text-xs flex-1 min-w-0"
                                                    />
                                                )}
                                                <label className="flex items-center gap-2">
                                                    <input
                                                        type="checkbox"
                                                        checked={debug}
                                                        onChange={(e) => setDebug(e.target.checked)}
                                                    />
                                                    <span className="text-gray-400">Debug</span>
                                                </label>
                                            </div>

                                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
                                                {Object.keys(extraKeys).map(key => (
                                                    <input
                                                        key={key}
                                                        type="password"
                                                        value={extraKeys[key]}
                                                        onChange={(e) => setExtraKeys(prev => ({ ...prev, [key]: e.target.value }))}
                                                        placeholder={`${key} key`}
                                                        className="bg-dark-panel border border-dark-border rounded-lg px-2 py-1.5 text-xs"
                                                    />
                                                ))}
                                            </div>

                                            <div className="flex items-center gap-2 text-xs text-gray-500">
                                                <span>Conversation:</span>
                                                <span className="text-gray-300 font-mono">{conversationId}</span>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Message Input */}
                <div className="p-4">
                    <div className="flex gap-2 md:gap-4">
                        <textarea
                            value={input}
                            onChange={(e) => {
                            setInput(e.target.value);
                            if (onInputChange) onInputChange(e.target.value);
                        }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                            placeholder="Send a message to the orchestrator..."
                            className="flex-1 bg-dark-bg border border-dark-border rounded-xl px-3 md:px-5 py-3 md:py-4 text-white placeholder-gray-600 focus:outline-none focus:border-neon/50 focus:ring-1 focus:ring-neon/50 transition-all resize-none h-12 md:h-[60px] custom-scrollbar text-sm"
                        />
                        <button
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            className="bg-neon text-black font-bold rounded-xl px-3 md:px-6 hover:bg-[#00dd77] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center min-w-[48px] md:min-w-[60px]"
                        >
                            {loading ? <Loader2 className="w-4 h-4 md:w-6 md:h-6 animate-spin" /> : <Send className="w-4 h-4 md:w-6 md:h-6" />}
                        </button>
                        <button
                            onClick={resetConversation}
                            className="bg-dark-panel border border-dark-border text-gray-300 rounded-xl px-2 md:px-4 hover:border-neon/50 transition-all duration-300 flex items-center justify-center"
                        >
                            <RefreshCcw className="w-3 h-3 md:w-4 md:h-4" />
                        </button>
                    </div>
                </div>
            </div>

            <datalist id="model-options">
                {MODEL_OPTIONS.map((model) => (
                    <option key={model} value={model} />
                ))}
            </datalist>
        </div>
    );
};

export default OrchestratorChat;
