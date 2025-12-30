import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, ChevronDown, Settings } from "lucide-react";
import { useApp } from "../contexts/AppContext";
import { CONFIG } from "../config";

const TOOLS = [
  { id: "orchestrator", label: "Orchestrator" },
  { id: "password", label: "Password" },
  { id: "crypto", label: "Crypto" },
  { id: "choice", label: "Choice" },
];

const TOOL_CONFIG = {
  orchestrator: {
    baseUrl: CONFIG.orchestrator.baseUrl,
    endpoint: CONFIG.orchestrator.endpoints.orchestrate,
  },
  password: {
    baseUrl: CONFIG.passwordChecker.baseUrl,
    endpoint: CONFIG.passwordChecker.endpoints.score,
  },
  crypto: {
    baseUrl: CONFIG.theorySpecialist.baseUrl,
    endpoint: CONFIG.theorySpecialist.endpoints.generate,
  },
  choice: {
    baseUrl: CONFIG.choiceMaker.baseUrl,
    endpoint: CONFIG.choiceMaker.endpoints.extract,
  },
};

const InputBar = ({ onSubmit, loading: externalLoading }) => {
  const { inputValue, setInputValue, selectedTool, setSelectedTool } = useApp();
  const [toolDropdownOpen, setToolDropdownOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const textareaRef = useRef(null);
  const containerRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const newHeight = Math.min(
        Math.max(textareaRef.current.scrollHeight, 72),
        180,
      );
      textareaRef.current.style.height = newHeight + "px";
    }
  }, [inputValue]);

  const handleSubmit = () => {
    if (onSubmit && inputValue.trim() && !externalLoading) {
      onSubmit();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const currentTool = TOOLS.find((t) => t.id === selectedTool) || TOOLS[0];
  const currentToolConfig = TOOL_CONFIG[selectedTool] || {};

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target)
      ) {
        setToolDropdownOpen(false);
        setSettingsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="input-bar-wrapper" ref={containerRef}>
      <div className={`input-bar ${inputValue ? "focused" : ""}`}>
        {/* Text Input - Clean and centered */}
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter for newline
Ctrl+Enter to submit"
            className="text-input"
            rows={1}
            disabled={externalLoading}
          />
        </div>

        {/* Tool Settings */}
        <div className="tool-settings-wrapper">
          <button
            className="tool-settings-button"
            onClick={() => {
              setSettingsOpen(!settingsOpen);
              setToolDropdownOpen(false);
            }}
            aria-label="Tool settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          <AnimatePresence>
            {settingsOpen && (
              <motion.div
                className="tool-settings-panel"
                initial={{ opacity: 0, y: 8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.96 }}
                transition={{ duration: 0.2 }}
              >
                <div className="tool-settings-title">Advanced settings</div>
                <div className="tool-settings-row">
                  <span className="tool-settings-label">Tool</span>
                  <span className="tool-settings-value">{currentTool.label}</span>
                </div>
                <div className="tool-settings-row">
                  <span className="tool-settings-label">Base URL</span>
                  <span className="tool-settings-value">
                    {currentToolConfig.baseUrl || "Not set"}
                  </span>
                </div>
                <div className="tool-settings-row">
                  <span className="tool-settings-label">Endpoint</span>
                  <span className="tool-settings-value">
                    {currentToolConfig.endpoint || "Not set"}
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Actions */}
        <div className="input-actions">
          <div className="tool-selector-wrapper">
            <button
              className="tool-selector-button"
              onClick={() => {
                setToolDropdownOpen(!toolDropdownOpen);
                setSettingsOpen(false);
              }}
            >
              <span className="tool-label">{currentTool.label}</span>
              <ChevronDown
                className={`w-3 h-3 transition-transform ${toolDropdownOpen ? "rotate-180" : ""}`}
              />
            </button>

            {/* Tool Dropdown */}
            <AnimatePresence>
              {toolDropdownOpen && (
                <motion.div
                  className="tool-dropdown"
                  initial={{ opacity: 0, y: 8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.98 }}
                  transition={{ duration: 0.2 }}
                >
                  {TOOLS.map((tool) => (
                    <button
                      key={tool.id}
                      onClick={() => {
                        setSelectedTool(tool.id);
                        setToolDropdownOpen(false);
                      }}
                      className={`tool-option ${selectedTool === tool.id ? "active" : ""}`}
                    >
                      <span className="tool-option-label">{tool.label}</span>
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <button
            onClick={handleSubmit}
            disabled={externalLoading || !inputValue.trim()}
            className="send-button"
          >
            {externalLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>


        </div>
      </div>

      <style>{`
                .input-bar-wrapper {
                    width: 100%;
                    max-width: 760px;
                }

                .input-bar {
                    position: relative;
                    display: block;
                    background: #000000;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 22px;
                    padding: 16px 18px 20px;
                    transition: all 200ms ease;
                    box-shadow: 0 0 18px rgba(0, 255, 136, 0.18);
                }

                .input-bar:hover {
                    border-color: rgba(255, 255, 255, 0.12);
                    box-shadow: 0 0 22px rgba(0, 255, 136, 0.22);
                }

                .input-bar.focused {
                    border-color: rgba(0, 255, 136, 0.4);
                    box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.08),
                        0 0 24px rgba(0, 255, 136, 0.25);
                }

                .input-wrapper {
                    min-height: 72px;
                    max-height: 180px;
                    display: flex;
                    align-items: center;
                }

                .text-input {
                    width: 100%;
                    min-height: 72px;
                    max-height: 180px;
                    background: transparent;
                    border: none;
                    color: white;
                    font-size: 17px;
                    font-family: 'Inter', system-ui, sans-serif;
                    line-height: 1.5;
                    resize: none;
                    overflow-y: auto;
                    padding: 4px 170px 48px 52px;
                }

                .text-input::placeholder {
                    color: rgba(255, 255, 255, 0.25);
                }

                .text-input:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .text-input:focus {
                    outline: none;
                }

                .text-input::-webkit-scrollbar {
                    width: 4px;
                }

                .text-input::-webkit-scrollbar-track {
                    background: transparent;
                }

                .text-input::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 2px;
                }

                .input-actions {
                    position: absolute;
                    right: 12px;
                    bottom: 12px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .send-button {
                    width: 38px;
                    height: 38px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 11px;
                    background: #00ff88;
                    border: none;
                    color: black;
                    cursor: pointer;
                    transition: all 200ms ease;
                    flex-shrink: 0;
                }

                .send-button:hover:not(:disabled) {
                    background: #00dd77;
                    transform: translateY(-1px);
                    box-shadow: 0 3px 12px rgba(0, 255, 136, 0.35);
                }

                .send-button:active:not(:disabled) {
                    transform: translateY(0);
                }

                .send-button:disabled {
                    opacity: 0.4;
                    cursor: not-allowed;
                    transform: none;
                }

                .tool-settings-wrapper {
                    position: absolute;
                    left: 12px;
                    bottom: 12px;
                }

                .tool-settings-button {
                    width: 32px;
                    height: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 10px;
                    background: rgba(255, 255, 255, 0.04);
                    border: none;
                    color: rgba(255, 255, 255, 0.6);
                    cursor: pointer;
                    transition: all 200ms ease;
                }

                .tool-settings-button:hover {
                    color: white;
                    background: rgba(255, 255, 255, 0.08);
                }

                .tool-settings-panel {
                    position: absolute;
                    left: 0;
                    bottom: calc(100% + 12px);
                    background: rgba(10, 10, 10, 0.92);
                    backdrop-filter: blur(16px);
                    border-radius: 14px;
                    padding: 12px 14px;
                    min-width: 240px;
                    max-width: 300px;
                    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.6);
                    z-index: 110;
                }

                .tool-settings-title {
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.6px;
                    color: rgba(255, 255, 255, 0.5);
                    margin-bottom: 10px;
                }

                .tool-settings-row {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                    padding: 6px 0;
                }

                .tool-settings-label {
                    font-size: 11px;
                    color: rgba(255, 255, 255, 0.45);
                }

                .tool-settings-value {
                    font-size: 12px;
                    color: rgba(255, 255, 255, 0.8);
                    word-break: break-all;
                }

                .tool-selector-wrapper {
                    position: relative;
                }

                .tool-selector-button {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    padding: 4px 6px;
                    background: transparent;
                    border: none;
                    color: rgba(255, 255, 255, 0.65);
                    font-size: 11px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 200ms ease;
                    white-space: nowrap;
                }

                .tool-selector-button:hover {
                    color: rgba(255, 255, 255, 0.85);
                }

                .tool-label {
                    text-transform: capitalize;
                    max-width: 96px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    letter-spacing: 0.3px;
                    font-size: 11px;
                }

                .tool-dropdown {
                    position: absolute;
                    bottom: calc(100% + 10px);
                    right: 0;
                    background: rgba(12, 12, 12, 0.96);
                    backdrop-filter: blur(20px);
                    border-radius: 14px;
                    padding: 6px;
                    min-width: 170px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
                    z-index: 100;
                    overflow: hidden;
                }

                .tool-option {
                    display: flex;
                    align-items: center;
                    padding: 8px 10px;
                    border-radius: 10px;
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 12px;
                    font-weight: 500;
                    text-align: left;
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    transition: all 150ms ease;
                    width: 100%;
                }

                .tool-option:hover {
                    background: rgba(255, 255, 255, 0.05);
                    color: white;
                }

                .tool-option-label {
                    flex: 1;
                    text-transform: capitalize;
                }

                /* Mobile adjustments */
                @media (max-width: 767px) {
                    .input-bar-wrapper {
                        max-width: 100%;
                    }

                    .input-bar {
                        padding: 12px 12px 16px;
                        border-radius: 16px;
                    }

                    .input-wrapper {
                        min-height: 64px;
                    }

                    .text-input {
                        min-height: 64px;
                        font-size: 15px;
                        padding: 4px 140px 40px 46px;
                    }

                    .input-actions {
                        right: 10px;
                        bottom: 10px;
                        gap: 6px;
                    }

                    .send-button {
                        width: 34px;
                        height: 34px;
                    }

                    .tool-settings-wrapper {
                        left: 10px;
                        bottom: 10px;
                    }

                    .tool-settings-panel {
                        min-width: 210px;
                        max-width: 70vw;
                    }

                    .tool-selector-button {
                        padding: 3px 4px;
                        font-size: 10px;
                    }

                    .tool-dropdown {
                        width: 170px;
                    }
                }

                @media (max-width: 480px) {
                    .input-bar {
                        padding: 10px 10px 14px;
                    }

                    .text-input {
                        font-size: 14px;
                        padding: 4px 120px 36px 42px;
                    }

                    .send-button {
                        width: 32px;
                        height: 32px;
                    }

                    .tool-selector-button {
                        padding: 2px 4px;
                        font-size: 9px;
                    }
                }
            `}</style>
    </div>
  );
};

export default InputBar;
