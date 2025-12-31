import React, { useState, useEffect } from 'react';
import { Menu } from 'lucide-react';
import { useApp } from '../contexts/AppContext';
import StatusIndicator from './StatusIndicator';

const ContentHeader = () => {
    const { toggleMobileSidebar } = useApp();
    const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

    useEffect(() => {
        const handleResize = () => {
            setIsMobile(window.innerWidth < 768);
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <header className="content-header">
            <div className="header-left">
                {/* Mobile menu button */}
                {isMobile && (
                    <button
                        onClick={toggleMobileSidebar}
                        className="mobile-menu-button"
                        aria-label="Toggle sidebar"
                    >
                        <Menu className="w-5 h-5" />
                    </button>
                )}
                <h1 className="content-title">Vitruvian-Cipher</h1>
            </div>
            <StatusIndicator />

            <style>{`
                .content-header {
                    height: 64px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 0 24px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                    background: rgba(0, 0, 0, 0.3);
                    backdrop-filter: blur(10px);
                    flex-shrink: 0;
                }

                .header-left {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                }

                .mobile-menu-button {
                    display: none;
                    align-items: center;
                    justify-content: center;
                    width: 40px;
                    height: 40px;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    color: white;
                    cursor: pointer;
                    transition: all 200ms;
                }

                .mobile-menu-button:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border-color: rgba(0, 255, 136, 0.3);
                }

                .content-title {
                    font-size: 24px;
                    font-weight: 600;
                    letter-spacing: -0.02em;
                    color: #ffffff;
                    margin: 0;
                }

                /* Mobile adjustments */
                @media (max-width: 767px) {
                    .content-header {
                        height: 56px;
                        padding: 0 16px;
                    }

                    .mobile-menu-button {
                        display: flex;
                    }

                    .content-title {
                        font-size: 18px;
                    }
                }

                @media (max-width: 480px) {
                    .content-title {
                        font-size: 16px;
                    }
                }
            `}</style>
        </header>
    );
};

export default ContentHeader;
