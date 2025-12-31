import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../contexts/AppContext';
import { CONFIG } from '../config';
import InputBar from './InputBar';
import { MessageSquare, Loader2 } from 'lucide-react';
import StatusIndicator from './StatusIndicator';

const MainContent = () => {
    const {
        selectedTool,
        messages,
        addMessage,
        inputValue,
        setInputValue,
        toolSettings,
        toolConversations,
        setToolConversations
    } = useApp();
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef(null);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        if (messages.length > 0) {
            bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages.length]);

    const formatScore = (score) => {
        if (typeof score !== 'number' || Number.isNaN(score)) return 'N/A';
        return `${(score * 100).toFixed(1)}%`;
    };

    const formatIntent = (intent) => {
        if (!intent || typeof intent !== 'object') return ['Intent: None'];
        const label = intent.intent?.label || intent.label || 'Unknown';
        const score = intent.intent?.score ?? intent.score;
        const predictions = intent.all_predictions || intent.intent?.all_predictions || [];
        const lines = [`Intent: ${label} (${formatScore(score)})`];
        if (Array.isArray(predictions) && predictions.length) {
            lines.push('Predictions:');
            predictions.slice(0, 5).forEach((pred) => {
                const predLabel = pred.label || 'Unknown';
                lines.push(`- ${predLabel} (${formatScore(pred.score)})`);
            });
        }
        return lines;
    };

    const formatEntities = (entities) => {
        if (!entities || typeof entities !== 'object') return ['Entities: None'];
        const list = Array.isArray(entities.entities)
            ? entities.entities
            : Array.isArray(entities.entities?.entities)
                ? entities.entities.entities
                : Array.isArray(entities.entities?.entities?.entities)
                    ? entities.entities.entities.entities
                    : [];
        const count = typeof entities.count === 'number' ? entities.count : list.length;
        const lines = [`Entities: ${count}`];
        if (list.length) {
            list.forEach((entity) => {
                const name = entity.entity || 'entity';
                const text = (entity.text || '').trim();
                const score = formatScore(entity.score);
                const range = Number.isFinite(entity.start) && Number.isFinite(entity.end)
                    ? ` [${entity.start}-${entity.end}]`
                    : '';
                lines.push(`- ${name} "${text}" (${score})${range}`);
            });
        }
        return lines;
    };

    const formatChoiceOutput = (payload) => {
        if (!payload || typeof payload !== 'object') {
            return String(payload ?? '');
        }
        const lines = [];
        if (payload.intent) {
            lines.push(...formatIntent(payload.intent));
        }
        if (payload.entities) {
            if (lines.length) lines.push('');
            lines.push(...formatEntities(payload.entities));
        }
        return lines.length ? lines.join('\n') : JSON.stringify(payload, null, 2);
    };

    const buildToolHistory = (toolId, nextMessages) => nextMessages
        .filter((msg) => msg.tool === toolId && (msg.role === 'user' || msg.role === 'assistant'))
        .slice(-8)
        .map((msg) => ({ role: msg.role, content: msg.content }));

    const callJson = async (url, options) => {
        const response = await fetch(url, options);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.detail || data.error || data.message || `HTTP ${response.status}`);
        }
        return data;
    };

    const handleSubmit = async () => {
        if (!inputValue.trim() || loading) return;

        const userMessage = {
            role: 'user',
            content: inputValue.trim(),
            tool: selectedTool,
            timestamp: new Date().toISOString()
        };

        const nextMessages = [...messages, userMessage];
        addMessage(userMessage);
        const submittedInput = inputValue.trim();
        setInputValue('');
        setLoading(true);

        try {
            let responseContent = '';

            if (selectedTool === 'password') {
                const payload = {
                    password: submittedInput,
                    components: toolSettings.password?.components || []
                };

                const data = await callJson(
                    `${CONFIG.passwordChecker.baseUrl}${CONFIG.passwordChecker.endpoints.score}`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    }
                );

                const summary = `Score ${data.normalized_score ?? 'N/A'}/100`;
                const details = Array.isArray(data.components)
                    ? data.components.map((comp) => {
                        const label = comp.label || comp.id || 'Engine';
                        if (comp.success === false) {
                            return `${label}: failed`;
                        }
                        const score = comp.normalized_score ?? comp.score ?? 'N/A';
                        return `${label}: ${score}`;
                    }).join('\n')
                    : '';

                responseContent = details ? `${summary}\n${details}` : summary;
            } else if (selectedTool === 'choice') {
                const mode = toolSettings.choice?.mode || 'both';
                const callChoice = (operation) => callJson(
                    `${CONFIG.choiceMaker.baseUrl}${CONFIG.choiceMaker.endpoints.extract}`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: submittedInput, operation })
                    }
                );

                if (mode === 'both') {
                    const [intentData, entityData] = await Promise.all([
                        callChoice('intent_extraction'),
                        callChoice('entity_extraction')
                    ]);
                    responseContent = formatChoiceOutput({
                        intent: intentData?.result,
                        entities: entityData?.result
                    });
                } else {
                    const data = await callChoice(mode);
                    const result = data?.result ?? data;
                    responseContent = formatChoiceOutput(
                        mode === 'intent_extraction'
                            ? { intent: result }
                            : { entities: result }
                    );
                }
            } else if (selectedTool === 'crypto') {
                const payload = { query: submittedInput };
                if (toolConversations.crypto) {
                    payload.conversation_id = toolConversations.crypto;
                }

                const data = await callJson(
                    `${CONFIG.theorySpecialist.baseUrl}${CONFIG.theorySpecialist.endpoints.generate}`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    }
                );

                if (data.conversation_id && data.conversation_id !== toolConversations.crypto) {
                    setToolConversations((prev) => ({ ...prev, crypto: data.conversation_id }));
                }

                responseContent = data.answer || data.reply || '(No response)';
            } else if (selectedTool === 'orchestrator') {
                const settings = toolSettings.orchestrator || {};
                let conversationId = toolConversations.orchestrator;
                if (!conversationId) {
                    conversationId = `conv_${Math.random().toString(36).slice(2, 10)}`;
                    setToolConversations((prev) => ({ ...prev, orchestrator: conversationId }));
                }

                const history = buildToolHistory('orchestrator', nextMessages);
                const extraKeys = Object.entries(settings.extraKeys || {}).reduce((acc, [key, value]) => {
                    if (value && value.trim()) {
                        acc[key] = value.trim();
                    }
                    return acc;
                }, {});
                const context = {};
                if (history.length) context.history = history;
                if (settings.summary && settings.summary.trim()) {
                    context.summary = settings.summary.trim();
                }
                if (settings.theoryConversationId && settings.theoryConversationId.trim()) {
                    context.state = { theory_conversation_id: settings.theoryConversationId.trim() };
                }

                const payload = {
                    conversation_id: conversationId,
                    text: submittedInput,
                    llm: {
                        provider: settings.provider || 'openai',
                        profile: settings.responderProfile || 'responder',
                        planner_profile: settings.plannerProfile || 'planner',
                        model: settings.modelOverride?.trim() || undefined,
                        planner_model: settings.plannerModelOverride?.trim() || undefined,
                        api_key: settings.apiKey?.trim() || undefined,
                        api_keys: Object.keys(extraKeys).length ? extraKeys : undefined,
                        allow_fallback: Boolean(settings.fallbackEnabled),
                        fallback_providers: settings.fallbackProviders
                            ? settings.fallbackProviders.split(',').map((p) => p.trim()).filter(Boolean)
                            : []
                    },
                    context: Object.keys(context).length ? context : undefined,
                    preferences: settings.debug ? { debug: true } : undefined
                };

                const data = await callJson(
                    `${CONFIG.orchestrator.baseUrl}${CONFIG.orchestrator.endpoints.orchestrate}`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    }
                );

                responseContent = data.reply || '(No response)';
            } else if (selectedTool === 'prime') {
                const payload = { number: submittedInput };

                const data = await callJson(
                    `${CONFIG.primeChecker.baseUrl}${CONFIG.primeChecker.endpoints.isprime}`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    }
                );

                const isPrime = data.is_prime ? 'Prime' : 'Composite';
                const source = data.source ? ` (${data.source})` : '';
                const factors = data.factors && data.factors.length > 0
                    ? `\nFactors: ${data.factors.join(' × ')}`
                    : '';
                const cached = data.cached ? ' [cached]' : '';
                const latency = data.latency_ms ? ` (${data.latency_ms}ms)` : '';

                responseContent = `${isPrime}${source}${latency}${cached}${factors}`;
            } else {
                responseContent = `Response from ${selectedTool} for: "${submittedInput}"`;
            }

            addMessage({
                role: 'assistant',
                content: responseContent,
                tool: selectedTool,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            addMessage({
                role: 'assistant',
                content: `Error: ${error.message}`,
                tool: selectedTool,
                timestamp: new Date().toISOString()
            });
        } finally {
            setLoading(false);
        }
    };

    const hasMessages = messages.length > 0;

    return (
        <div className="main-content">
            {/* Messages Area */}
            <main className={`content-area ${hasMessages ? 'has-messages' : ''}`}>
                <div className="messages-surface">
                    <div className={`messages-container ${hasMessages ? '' : 'is-empty'}`}>
                        {messages.length === 0 ? (
                            <div className="empty-state">
                                <div className="empty-icon">
                                    <MessageSquare className="w-16 h-16 text-neon/30" />
                                </div>
                            </div>
                        ) : (
                            messages.map((msg, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}
                                >
                                    <div className="message-content">
                                        <div className="message-text">{msg.content}</div>
                                        {msg.role === 'assistant' && msg.tool && (
                                            <div className="message-tool">via {msg.tool}</div>
                                        )}
                                    </div>
                                </motion.div>
                            ))
                        )}
                        {loading && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="message assistant-message loading"
                            >
                                <div className="message-content">
                                    <Loader2 className="w-5 h-5 animate-spin text-neon" />
                                </div>
                            </motion.div>
                        )}
                        <div ref={bottomRef} />
                    </div>
                </div>
            </main>

            <div className="status-indicator-rail">
                <StatusIndicator />
            </div>

            {/* Input Bar */}
            <div className={`input-container ${hasMessages ? 'at-bottom' : 'centered'}`}>
                <InputBar onSubmit={handleSubmit} loading={loading} idleGlow={!hasMessages} />
            </div>

            <style>{`
                .main-content {
                    display: flex;
                    flex-direction: column;
                    height: var(--app-height);
                    overflow: visible;
                    position: relative;
                    transition: all 0.45s cubic-bezier(0.22, 1, 0.36, 1);
                }

                .content-area {
                    flex: 1;
                    padding: 0 24px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    overflow: hidden;
                    min-height: 0;
                    transition: padding 0.45s cubic-bezier(0.22, 1, 0.36, 1);
                }

                .content-area:not(.has-messages) {
                    justify-content: center;
                    align-items: center;
                }

                .empty-state {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 100%;
                    height: 100%;
                }

                .empty-icon {
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    background: rgba(0, 255, 136, 0.05);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .messages-surface {
                    width: 75vw;
                    max-width: 100%;
                    flex: 1;
                    min-height: 0;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.55);
                    border-radius: 0;
                    padding: 20px 24px;
                    backdrop-filter: blur(16px);
                    display: flex;
                    transition: width 0.45s cubic-bezier(0.22, 1, 0.36, 1);
                }

                .messages-container {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                    width: 100%;
                    flex: 1;
                    overflow-y: auto;
                    min-height: 0;
                    padding-bottom: 160px;
                    padding-right: 28px;
                    scrollbar-gutter: stable;
                    scrollbar-width: thin;
                    scrollbar-color: rgba(170, 170, 170, 0.7) transparent;
                }

                .messages-container.is-empty {
                    justify-content: center;
                    align-items: center;
                    gap: 0;
                    padding-bottom: 0;
                }

                .message {
                    display: flex;
                    gap: 0;
                    width: 100%;
                    animation: slideIn 0.3s ease;
                    align-items: flex-start;
                }

                @keyframes slideIn {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .user-message {
                    justify-content: flex-end;
                    align-self: flex-end;
                }

                .assistant-message {
                    justify-content: flex-start;
                }

                .message-content {
                    max-width: 75%;
                    width: auto;
                    min-width: 0;
                    background: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 16px;
                    padding: 12px 14px;
                    position: relative;
                }

                .message-text {
                    color: white;
                    font-size: 15px;
                    line-height: 1.5;
                    white-space: pre-wrap;
                    word-break: break-word;
                }

                .user-message .message-content {
                    background: rgba(9, 64, 35, 0.9);
                    border-color: rgba(0, 255, 136, 0.2);
                    margin-left: auto;
                }

                .assistant-message .message-content {
                    background: rgba(255, 255, 255, 0.04);
                    border-color: rgba(0, 255, 136, 0.18);
                    box-shadow: 0 0 14px rgba(0, 255, 136, 0.06);
                    margin-right: auto;
                }

                .assistant-message .message-text {
                    color: #ffffff;
                    font-family: 'Space Mono', 'IBM Plex Mono', 'Menlo', monospace;
                    letter-spacing: 0.2px;
                    font-weight: 500;
                    text-shadow: 0 0 12px rgba(0, 255, 136, 0.22);
                }

                .message-tool {
                    font-size: 10px;
                    color: rgba(255, 255, 255, 0.35);
                    margin-top: 6px;
                    text-transform: none;
                    letter-spacing: 0.2px;
                }

                .assistant-message .message-tool {
                    color: rgba(0, 255, 136, 0.55);
                    letter-spacing: 0.6px;
                    text-transform: uppercase;
                }

                .input-container {
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                    z-index: 5;
                }

                .status-indicator-rail {
                    position: absolute;
                    top: 24px;
                    right: 16px;
                    z-index: 6;
                }

                .input-container.centered {
                    position: absolute;
                    inset: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 0 24px;
                }

                .input-container.at-bottom {
                    position: absolute;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    padding: 16px 24px 24px;
                    display: flex;
                    justify-content: center;
                    align-items: flex-end;
                }

                /* Custom scrollbar */
                .messages-container::-webkit-scrollbar {
                    width: 10px;
                }

                .messages-container::-webkit-scrollbar-track {
                    background: rgba(255, 255, 255, 0.04);
                }

                .messages-container::-webkit-scrollbar-thumb {
                    background: rgba(170, 170, 170, 0.7);
                    border-radius: 8px;
                    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
                }

                .messages-container::-webkit-scrollbar-thumb:hover {
                    background: rgba(190, 190, 190, 0.8);
                }

                /* Mobile adjustments */
                @media (max-width: 767px) {
                    .content-area {
                        padding: 0 16px;
                    }

                    .status-indicator-rail {
                        display: none;
                    }

                    .messages-surface {
                        width: 100%;
                        border-radius: 0;
                        padding: 16px;
                    }

                    .messages-container {
                        padding-bottom: 140px;
                        padding-right: 18px;
                    }

                    .message-content {
                        max-width: 90%;
                    }

                    .input-container.centered {
                        padding: 0 16px;
                    }

                    .input-container.at-bottom {
                        padding: 12px 16px 16px;
                    }
                }
            `}</style>
        </div>
    );
};

export default MainContent;
