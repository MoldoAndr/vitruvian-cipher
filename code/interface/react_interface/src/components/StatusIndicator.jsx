import React, { useEffect, useState } from 'react';
import { CONFIG } from '../config';
import { Activity, Wifi, WifiOff } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const StatusDot = ({ name, url }) => {
    const [isOnline, setIsOnline] = useState(false);

    useEffect(() => {
        const checkHealth = async () => {
            try {
                const response = await fetch(url);
                setIsOnline(response.ok);
            } catch (error) {
                setIsOnline(false);
            }
        };

        checkHealth();
        const interval = setInterval(checkHealth, 30000);
        return () => clearInterval(interval);
    }, [url]);

    return (
        <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full transition-all duration-500 ${
                isOnline 
                ? 'bg-neon shadow-[0_0_8px_rgba(0,255,136,0.6)]' 
                : 'bg-red-500/50'
            }`} />
            <span className="text-xs text-gray-400 font-mono uppercase tracking-wider">{name}</span>
        </div>
    );
};

const StatusIndicator = () => {
    const [showExpanded, setShowExpanded] = useState(false);

    return (
        <div
            className="status-indicator-wrapper"
            onMouseEnter={() => setShowExpanded(true)}
            onMouseLeave={() => setShowExpanded(false)}
        >
            {/* Collapsed state - just heartbeat icon */}
            <motion.div
                className="heartbeat-container"
                whileHover={{ scale: 1.2 }}
                transition={{ duration: 0.2 }}
            >
                <div className="heartbeat-icon">
                    <Activity className="w-5 h-5 text-neon animate-pulse" />
                </div>
            </motion.div>

            {/* Expanded state - full status */}
            <AnimatePresence>
                {showExpanded && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.8, y: 10 }}
                        transition={{ duration: 0.8 }}
                        className="status-expanded"
                    >
                        <div className="status-list">
                            <StatusDot
                                name="Password"
                                url={`${CONFIG.passwordChecker.baseUrl}${CONFIG.passwordChecker.endpoints.health}`}
                            />
                            <StatusDot
                                name="Theory"
                                url={`${CONFIG.theorySpecialist.baseUrl}${CONFIG.theorySpecialist.endpoints.health}`}
                            />
                            <StatusDot
                                name="Choice"
                                url={`${CONFIG.choiceMaker.baseUrl}${CONFIG.choiceMaker.endpoints.health}`}
                            />
                            <StatusDot
                                name="Prime"
                                url={`${CONFIG.primeChecker.baseUrl}${CONFIG.primeChecker.endpoints.health}`}
                            />
                            <StatusDot
                                name="Orchestrator"
                                url={`${CONFIG.orchestrator.baseUrl}${CONFIG.orchestrator.endpoints.health}`}
                            />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <style>{`
                .status-indicator-wrapper {
                    position: relative;
                    display: flex;
                    align-items: center;
                }

                .heartbeat-container {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                }

                .heartbeat-icon {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(0, 0, 0, 0.6);
                    backdrop-filter: blur(10px);
                    padding: 13px;
                    border-radius: 50%;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    transition: all 200ms;
                }

                .heartbeat-icon:hover {
                    border-color: rgba(0, 255, 136, 0.3);
                    box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
                }

                .status-expanded {
                    position: absolute;
                    top: 100%;
                    right: 0;
                    margin-top: 12px;
                    background: rgba(0, 0, 0, 0.8);
                    backdrop-filter: blur(20px);
                    padding: 12px 16px;
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
                    z-index: 100;
                    min-width: 200px;
                }

                .status-list {
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    align-items: flex-start;
                }

                @media (max-width: 640px) {
                    .status-expanded {
                        right: -100px;
                        min-width: 250px;
                    }
                }
            `}</style>
        </div>
    );
};

export default StatusIndicator;
