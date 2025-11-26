import React, { useState } from 'react';
import { Shield, BrainCircuit, FileText, Split } from 'lucide-react';
import StatusIndicator from './StatusIndicator';
import PasswordChecker from './PasswordChecker';
import CryptoExpert from './CryptoExpert';
import DocumentIngestion from './DocumentIngestion';
import ChoiceMaker from './ChoiceMaker';
import { motion, AnimatePresence } from 'framer-motion';

const Layout = () => {
    const [activeTab, setActiveTab] = useState('password');

    const tabs = [
        { id: 'password', label: 'Password Analysis', icon: Shield, component: PasswordChecker },
        { id: 'crypto', label: 'Cryptography Query', icon: BrainCircuit, component: CryptoExpert },
        { id: 'document', label: 'Document Ingestion', icon: FileText, component: DocumentIngestion },
        { id: 'choice', label: 'Choice Maker', icon: Split, component: ChoiceMaker },
    ];

    return (
        <div className="min-h-screen bg-black text-white flex items-start justify-center p-4 md:p-8">
            <div className="w-full max-w-7xl h-[90vh] bg-dark-panel border border-dark-border rounded-3xl flex flex-col overflow-hidden backdrop-blur-xl shadow-2xl relative">
                {/* Background Glow Effects */}
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-neon/5 rounded-full blur-[100px] pointer-events-none" />
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-[100px] pointer-events-none" />

                {/* Header */}
                <header className="px-8 py-6 border-b border-dark-border flex flex-col md:flex-row justify-between items-center gap-4 z-10 bg-dark-bg/50 backdrop-blur-md">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-neon flex items-center justify-center shadow-[0_0_15px_rgba(0,255,136,0.4)]">
                            <Shield className="w-6 h-6 text-black" />
                        </div>
                        <h1 className="text-2xl font-bold tracking-tight">Agent Interface <span className="text-neon">v2.0</span></h1>
                    </div>
                    <StatusIndicator />
                </header>

                {/* Navigation */}
                <nav className="px-8 pt-6 pb-0 border-b border-dark-border flex gap-8 overflow-x-auto custom-scrollbar z-10 bg-dark-bg/30">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`pb-4 px-2 relative flex items-center gap-2 transition-colors duration-300 whitespace-nowrap ${
                                activeTab === tab.id ? 'text-neon' : 'text-gray-500 hover:text-gray-300'
                            }`}
                        >
                            <tab.icon className="w-4 h-4" />
                            <span className="font-medium text-sm">{tab.label}</span>
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
                            {React.createElement(tabs.find(t => t.id === activeTab).component)}
                        </motion.div>
                    </AnimatePresence>
                </main>
            </div>
        </div>
    );
};

export default Layout;
