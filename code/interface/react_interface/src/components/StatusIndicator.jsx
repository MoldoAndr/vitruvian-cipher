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
    const [isHovered, setIsHovered] = useState(false);

    return (
        <div 
            className="relative"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Collapsed state - just heartbeat icon */}
            <div className="flex items-center justify-center bg-dark-panel px-3 py-2 rounded-full border border-dark-border backdrop-blur-sm">
                <Activity className="w-4 h-4 text-neon animate-pulse" />
            </div>
            
            {/* Expanded state - full status */}
            <AnimatePresence>
                {isHovered && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8, y: -10 }}
                        animate={{ opacity: 1, scale: 1, y: -40, x: -50 }}
                        exit={{ opacity: 0, scale: 0.8, y: -10 }}
                        transition={{ duration: 0.5 }}
                        className="absolute top-full mt-2 right-0 bg-dark-panel px-4 py-2 rounded-full border border-dark-border backdrop-blur-sm shadow-lg opacity-100"
                    >
                        <div className="flex gap-6 items-center">
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
                                name="Orchestrator" 
                                url={`${CONFIG.orchestrator.baseUrl}${CONFIG.orchestrator.endpoints.health}`} 
                            />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default StatusIndicator;
