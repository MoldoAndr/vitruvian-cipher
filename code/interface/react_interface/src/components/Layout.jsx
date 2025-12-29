import React, { useState, useEffect } from 'react';
import { Shield, BrainCircuit, FileText, Split, MessageSquare } from 'lucide-react';
import StatusIndicator from './StatusIndicator';
import PasswordChecker from './PasswordChecker';
import CryptoExpert from './CryptoExpert';
import DocumentIngestion from './DocumentIngestion';
import ChoiceMaker from './ChoiceMaker';
import OrchestratorChat from './OrchestratorChat';
import { motion, AnimatePresence } from 'framer-motion';

const Layout = () => {
    const [activeTab, setActiveTab] = useState('password');
    const [inputStates, setInputStates] = useState({
        password: '',
        crypto: '',
        document: '',
        choice: '',
        orchestrator: ''
    });

    const tabs = [
        { id: 'password', label: 'Password Analysis', icon: Shield, component: PasswordChecker },
        { id: 'crypto', label: 'Cryptography Query', icon: BrainCircuit, component: CryptoExpert },
        { id: 'document', label: 'Document Ingestion', icon: FileText, component: DocumentIngestion },
        { id: 'choice', label: 'Choice Maker', icon: Split, component: ChoiceMaker },
        { id: 'orchestrator', label: 'Orchestrator', icon: MessageSquare, component: OrchestratorChat },
    ];

    const updateInputState = (tabId, value) => {
        setInputStates(prev => ({
            ...prev,
            [tabId]: value
        }));
    };

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.ctrlKey) {
                const currentIndex = tabs.findIndex(tab => tab.id === activeTab);
                
                if (e.key === 'ArrowLeft' && currentIndex > 0) {
                    e.preventDefault();
                    setActiveTab(tabs[currentIndex - 1].id);
                } else if (e.key === 'ArrowRight' && currentIndex < tabs.length - 1) {
                    e.preventDefault();
                    setActiveTab(tabs[currentIndex + 1].id);
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [activeTab]);

    return (
        <div className="text-white flex items-start justify-center p-2 sm:p-4 md:p-8 relative z-10">
            <div className="w-full max-w-7xl h-[calc(var(--app-height)-1rem)] sm:h-[calc(var(--app-height)-2rem)] md:h-[90vh] bg-dark-panel border border-dark-border rounded-none sm:rounded-3xl flex flex-col overflow-hidden backdrop-blur-xl shadow-2xl relative">
                {/* Background Glow Effects */}
                <div className="absolute top-0 left-1/4 w-64 h-64 md:w-96 md:h-96 bg-neon/5 rounded-full blur-[100px] pointer-events-none" />
                <div className="absolute bottom-0 right-1/4 w-64 h-64 md:w-96 md:h-96 bg-blue-500/5 rounded-full blur-[100px] pointer-events-none" />

                {/* Header */}
                <header className="px-4 py-4 md:px-8 md:py-6 border-b border-dark-border flex flex-col md:flex-row justify-between items-center gap-4 z-10 bg-dark-bg/50 backdrop-blur-md">
                    <div className="flex items-center gap-3">
                        <h1 className="text-xl md:text-2xl font-bold tracking-tight">vitruvian cipher</h1>
                    </div>
                    <StatusIndicator />
                </header>

                {/* Navigation */}
                <nav className="px-4 pt-4 pb-0 md:px-8 md:pt-6 border-b border-dark-border flex gap-4 md:gap-8 overflow-x-auto custom-scrollbar z-10 bg-dark-bg/30 relative">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`group relative pb-4 px-2 flex items-center gap-2 transition-all duration-1000 whitespace-nowrap ${
                                activeTab === tab.id ? 'text-neon' : 'text-gray-500 hover:text-gray-300'
                            }`}
                        >
                            <tab.icon className="w-4 h-4 flex-shrink-0" />
                            <span className="font-medium text-sm max-w-[200px] md:max-w-0 overflow-hidden transition-all duration-1000 md:group-hover:max-w-[200px]">
                                {tab.label}
                            </span>
                            {activeTab === tab.id && (
                                <motion.div 
                                    layoutId="activeTab"
                                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-neon shadow-[0_0_10px_rgba(0,255,136,0.8)]"
                                />
                            )}
                        </button>
                    ))}
                </nav>

                {/* Content Area */}
                <main className="flex-1 overflow-hidden relative z-0">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeTab}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            transition={{ duration: 0.2 }}
                            className="h-full"
                        >
                            {React.createElement(
                                tabs.find(t => t.id === activeTab).component,
                                {
                                    inputValue: inputStates[activeTab],
                                    onInputChange: (value) => updateInputState(activeTab, value)
                                }
                            )}
                        </motion.div>
                    </AnimatePresence>
                </main>
            </div>
        </div>
    );
};

export default Layout;
