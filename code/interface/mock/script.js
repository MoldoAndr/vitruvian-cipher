// Configuration for microservices
const CONFIG = {
    passwordChecker: {
        baseUrl: 'http://localhost:9000',
        endpoints: {
            health: '/health',
            score: '/score'
        }
    },
    theorySpecialist: {
        baseUrl: 'http://localhost:8100',
        endpoints: {
            health: '/health',
            generate: '/generate',
            ingest: '/ingest',
            conversations: '/conversations'
        }
    },
    choiceMaker: {
        // Choice Maker host port mapped to 8081 (container still listens on 8080)
        baseUrl: 'http://localhost:8081',
        endpoints: {
            health: '/health',
            extract: '/predict'
        }
    }
};

// Global state
let currentConversationId = null;
let selectedComponents = ['pass_strength_ai', 'zxcvbn', 'haveibeenpwned'];
let selectedDocumentType = 'pdf';
let selectedFile = null;

// Initialize the interface
document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    initializeOptions();
    initializeFileUpload();
    checkHealth();
    setInterval(checkHealth, 30000);
    
    // Handle Enter key submissions
    document.getElementById('password-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') handlePasswordAnalysis();
    });
    
    document.getElementById('crypto-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleCryptoQuery();
        }
    });
    
    document.getElementById('document-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') handleDocumentIngestion();
    });

    // New: Handle Enter key for choice maker
    document.getElementById('choice-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') handleChoiceQuery();
    });
});

// Tab management
function initializeTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.getAttribute('data-tab')));
    });
}

function switchTab(tabName) {
    // Update tab appearance
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-content`).classList.add('active');
}

// Options management
function initializeOptions() {
    // Component selection for password analysis
    document.querySelectorAll('[data-component]').forEach(pill => {
        pill.addEventListener('click', () => {
            pill.classList.toggle('selected');
            updateSelectedComponents();
        });
    });
    
    // Document type selection
    document.querySelectorAll('[data-type]').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('[data-type]').forEach(p => p.classList.remove('selected'));
            pill.classList.add('selected');
            selectedDocumentType = pill.getAttribute('data-type');
        });
    });

    // Choice Maker mode selection (intent/entities/both)
    document.querySelectorAll('[data-choice-mode]').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('[data-choice-mode]').forEach(p => p.classList.remove('selected'));
            pill.classList.add('selected');
        });
    });
}

function updateSelectedComponents() {
    selectedComponents = Array.from(document.querySelectorAll('[data-component].selected'))
        .map(pill => pill.getAttribute('data-component'));
}

// File upload management
function initializeFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const selectedFileDiv = document.getElementById('selected-file');
    const removeFileBtn = document.getElementById('remove-file');
    
    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // Drag and drop functionality
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
    
    // Remove file button
    removeFileBtn.addEventListener('click', () => {
        clearFileSelection();
    });
}

function handleFileSelection(file) {
    // Validate file type
    const validTypes = ['application/pdf', 'text/markdown', 'text/plain', 'text/x-markdown'];
    const validExtensions = ['.pdf', '.md', '.txt', '.markdown'];
    
    const isValidType = validTypes.includes(file.type) || 
                       validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    
    if (!isValidType) {
        addMessage('document-chat', '❌ Invalid file type. Please select a PDF, Markdown, or Text file.', 'error');
        return;
    }
    
    selectedFile = file;
    updateFileDisplay();
    
    // Auto-detect document type
    if (file.name.toLowerCase().endsWith('.pdf')) {
        selectDocumentType('pdf');
    } else if (file.name.toLowerCase().endsWith('.md') || file.name.toLowerCase().endsWith('.markdown')) {
        selectDocumentType('markdown');
    } else {
        selectDocumentType('text');
    }
}

function selectDocumentType(type) {
    document.querySelectorAll('[data-type]').forEach(pill => pill.classList.remove('selected'));
    document.querySelector(`[data-type="${type}"]`).classList.add('selected');
    selectedDocumentType = type;
}

function updateFileDisplay() {
    const selectedFileDiv = document.getElementById('selected-file');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    
    if (selectedFile) {
        fileName.textContent = selectedFile.name;
        fileSize.textContent = formatFileSize(selectedFile.size);
        selectedFileDiv.classList.add('visible');
    } else {
        selectedFileDiv.classList.remove('visible');
    }
}

function clearFileSelection() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    updateFileDisplay();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Message management
function addMessage(containerId, content, type = 'system') {
    const container = document.getElementById(containerId);
    const welcomeMessage = container.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.innerHTML = `<div class="message-content">${content}</div>`;
    
    container.appendChild(message);
    container.scrollTop = container.scrollHeight;
}

function addLoadingMessage(containerId) {
    const container = document.getElementById(containerId);
    const loading = document.createElement('div');
    loading.className = 'loading-indicator';
    loading.innerHTML = `
        <span>Processing</span>
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;
    container.appendChild(loading);
    container.scrollTop = container.scrollHeight;
    return loading;
}

// Health check functions
async function checkHealth() {
    await Promise.all([
        checkPasswordCheckerHealth(),
        checkTheorySpecialistHealth(),
        // New: also check choice maker
        checkChoiceMakerHealth()
    ]);
}

async function checkPasswordCheckerHealth() {
    const statusElement = document.getElementById('password-status');
    
    try {
        const response = await fetch(`${CONFIG.passwordChecker.baseUrl}${CONFIG.passwordChecker.endpoints.health}`);
        if (response.ok) {
            statusElement.classList.add('online');
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        statusElement.classList.remove('online');
    }
}

async function checkTheorySpecialistHealth() {
    const statusElement = document.getElementById('theory-status');
    
    try {
        const response = await fetch(`${CONFIG.theorySpecialist.baseUrl}${CONFIG.theorySpecialist.endpoints.health}`);
        if (response.ok) {
            statusElement.classList.add('online');
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        statusElement.classList.remove('online');
    }
}

// New: choice maker health check
async function checkChoiceMakerHealth() {
    const statusElement = document.getElementById('choice-status');
    if (!statusElement) return;

    try {
        const response = await fetch(`${CONFIG.choiceMaker.baseUrl}${CONFIG.choiceMaker.endpoints.health}`);
        if (response.ok) {
            statusElement.classList.add('online');
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        statusElement.classList.remove('online');
    }
}

// Password Analysis Handler
async function handlePasswordAnalysis() {
    const input = document.getElementById('password-input');
    const password = input.value.trim();
    
    if (!password) return;
    
    const button = document.querySelector('#password-content .send-button');
    button.disabled = true;
    
    // Add user message
    addMessage('password-chat', `Analyze password: ${'*'.repeat(password.length)}`, 'user');
    
    // Add loading indicator
    const loading = addLoadingMessage('password-chat');
    
    try {
        const payload = { password };
        if (selectedComponents.length > 0) {
            payload.components = selectedComponents;
        }
        
        const response = await fetch(`${CONFIG.passwordChecker.baseUrl}${CONFIG.passwordChecker.endpoints.score}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        loading.remove();
        
        if (response.ok) {
            const data = await response.json();
            
            let resultHtml = `
                <h4>Password Analysis Complete</h4>
                <p><strong>Overall Score:</strong> <span class="score-highlight">${data.normalized_score}/100</span></p>
                <p><strong>Active Components:</strong> ${data.active_components.join(', ')}</p>
            `;
            
            data.components.forEach(component => {
                const status = component.success ? '✅' : '❌';
                resultHtml += `
                    <div class="component-result">
                        <strong>${status} ${component.label}</strong><br>
                        Score: <span class="score-highlight">${component.normalized_score || 'N/A'}/100</span><br>
                        ${component.error ? `Error: ${component.error}` : 'Analysis completed successfully'}
                    </div>
                `;
            });
            
            addMessage('password-chat', resultHtml, 'system');
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            addMessage('password-chat', `❌ Error: ${errorData.detail}`, 'error');
        }
    } catch (error) {
        loading.remove();
        addMessage('password-chat', `❌ Network Error: ${error.message}`, 'error');
    }
    
    input.value = '';
    button.disabled = false;
}

// Cryptography Query Handler
async function handleCryptoQuery() {
    const input = document.getElementById('crypto-input');
    const query = input.value.trim();
    
    if (!query) return;
    
    const button = document.querySelector('#crypto-content .send-button');
    button.disabled = true;
    
    // Add user message
    addMessage('crypto-chat', query, 'user');
    
    // Add loading indicator
    const loading = addLoadingMessage('crypto-chat');
    
    try {
        const payload = { query };
        if (currentConversationId) {
            payload.conversation_id = currentConversationId;
        }
        
        const response = await fetch(`${CONFIG.theorySpecialist.baseUrl}${CONFIG.theorySpecialist.endpoints.generate}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        loading.remove();
        
        if (response.ok) {
            const data = await response.json();
            currentConversationId = data.conversation_id;
            
            let resultHtml = `
                <h4>Cryptography Analysis</h4>
                <p>${data.answer.replace(/\n/g, '<br>')}</p>
            `;
            
            if (data.sources && data.sources.length > 0) {
                resultHtml += `
                    <div style="margin-top: 12px; padding: 8px; background: rgba(255,255,255,0.02); border-radius: 6px;">
                        <strong>Sources:</strong><br>
                        ${data.sources.map(source => {
                            const metadata = source.metadata || {};
                            let name = metadata.source || 'Unknown Source';
                            try {
                                name = decodeURIComponent(name);
                            } catch (e) {
                                console.warn('Failed to decode source name:', name);
                            }
                            const page = metadata.source_page ? ` (Page ${metadata.source_page})` : '';
                            const score = source.relevance_score ? ` [${(source.relevance_score * 100).toFixed(1)}%]` : '';
                            return `• ${name}${page}${score}`;
                        }).join('<br>')}
                    </div>
                `;
            }
            
            addMessage('crypto-chat', resultHtml, 'system');
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            addMessage('crypto-chat', `❌ Error: ${errorData.detail}`, 'error');
        }
    } catch (error) {
        loading.remove();
        addMessage('crypto-chat', `❌ Network Error: ${error.message}`, 'error');
    }
    
    input.value = '';
    button.disabled = false;
}

// Document Ingestion Handler
async function handleDocumentIngestion() {
    const input = document.getElementById('document-input');
    const documentPath = input.value.trim();
    
    // Check if we have either a file or a path
    if (!selectedFile && !documentPath) {
        addMessage('document-chat', '❌ Please either upload a file or enter a document path.', 'error');
        return;
    }
    
    const button = document.querySelector('#document-content .send-button');
    button.disabled = true;
    
    let userMessage = '';
    let payload = {};
    
    if (selectedFile) {
        // Handle file upload
        userMessage = `Upload file: ${selectedFile.name} (${selectedDocumentType.toUpperCase()})`;
        
        // For file upload, we'll need to send the file content or create a temporary path
        // Since the backend expects a path, we'll simulate this for now
        payload = {
            document_path: `/tmp/${selectedFile.name}`,
            document_type: selectedDocumentType
        };
        
        addMessage('document-chat', userMessage, 'user');
        addMessage('document-chat', '⚠️ Note: File upload simulation - in production this would upload the actual file content.', 'system');
        
    } else {
        // Handle URL/path input
        userMessage = `Ingest document: ${documentPath} (${selectedDocumentType.toUpperCase()})`;
        payload = {
            document_path: documentPath,
            document_type: selectedDocumentType
        };
        addMessage('document-chat', userMessage, 'user');
    }
    
    // Add loading indicator
    const loading = addLoadingMessage('document-chat');
    
    try {
        const response = await fetch(`${CONFIG.theorySpecialist.baseUrl}${CONFIG.theorySpecialist.endpoints.ingest}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        loading.remove();
        
        if (response.ok) {
            const data = await response.json();
            
            const resultHtml = `
                <h4>Document Ingestion Complete</h4>
                <div class="component-result">
                    <strong>Status:</strong> <span class="score-highlight">${data.status}</span><br>
                    <strong>Document ID:</strong> ${data.document_id || 'N/A'}<br>
                    <strong>Message:</strong> ${data.message}
                </div>
            `;
            
            addMessage('document-chat', resultHtml, 'system');
            
            // Clear inputs after successful ingestion
            input.value = '';
            clearFileSelection();
            
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            addMessage('document-chat', `❌ Error: ${errorData.detail}`, 'error');
        }
    } catch (error) {
        loading.remove();
        addMessage('document-chat', `❌ Network Error: ${error.message}`, 'error');
    }
    
    button.disabled = false;
}

// New: Choice Query Handler
async function handleChoiceQuery() {
    const input = document.getElementById('choice-input');
    const text = input.value.trim();
    console.log("Handling choice query for text:", text);
    if (!text) return;

    const button = document.querySelector('#choice-content .send-button');
    button.disabled = true;

    addMessage('choice-chat', text, 'user');
    const loading = addLoadingMessage('choice-chat');

    try {
        // Determine requested mode from UI
        const selectedModePill = document.querySelector('[data-choice-mode].selected');
        let mode = 'both'; // Default to both
        if (selectedModePill) {
            mode = selectedModePill.getAttribute('data-choice-mode');
        }

        const callChoiceMaker = async (operation) => {
            const payload = { text, operation };
            const resp = await fetch(`${CONFIG.choiceMaker.baseUrl}${CONFIG.choiceMaker.endpoints.extract}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!resp.ok) {
                const errorData = await resp.json().catch(() => ({ error: 'Unknown error' }));
                throw new Error(errorData.error || errorData.message || errorData.detail || `HTTP ${resp.status}`);
            }
            const data = await resp.json();
            if (data.status !== 'ok') {
                throw new Error(data.message || 'Choice Maker returned an error response.');
            }
            return data;
        };

        // If mode is "both", perform two calls (intent + entities) and merge results client-side
        let intentData = null;
        let entityData = null;

        if (mode === 'both') {
            [intentData, entityData] = await Promise.all([
                callChoiceMaker('intent_extraction'),
                callChoiceMaker('entity_extraction')
            ]);
        } else if (mode === 'intent_extraction') {
            intentData = await callChoiceMaker('intent_extraction');
        } else if (mode === 'entity_extraction') {
            entityData = await callChoiceMaker('entity_extraction');
        }

        loading.remove();

        let html = '<h4>Choice Maker Result</h4>';

        if (intentData && intentData.result) {
            const intent = intentData.result.intent || intentData.result;
            if (intent) {
                html += `
                    <div class="component-result">
                        <strong>Intent Classification</strong><br>
                        Label: <span class="score-highlight">${intent.label || 'Unknown'}</span><br>
                        Confidence: ${intent.score ? (intent.score * 100).toFixed(1) + '%' : 'N/A'}
                    </div>
                `;
            }
        }

        if (entityData && entityData.result) {
            const entitiesBlock = entityData.result.entities || entityData.result;
            const entities = Array.isArray(entitiesBlock.entities) ? entitiesBlock.entities : (Array.isArray(entitiesBlock) ? entitiesBlock : []);
            
            if (entities.length > 0) {
                html += `
                    <div class="component-result">
                        <strong>Entity Extraction</strong><br>
                        Found ${entities.length} entities:<br>
                        <ul style="margin-top:6px; padding-left:18px;">
                            ${entities.map(e => `
                                <li>
                                    <span class="score-highlight">${e.entity}</span> → "${e.text}" 
                                    (conf: ${e.score ? (e.score * 100).toFixed(1) + '%' : 'N/A'}, span: ${e.start}-${e.end})
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                `;
            } else {
                html += `
                    <div class="component-result">
                        <strong>Entity Extraction</strong><br>
                        No entities detected in this text.
                    </div>
                `;
            }
        }

        if (!html.includes('component-result')) {
            html += '<p>No intent or entities could be extracted from this text.</p>';
        }

        addMessage('choice-chat', html, 'system');
    } catch (error) {
        loading.remove();
        addMessage('choice-chat', `❌ Error: ${error.message}`, 'error');
    }

    input.value = '';
    button.disabled = false;
}
