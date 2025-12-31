import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { getDefaultToolSettings } from '../toolSettings';

const AppContext = createContext(null);

export const useApp = () => {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useApp must be used within AppProvider');
    }
    return context;
};

export const AppProvider = ({ children }) => {
    // Sidebar state
    const [sidebarExpanded, setSidebarExpanded] = useState(false);
    const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

    // Input value state
    const [inputValue, setInputValue] = useState('');

    // Tool selection state (which tool to use: orchestrator, password, crypto, etc.)
    const [selectedTool, setSelectedTool] = useState('orchestrator');

    // Unified conversation state (shared across all tools)
    const [messages, setMessages] = useState([]);

    // Per-tool settings
    const [toolSettings, setToolSettings] = useState(getDefaultToolSettings);

    // Per-tool conversation state
    const [toolConversations, setToolConversations] = useState(() => ({
        orchestrator: `conv_${Math.random().toString(36).slice(2, 10)}`,
        crypto: null
    }));

    // User state (placeholder for now, no backend)
    const [user] = useState({
        username: 'Vitruvian User',
        avatarUrl: '/logo.png'
    });

    // Sidebar preference from localStorage
    useEffect(() => {
        const savedSidebarState = localStorage.getItem('sidebarExpanded');
        if (savedSidebarState !== null) {
            setSidebarExpanded(JSON.parse(savedSidebarState));
        } else {
            // Default: start collapsed on desktop
            setSidebarExpanded(false);
        }
    }, []);

    // Save sidebar preference to localStorage
    useEffect(() => {
        localStorage.setItem('sidebarExpanded', JSON.stringify(sidebarExpanded));
    }, [sidebarExpanded]);

    // Toggle sidebar
    const toggleSidebar = useCallback(() => {
        setSidebarExpanded(prev => !prev);
    }, []);

    // Toggle mobile sidebar
    const toggleMobileSidebar = useCallback(() => {
        setMobileSidebarOpen(prev => !prev);
    }, []);

    // Set mobile sidebar state
    const setMobileSidebarOpenState = useCallback((value) => {
        setMobileSidebarOpen(value);
    }, []);

    // Start new chat (resets conversation)
    const startNewChat = useCallback(() => {
        setInputValue('');
        setSelectedTool('orchestrator');
        setMessages([]);
        setToolConversations({
            orchestrator: `conv_${Math.random().toString(36).slice(2, 10)}`,
            crypto: null
        });
    }, []);

    // Update input value
    const handleSetInputValue = useCallback((value) => {
        setInputValue(value);
    }, []);

    // Update selected tool
    const handleSetSelectedTool = useCallback((tool) => {
        setSelectedTool(tool);
    }, []);

    // Add message to unified conversation
    const addMessage = useCallback((message) => {
        setMessages(prev => [...prev, message]);
    }, []);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e) => {
            // Ctrl/Cmd + B: Toggle sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                toggleSidebar();
            }
            // Ctrl/Cmd + N: New chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                startNewChat();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [toggleSidebar, startNewChat]);

    const value = {
        // State
        sidebarExpanded,
        mobileSidebarOpen,
        inputValue,
        selectedTool,
        messages,
        toolSettings,
        toolConversations,
        user,

        // Actions
        toggleSidebar,
        toggleMobileSidebar,
        setMobileSidebarOpen: setMobileSidebarOpenState,
        setInputValue: handleSetInputValue,
        setSelectedTool: handleSetSelectedTool,
        addMessage,
        startNewChat,
        setToolSettings,
        setToolConversations
    };

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
};

export default AppContext;
