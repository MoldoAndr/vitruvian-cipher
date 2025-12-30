import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../contexts/AppContext';
import InputBar from './InputBar';
import { MessageSquare, Loader2 } from 'lucide-react';
import StatusIndicator from './StatusIndicator';

const MainContent = () => {
    const { selectedTool, messages, addMessage, inputValue, setInputValue } = useApp();
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef(null);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        if (messages.length > 0) {
            bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages.length]);

    const handleSubmit = async () => {
        if (!inputValue.trim() || loading) return;

        const userMessage = {
            role: 'user',
            content: inputValue.trim(),
            tool: selectedTool,
            timestamp: new Date().toISOString()
        };

        addMessage(userMessage);
        const submittedInput = inputValue;
        setInputValue('');
        setLoading(true);

        // TODO: Call the actual tool API here
        // For now, simulate a response
        setTimeout(() => {
            addMessage({
                role: 'assistant',
                content: `Response from ${selectedTool} for: "${submittedInput}"`,
                tool: selectedTool,
                timestamp: new Date().toISOString()
            });
            setLoading(false);
        }, 1000);
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
                <InputBar onSubmit={handleSubmit} loading={loading} />
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
                    padding-right: 14px;
                    scrollbar-gutter: stable;
                    scrollbar-width: auto;
                    scrollbar-color: #000 #000;
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
                    margin-right: auto;
                }

                .message-tool {
                    font-size: 10px;
                    color: rgba(255, 255, 255, 0.35);
                    margin-top: 6px;
                    text-transform: none;
                    letter-spacing: 0.2px;
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
                    background: #000;
                }

                .messages-container::-webkit-scrollbar-thumb {
                    background: #000;
                    border-radius: 8px;
                    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
                }

                .messages-container::-webkit-scrollbar-thumb:hover {
                    background: #000;
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
                        padding-right: 10px;
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
