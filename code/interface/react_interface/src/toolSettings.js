export const PASSWORD_COMPONENTS = [
    { id: 'pass_strength_ai', label: 'PassGPT' },
    { id: 'zxcvbn', label: 'zxcvbn' },
    { id: 'haveibeenpwned', label: 'HIBP' },
];

export const CHOICE_MODES = [
    { id: 'both', label: 'Both' },
    { id: 'intent_extraction', label: 'Intent' },
    { id: 'entity_extraction', label: 'Entities' },
];

export const ORCHESTRATOR_PROVIDERS = [
    { id: 'openai', label: 'OpenAI' },
    { id: 'anthropic', label: 'Anthropic' },
    { id: 'gemini', label: 'Gemini' },
    { id: 'ollama_local', label: 'Ollama Local' },
    { id: 'ollama_cloud', label: 'Ollama Cloud' },
];

export const getDefaultToolSettings = () => ({
    password: {
        components: PASSWORD_COMPONENTS.map((component) => component.id),
    },
    choice: {
        mode: 'both',
    },
    orchestrator: {
        provider: 'openai',
        apiKey: '',
        plannerProfile: 'planner',
        responderProfile: 'responder',
        modelOverride: '',
        plannerModelOverride: '',
        summary: '',
        theoryConversationId: '',
        extraKeys: {
            openai: '',
            anthropic: '',
            gemini: '',
            ollama_local: '',
            ollama_cloud: '',
        },
        fallbackEnabled: false,
        fallbackProviders: '',
        debug: false,
    },
    crypto: {},
    prime: {},
});
