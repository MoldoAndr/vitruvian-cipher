import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useApp } from '../contexts/AppContext';
import Sidebar from './Sidebar';
import MainContent from './MainContent';

const MainLayout = () => {
    const { sidebarExpanded, mobileSidebarOpen, setMobileSidebarOpen: setMobileOpen } = useApp();
    const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

    useEffect(() => {
        const handleResize = () => {
            const mobile = window.innerWidth < 768;
            setIsMobile(mobile);
            if (!mobile && mobileSidebarOpen) {
                setMobileOpen(false);
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [mobileSidebarOpen, setMobileOpen]);

    // Close sidebar when clicking overlay
    const handleOverlayClick = () => {
        setMobileOpen(false);
    };

    return (
        <div className={`main-layout ${sidebarExpanded ? 'sidebar-expanded' : 'sidebar-collapsed'}`}>
            {/* Mobile Sidebar Overlay */}
            <AnimatePresence>
                {isMobile && mobileSidebarOpen && (
                    <motion.div
                        className="sidebar-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.45 }}
                        onClick={handleOverlayClick}
                    />
                )}
            </AnimatePresence>

            {/* Sidebar */}
            <Sidebar isOpen={mobileSidebarOpen} setIsOpen={setMobileOpen} isMobile={isMobile} />

            {/* Main Content Area */}
            <MainContent />

            <style>{`
                .main-layout {
                    display: grid;
                    grid-template-columns: var(--sidebar-width, 72px) 1fr;
                    height: var(--app-height);
                    overflow: hidden;
                    position: relative;
                    z-index: 10;
                    transition: grid-template-columns 0.5s cubic-bezier(0.22, 1, 0.36, 1);
                }

                .sidebar-collapsed {
                    --sidebar-width: 72px;
                }

                .sidebar-expanded {
                    --sidebar-width: 280px;
                }

                .sidebar-overlay {
                    position: fixed;
                    inset: 0;
                    background: rgba(0, 0, 0, 0.5);
                    z-index: 90;
                    backdrop-filter: blur(4px);
                }

                /* Mobile layout */
                @media (max-width: 767px) {
                    .main-layout {
                        grid-template-columns: 1fr;
                    }
                }
            `}</style>
        </div>
    );
};

export default MainLayout;
