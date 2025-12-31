import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, MoreVertical, Settings, Languages, HelpCircle, BookOpen, LogOut } from 'lucide-react';
import { useApp } from '../contexts/AppContext';

const UserProfile = ({ isMobile = false, closeSidebar }) => {
    const { sidebarExpanded, user } = useApp();
    const showDetails = sidebarExpanded || isMobile;
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef(null);

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setMenuOpen(false);
            }
        };

        if (menuOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [menuOpen]);

    const menuItems = [
        { icon: Settings, label: 'Settings', onClick: () => console.log('Settings') },
        { icon: Languages, label: 'Language', onClick: () => console.log('Language') },
        { icon: HelpCircle, label: 'Get Help', onClick: () => console.log('Get Help') },
        { icon: BookOpen, label: 'Learn More', onClick: () => console.log('Learn More') },
        { icon: LogOut, label: 'Log Out', onClick: () => console.log('Log Out') },
    ];

    // Generate avatar with initials
    const initials = user.username
        .split(' ')
        .map(word => word[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);

    return (
        <div className="user-profile-container" ref={menuRef}>
            <div
                className={`user-profile ${(sidebarExpanded || isMobile) ? 'expanded' : 'collapsed'}`}
                onClick={() => showDetails && setMenuOpen(!menuOpen)}
            >
                {/* Avatar */}
                <div className="user-avatar">
                    {user.avatarUrl ? (
                        <img src={user.avatarUrl} alt={user.username} className="avatar-image" />
                    ) : (
                        <div className="avatar-placeholder">
                            {initials}
                        </div>
                    )}
                </div>

                {/* Username */}
                <span
                    className={`username ${showDetails ? '' : 'is-hidden'}`}
                    aria-hidden={!showDetails}
                >
                    {user.username}
                </span>

                {/* Three dots */}
                <div className={`menu-dots ${showDetails ? '' : 'is-hidden'}`} aria-hidden={!showDetails}>
                    <MoreVertical className="w-4 h-4 text-gray-400" />
                </div>
            </div>

            {/* Dropdown Menu */}
            <AnimatePresence>
                {menuOpen && (sidebarExpanded || isMobile) && (
                    <motion.div
                        className="user-menu"
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        transition={{ duration: 0.2, ease: 'easeOut' }}
                    >
                        {menuItems.map((item, index) => (
                            <button
                                key={index}
                                onClick={() => {
                                    item.onClick();
                                    setMenuOpen(false);
                                }}
                                className="menu-item"
                            >
                                <item.icon className="w-4 h-4 text-gray-400" />
                                <span>{item.label}</span>
                            </button>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            <style>{`
                .user-profile-container {
                    position: relative;
                    padding: 12px;
                    border-top: 1px solid rgba(255, 255, 255, 0.05);
                }

                .user-profile {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 8px;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 200ms;
                }

                .user-profile:hover {
                    background: rgba(255, 255, 255, 0.05);
                }

                .user-profile.collapsed {
                    justify-content: center;
                    gap: 0;
                }

                .user-avatar {
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    overflow: hidden;
                    flex-shrink: 0;
                    background: linear-gradient(135deg, #00ff88 0%, #00aa55 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .avatar-image {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }

                .avatar-placeholder {
                    color: #000000;
                    font-size: 14px;
                    font-weight: 600;
                }

                .username {
                    flex: 1;
                    font-size: 14px;
                    font-weight: 500;
                    color: #ffffff;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    max-width: 180px;
                    transition: opacity 260ms ease, transform 260ms ease, max-width 360ms ease;
                }

                .username.is-hidden {
                    max-width: 0;
                    opacity: 0;
                    transform: translateX(-8px);
                }

                .menu-dots {
                    flex-shrink: 0;
                    transition: opacity 200ms ease, transform 200ms ease, width 200ms ease;
                    width: 18px;
                    display: flex;
                    justify-content: center;
                }

                .menu-dots.is-hidden {
                    opacity: 0;
                    transform: translateX(-6px);
                    width: 0;
                }

                .user-menu {
                    position: absolute;
                    bottom: calc(100% + 8px);
                    left: 12px;
                    background: rgba(20, 20, 20, 0.95);
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: 8px;
                    min-width: 200px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
                    z-index: 100;
                }

                .menu-item {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 10px 12px;
                    border-radius: 8px;
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 14px;
                    transition: all 150ms;
                    cursor: pointer;
                    background: transparent;
                    border: none;
                    width: 100%;
                    text-align: left;
                }

                .menu-item:hover {
                    background: rgba(255, 255, 255, 0.05);
                    color: #ffffff;
                }

                .menu-item:hover svg {
                    color: #00ff88;
                }
            `}</style>
        </div>
    );
};

export default UserProfile;
