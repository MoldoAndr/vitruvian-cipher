import React from 'react';
import { motion } from 'framer-motion';
import { BrainCircuit, Plus, MessageCircle, X, ChevronRight, ChevronLeft } from 'lucide-react';
import { useApp } from '../contexts/AppContext';
import UserProfile from './UserProfile';

const Sidebar = ({ isOpen, setIsOpen, isMobile }) => {
    const { sidebarExpanded, startNewChat, toggleSidebar } = useApp();
    const showLabels = sidebarExpanded || isMobile;
    const isCollapsed = !showLabels;

    const handleNewChat = () => {
        startNewChat();
        if (isMobile) {
            setIsOpen(false);
        }
    };

    return (
        <motion.aside
            className={`sidebar ${isMobile && isOpen ? 'mobile-open' : ''}`}
            initial={false}
            animate={{
                width: isMobile ? 280 : (sidebarExpanded ? 280 : 72),
                x: isMobile ? (isOpen ? 0 : -280) : 0
            }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
            {/* Logo with hover expand/collapse */}
            <div className={`sidebar-header ${!isMobile && !sidebarExpanded ? 'collapsed' : ''}`}>
                {showLabels ? (
                    <div className="logo-container">
                    </div>
                ) : (
                    <button
                        onClick={toggleSidebar}
                        className="expand-button"
                        aria-label="Expand sidebar"
                    >
                        <ChevronRight className="w-6 h-6 text-neon" />
                    </button>
                )}

                {/* Collapse button (when expanded) */}
                {!isMobile && sidebarExpanded && (
                    <button
                        onClick={toggleSidebar}
                        className="collapse-button"
                        aria-label="Collapse sidebar"
                    >
                        <ChevronLeft className="w-6 h-6 text-neon" />
                    </button>
                )}

                {/* Mobile close button */}
                {isMobile && (
                    <button
                        onClick={() => setIsOpen(false)}
                        className="mobile-close-button"
                        aria-label="Close sidebar"
                    >
                        <X className="w-5 h-5" />
                    </button>
                )}
            </div>

            {/* Navigation */}
            <nav className="sidebar-navigation">
                {/* New Chat Button */}
                <button
                    onClick={handleNewChat}
                    className={`new-chat-button ${isCollapsed ? 'collapsed' : ''}`}
                    title={showLabels ? 'New Chat' : ''}
                >
                    <Plus className="w-5 h-5 text-black" />
                    <span
                        className={`nav-label ${showLabels ? '' : 'label-hidden'}`}
                        aria-hidden={!showLabels}
                    >
                        New Chat
                    </span>
                </button>
                {/* Chat History */}
                <button
                    className={`chats-button ${isCollapsed ? 'collapsed' : ''}`}
                    title={showLabels ? 'Chat History' : 'Chats'}
                >
                    <MessageCircle className="w-5 h-5 text-neon" />
                    <span
                        className={`nav-label ${showLabels ? '' : 'label-hidden'}`}
                        aria-hidden={!showLabels}
                    >
                        Chat History
                    </span>
                </button>
            </nav>

            {/* User Profile */}
            <UserProfile isMobile={isMobile} closeSidebar={() => setIsOpen(false)} />

            <style>{`
                .sidebar {
                    display: flex;
                    flex-direction: column;
                    background: rgba(0, 0, 0, 0.6);
                    backdrop-filter: blur(20px);
                    border-right: 1px solid rgba(255, 255, 255, 0.05);
                    height: 100vh;
                    overflow: hidden;
                    position: relative;
                    z-index: 50;
                }

                .sidebar-header {
                    height: 64px;
                    display: flex;
                    align-items: center;
                    justify-content: flex-start;
                    padding: 0 16px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                    flex-shrink: 0;
                    position: relative;
                }

                .sidebar-header.collapsed {
                    justify-content: center;
                }

                .logo-container {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }

                .collapse-button {
                    position: absolute;
                    right: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 32px;
                    height: 32px;
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 10px;
                    cursor: pointer;
                    transition: all 200ms;
                }

                .collapse-button:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border-color: rgba(0, 255, 136, 0.3);
                    color: white;
                }

                .expand-button {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 40px;
                    height: 40px;
                    background: rgba(0, 255, 136, 0.18);
                    border: 1px solid rgba(0, 255, 136, 0.45);
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 200ms;
                }

                .expand-button:hover {
                    background: rgba(0, 255, 136, 0.25);
                    border-color: rgba(0, 255, 136, 0.6);
                    box-shadow: 0 0 12px rgba(0, 255, 136, 0.3);
                    transform: scale(1.1);
                }

                .mobile-close-button {
                    position: absolute;
                    right: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 32px;
                    height: 32px;
                    background: rgba(255, 255, 255, 0.05);
                    border: none;
                    border-radius: 6px;
                    color: white;
                    cursor: pointer;
                    transition: all 200ms;
                }

                .mobile-close-button:hover {
                    background: rgba(255, 255, 255, 0.1);
                }

                .sidebar-navigation {
                    flex: 1;
                    overflow-y: auto;
                    overflow-x: hidden;
                    padding: 12px 8px;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .new-chat-button {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    background: #00ff88;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 200ms;
                    width: 100%;
                    justify-content: center;
                }

                .new-chat-button.collapsed {
                    gap: 0;
                }

                .new-chat-button:hover {
                    background: #00dd77;
                    transform: scale(1.02);
                }

                .chats-button {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    background: rgba(0, 255, 136, 0.1);
                    border: 1px solid rgba(0, 255, 136, 0.3);
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 200ms;
                    width: 100%;
                    justify-content: center;
                }

                .chats-button.collapsed {
                    gap: 0;
                }

                .nav-label {
                    display: inline-block;
                    max-width: 160px;
                    opacity: 1;
                    transform: translateX(0);
                    transition: opacity 260ms ease, transform 260ms ease, max-width 360ms ease;
                    white-space: nowrap;
                    overflow: hidden;
                }

                .nav-label.label-hidden {
                    max-width: 0;
                    opacity: 0;
                    transform: translateX(-8px);
                }

                .new-chat-button .nav-label {
                    color: #000000;
                    font-weight: 600;
                }

                .chats-button .nav-label {
                    color: rgba(255, 255, 255, 0.85);
                    font-weight: 500;
                }

                .chats-button:hover {
                    background: rgba(0, 255, 136, 0.15);
                    border-color: rgba(0, 255, 136, 0.5);
                }

                /* Custom scrollbar */
                .sidebar-navigation::-webkit-scrollbar {
                    width: 4px;
                }

                .sidebar-navigation::-webkit-scrollbar-track {
                    background: transparent;
                }

                .sidebar-navigation::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 2px;
                }

                .sidebar-navigation::-webkit-scrollbar-thumb:hover {
                    background: rgba(255, 255, 255, 0.2);
                }

                /* Mobile styles */
                @media (max-width: 767px) {
                    .sidebar {
                        position: fixed !important;
                        left: 0;
                        top: 0;
                        bottom: 0;
                        width: 280px !important;
                        box-shadow: 0 0 100px rgba(0, 0, 0, 0.8);
                    }
                }
            `}</style>
        </motion.aside>
    );
};

export default Sidebar;
