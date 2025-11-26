import React, { useState, useRef, useEffect } from 'react';
import { CONFIG } from '../config';
import { FileText, Upload, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const DocumentIngestion = () => {
    const [inputPath, setInputPath] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const [docType, setDocType] = useState('pdf');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null);
    const [history, setHistory] = useState([]);
    const fileInputRef = useRef(null);
    const bottomRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [status, loading, history]);

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            setSelectedFile(file);
            setInputPath('');
            
            // Auto-detect type
            if (file.name.endsWith('.pdf')) setDocType('pdf');
            else if (file.name.endsWith('.md')) setDocType('markdown');
            else setDocType('text');
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file) {
            setSelectedFile(file);
            setInputPath('');
            if (file.name.endsWith('.pdf')) setDocType('pdf');
            else if (file.name.endsWith('.md')) setDocType('markdown');
            else setDocType('text');
        }
    };

    const handleIngest = async () => {
        if (!selectedFile && !inputPath) return;
        
        setLoading(true);
        setStatus(null);
        setInputPath('');
        const descriptor = selectedFile ? `Upload: ${selectedFile.name}` : `Path: ${inputPath}`;
        setHistory(prev => [...prev, { role: 'user', content: descriptor }]);
        scrollToBottom();
        inputRef.current?.focus();

        try {
            const payload = {
                document_path: selectedFile ? `/tmp/${selectedFile.name}` : inputPath,
                document_type: docType === 'markdown' ? 'md' : docType
            };

            const response = await fetch(`${CONFIG.theorySpecialist.baseUrl}${CONFIG.theorySpecialist.endpoints.ingest}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                setStatus({ type: 'success', message: data.message, details: data });
                setSelectedFile(null);
                setInputPath('');
                setHistory(prev => [...prev, { role: 'system', content: data.message }]);
            } else {
                const err = await response.json();
                setStatus({ type: 'error', message: err.detail || 'Ingestion failed' });
                setHistory(prev => [...prev, { role: 'error', content: err.detail || 'Ingestion failed' }]);
            }
        } catch (e) {
            setStatus({ type: 'error', message: e.message });
            setHistory(prev => [...prev, { role: 'error', content: e.message }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full p-6 overflow-y-auto custom-scrollbar">
            <div className="max-w-2xl mx-auto w-full space-y-8">
                {history.length === 0 && (
                    <div className="text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-neon-dim mb-4">
                            <FileText className="w-8 h-8 text-neon" />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Document Ingestion</h2>
                        <p className="text-gray-400">Add documents to the knowledge base for enhanced analysis.</p>
                    </div>
                )}

                {history.length > 0 && (
                    <div className="space-y-3">
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
                                    <FileText className="w-5 h-5" />
                                </div>
                                <div className={`max-w-[85%] rounded-2xl p-3 text-sm ${
                                    entry.role === 'user'
                                    ? 'bg-neon/10 border border-neon/20 text-white'
                                    : entry.role === 'error'
                                    ? 'bg-red-500/10 border border-red-500/20 text-red-200'
                                    : 'bg-dark-panel border border-dark-border text-gray-200'
                                }`}>
                                    <div className="whitespace-pre-wrap leading-relaxed break-words">{entry.content}</div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}

                <div className="flex justify-center gap-4">
                    {['pdf', 'markdown', 'text'].map(type => (
                        <button
                            key={type}
                            onClick={() => setDocType(type)}
                            className={`px-6 py-2 rounded-full text-sm font-medium transition-all duration-300 border ${
                                docType === type
                                ? 'bg-neon-dim border-neon text-neon shadow-[0_0_10px_rgba(0,255,136,0.2)]'
                                : 'bg-dark-panel border-dark-border text-gray-500 hover:border-gray-500'
                            }`}
                        >
                            {type.toUpperCase()}
                        </button>
                    ))}
                </div>

                <div 
                    className={`border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-300 cursor-pointer ${
                        selectedFile 
                        ? 'border-neon bg-neon-dim' 
                        : 'border-dark-border hover:border-neon/50 hover:bg-dark-panel'
                    }`}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                >
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        className="hidden" 
                        onChange={handleFileSelect}
                        accept=".pdf,.md,.txt"
                    />
                    
                    {selectedFile ? (
                        <div className="flex items-center justify-center gap-4">
                            <FileText className="w-8 h-8 text-neon" />
                            <div className="text-left">
                                <div className="text-white font-medium">{selectedFile.name}</div>
                                <div className="text-xs text-neon">{(selectedFile.size / 1024).toFixed(2)} KB</div>
                            </div>
                            <button 
                                onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                                className="p-2 hover:bg-black/20 rounded-full transition-colors"
                            >
                                <X className="w-5 h-5 text-white" />
                            </button>
                        </div>
                    ) : (
                        <>
                            <Upload className="w-10 h-10 text-gray-500 mx-auto mb-4" />
                            <div className="text-gray-300 font-medium mb-2">Click to upload or drag and drop</div>
                            <div className="text-sm text-gray-500">PDF, Markdown, or Text files</div>
                        </>
                    )}
                </div>

                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-dark-border"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-4 bg-dark-bg text-gray-500">OR ENTER PATH</span>
                    </div>
                </div>

                <div className="flex gap-4">
                    <input
                        ref={inputRef}
                        type="text"
                        value={inputPath}
                        onChange={(e) => { setInputPath(e.target.value); setSelectedFile(null); }}
                        placeholder="Enter document path or URL..."
                        className="flex-1 bg-dark-panel border border-dark-border rounded-xl px-5 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-neon/50 focus:ring-1 focus:ring-neon/50 transition-all"
                    />
                    <button
                        onClick={handleIngest}
                        disabled={loading || (!selectedFile && !inputPath)}
                        className="bg-neon text-black font-bold rounded-xl px-8 hover:bg-[#00dd77] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center gap-2"
                    >
                        {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                        INGEST
                    </button>
                </div>

                <AnimatePresence>
                    {status && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className={`p-4 rounded-xl border flex items-start gap-3 ${
                                status.type === 'success' 
                                ? 'bg-neon-dim border-neon/30 text-neon' 
                                : 'bg-red-500/10 border-red-500/30 text-red-400'
                            }`}
                        >
                            {status.type === 'success' ? <CheckCircle className="w-5 h-5 mt-0.5" /> : <AlertCircle className="w-5 h-5 mt-0.5" />}
                            <div>
                                <div className="font-medium">{status.message}</div>
                                {status.details && (
                                    <div className="text-xs opacity-70 mt-1">
                                        ID: {status.details.document_id || 'N/A'}
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

export default DocumentIngestion;
