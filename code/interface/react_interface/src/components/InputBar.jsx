import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, ChevronDown, Settings } from "lucide-react";
import { useApp } from "../contexts/AppContext";
import {
  PASSWORD_COMPONENTS,
  CHOICE_MODES,
  ORCHESTRATOR_PROVIDERS,
} from "../toolSettings";

const TOOLS = [
  { id: "orchestrator", label: "Orchestrator" },
  { id: "password", label: "Password" },
  { id: "crypto", label: "Crypto" },
  { id: "choice", label: "Choice" },
  { id: "prime", label: "Prime" },
];

const InputBar = ({ onSubmit, loading: externalLoading, idleGlow = false }) => {
  const {
    inputValue,
    setInputValue,
    selectedTool,
    setSelectedTool,
    toolSettings,
    setToolSettings,
  } = useApp();
  const [toolDropdownOpen, setToolDropdownOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [orchestratorAdvancedOpen, setOrchestratorAdvancedOpen] = useState(false);
  const textareaRef = useRef(null);
  const settingsRef = useRef(null);
  const toolSelectorRef = useRef(null);

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
  const currentToolSettings = toolSettings[selectedTool] || {};

  const togglePasswordComponent = (componentId) => {
    setToolSettings((prev) => {
      const current = prev.password.components;
      const next = current.includes(componentId)
        ? current.filter((id) => id !== componentId)
        : [...current, componentId];
      return { ...prev, password: { ...prev.password, components: next } };
    });
  };

  const updateChoiceMode = (mode) => {
    setToolSettings((prev) => ({
      ...prev,
      choice: { ...prev.choice, mode },
    }));
  };

  const updateOrchestrator = (updates) => {
    setToolSettings((prev) => ({
      ...prev,
      orchestrator: { ...prev.orchestrator, ...updates },
    }));
  };

  const updateOrchestratorKey = (key, value) => {
    setToolSettings((prev) => ({
      ...prev,
      orchestrator: {
        ...prev.orchestrator,
        extraKeys: {
          ...prev.orchestrator.extraKeys,
          [key]: value,
        },
      },
    }));
  };

  // Close dropdown/panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        toolDropdownOpen &&
        toolSelectorRef.current &&
        !toolSelectorRef.current.contains(event.target)
      ) {
        setToolDropdownOpen(false);
      }

      if (
        settingsOpen &&
        settingsRef.current &&
        !settingsRef.current.contains(event.target)
      ) {
        setSettingsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [settingsOpen, toolDropdownOpen]);

  return (
    <div className="input-bar-wrapper">
      <div className={`input-bar ${inputValue ? "focused" : ""} ${idleGlow ? "idle-glow" : ""}`}>
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
        <div className="tool-settings-wrapper" ref={settingsRef}>
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
                <div className="tool-settings-title">Tool settings</div>
                <div className="tool-settings-row">
                  <span className="tool-settings-label">Tool</span>
                  <span className="tool-settings-value">{currentTool.label}</span>
                </div>

                {selectedTool === "password" && (
                  <div className="tool-settings-section">
                    <div className="tool-settings-section-title">
                      Password engines
                    </div>
                    <div className="tool-settings-options">
                      {PASSWORD_COMPONENTS.map((component) => (
                        <label key={component.id} className="tool-settings-option">
                          <input
                            type="checkbox"
                            checked={currentToolSettings.components?.includes(
                              component.id,
                            )}
                            onChange={() => togglePasswordComponent(component.id)}
                          />
                          <span>{component.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {selectedTool === "choice" && (
                  <div className="tool-settings-section">
                    <div className="tool-settings-section-title">Mode</div>
                    <div className="tool-settings-options">
                      {CHOICE_MODES.map((mode) => (
                        <button
                          key={mode.id}
                          type="button"
                          className={`tool-settings-pill ${
                            currentToolSettings.mode === mode.id ? "active" : ""
                          }`}
                          onClick={() => updateChoiceMode(mode.id)}
                        >
                          {mode.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {selectedTool === "orchestrator" && (
                  <div className="tool-settings-section">
                    <div className="tool-settings-section-title">LLM</div>
                    <label className="tool-settings-field">
                      <span className="tool-settings-label">Provider</span>
                      <select
                        className="tool-settings-input"
                        value={currentToolSettings.provider}
                        onChange={(e) =>
                          updateOrchestrator({ provider: e.target.value })
                        }
                      >
                        {ORCHESTRATOR_PROVIDERS.map((provider) => (
                          <option key={provider.id} value={provider.id}>
                            {provider.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="tool-settings-field">
                      <span className="tool-settings-label">API key</span>
                      <input
                        className="tool-settings-input"
                        type="password"
                        value={currentToolSettings.apiKey || ""}
                        onChange={(e) =>
                          updateOrchestrator({ apiKey: e.target.value })
                        }
                        placeholder="Optional"
                      />
                    </label>
                    <label className="tool-settings-field">
                      <span className="tool-settings-label">Model override</span>
                      <input
                        className="tool-settings-input"
                        value={currentToolSettings.modelOverride || ""}
                        onChange={(e) =>
                          updateOrchestrator({ modelOverride: e.target.value })
                        }
                        placeholder="Optional"
                      />
                    </label>
                    <label className="tool-settings-field">
                      <span className="tool-settings-label">Summary</span>
                      <textarea
                        className="tool-settings-textarea"
                        value={currentToolSettings.summary || ""}
                        onChange={(e) =>
                          updateOrchestrator({ summary: e.target.value })
                        }
                        placeholder="Optional"
                      />
                    </label>
                    <label className="tool-settings-field">
                      <span className="tool-settings-label">
                        Theory conversation ID
                      </span>
                      <input
                        className="tool-settings-input"
                        value={currentToolSettings.theoryConversationId || ""}
                        onChange={(e) =>
                          updateOrchestrator({
                            theoryConversationId: e.target.value,
                          })
                        }
                        placeholder="Optional"
                      />
                    </label>

                    <button
                      type="button"
                      className="tool-settings-advanced-toggle"
                      onClick={() =>
                        setOrchestratorAdvancedOpen(!orchestratorAdvancedOpen)
                      }
                    >
                      {orchestratorAdvancedOpen ? "Hide" : "Show"} advanced
                    </button>

                    {orchestratorAdvancedOpen && (
                      <div className="tool-settings-advanced">
                        <label className="tool-settings-field">
                          <span className="tool-settings-label">
                            Responder profile
                          </span>
                          <input
                            className="tool-settings-input"
                            value={currentToolSettings.responderProfile || ""}
                            onChange={(e) =>
                              updateOrchestrator({
                                responderProfile: e.target.value,
                              })
                            }
                            placeholder="responder"
                          />
                        </label>
                        <label className="tool-settings-field">
                          <span className="tool-settings-label">
                            Planner profile
                          </span>
                          <input
                            className="tool-settings-input"
                            value={currentToolSettings.plannerProfile || ""}
                            onChange={(e) =>
                              updateOrchestrator({
                                plannerProfile: e.target.value,
                              })
                            }
                            placeholder="planner"
                          />
                        </label>
                        <label className="tool-settings-field">
                          <span className="tool-settings-label">
                            Planner model override
                          </span>
                          <input
                            className="tool-settings-input"
                            value={currentToolSettings.plannerModelOverride || ""}
                            onChange={(e) =>
                              updateOrchestrator({
                                plannerModelOverride: e.target.value,
                              })
                            }
                            placeholder="Optional"
                          />
                        </label>
                        <label className="tool-settings-toggle">
                          <span className="tool-settings-label">Fallback</span>
                          <input
                            type="checkbox"
                            checked={currentToolSettings.fallbackEnabled}
                            onChange={(e) =>
                              updateOrchestrator({
                                fallbackEnabled: e.target.checked,
                              })
                            }
                          />
                        </label>
                        {currentToolSettings.fallbackEnabled && (
                          <label className="tool-settings-field">
                            <span className="tool-settings-label">
                              Fallback providers
                            </span>
                            <input
                              className="tool-settings-input"
                              value={currentToolSettings.fallbackProviders || ""}
                              onChange={(e) =>
                                updateOrchestrator({
                                  fallbackProviders: e.target.value,
                                })
                              }
                              placeholder="comma-separated"
                            />
                          </label>
                        )}
                        <label className="tool-settings-toggle">
                          <span className="tool-settings-label">Debug</span>
                          <input
                            type="checkbox"
                            checked={currentToolSettings.debug}
                            onChange={(e) =>
                              updateOrchestrator({ debug: e.target.checked })
                            }
                          />
                        </label>
                        {currentToolSettings.extraKeys && (
                          <div className="tool-settings-grid">
                            {Object.keys(currentToolSettings.extraKeys).map(
                              (key) => (
                                <input
                                  key={key}
                                  type="password"
                                  className="tool-settings-input"
                                  value={currentToolSettings.extraKeys[key] || ""}
                                  onChange={(e) =>
                                    updateOrchestratorKey(key, e.target.value)
                                  }
                                  placeholder={`${key} key`}
                                />
                              ),
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {selectedTool === "crypto" && (
                  <div className="tool-settings-section">
                    <div className="tool-settings-section-title">Notes</div>
                    <div className="tool-settings-value">
                      No additional settings for this tool.
                    </div>
                  </div>
                )}

                {selectedTool === "prime" && (
                  <div className="tool-settings-section">
                    <div className="tool-settings-section-title">Notes</div>
                    <div className="tool-settings-value">
                      No additional settings for this tool.
                    </div>
                  </div>
                )}

              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Actions */}
        <div className="input-actions">
          <div className="tool-selector-wrapper" ref={toolSelectorRef}>
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
                    overflow: visible;
                    isolation: isolate;
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

                .input-bar > * {
                    position: relative;
                    z-index: 1;
                }

                .input-bar.idle-glow::before {
                    content: '';
                    position: absolute;
                    inset: -2px;
                    border-radius: 26px;
                    border: 1px solid rgba(0, 255, 136, 0.18);
                    box-shadow: 0 0 18px rgba(0, 255, 136, 0.2);
                    opacity: 0.7;
                    pointer-events: none;
                    animation: idleGlow 4.6s ease-in-out infinite;
                }

                @keyframes idleGlow {
                    0%, 100% {
                        opacity: 0.5;
                        box-shadow: 0 0 14px rgba(0, 255, 136, 0.15);
                    }
                    45% {
                        opacity: 0.85;
                        box-shadow: 0 0 28px rgba(0, 255, 136, 0.35);
                    }
                    70% {
                        opacity: 0.6;
                        box-shadow: 0 0 18px rgba(0, 255, 136, 0.2);
                    }
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
                    max-width: 320px;
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

                .tool-settings-section {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    margin-top: 8px;
                }

                .tool-settings-section-title {
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.6px;
                    color: rgba(255, 255, 255, 0.5);
                }

                .tool-settings-options {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                }

                .tool-settings-option {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 12px;
                    color: rgba(255, 255, 255, 0.75);
                }

                .tool-settings-option input {
                    accent-color: #00ff88;
                }

                .tool-settings-pill {
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    background: rgba(255, 255, 255, 0.03);
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 11px;
                    padding: 4px 10px;
                    border-radius: 999px;
                    cursor: pointer;
                    transition: all 150ms ease;
                }

                .tool-settings-pill.active {
                    color: #00ff88;
                    border-color: rgba(0, 255, 136, 0.4);
                    background: rgba(0, 255, 136, 0.1);
                }

                .tool-settings-field {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                }

                .tool-settings-input {
                    background: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 8px;
                    padding: 6px 8px;
                    color: white;
                    font-size: 11px;
                }

                .tool-settings-input:focus {
                    outline: none;
                    border-color: rgba(0, 255, 136, 0.4);
                }

                .tool-settings-textarea {
                    background: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 8px;
                    padding: 6px 8px;
                    color: white;
                    font-size: 11px;
                    min-height: 64px;
                    resize: none;
                }

                .tool-settings-textarea:focus {
                    outline: none;
                    border-color: rgba(0, 255, 136, 0.4);
                }

                .tool-settings-grid {
                    display: grid;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 6px;
                }

                .tool-settings-toggle {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;
                    font-size: 12px;
                    color: rgba(255, 255, 255, 0.75);
                }

                .tool-settings-advanced-toggle {
                    align-self: flex-start;
                    background: transparent;
                    border: none;
                    color: rgba(255, 255, 255, 0.55);
                    font-size: 11px;
                    cursor: pointer;
                    padding: 2px 0;
                }

                .tool-settings-advanced-toggle:hover {
                    color: rgba(255, 255, 255, 0.85);
                }

                .tool-settings-advanced {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    margin-top: 6px;
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
                    font-size: 14px;
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
                        max-width: 80vw;
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
