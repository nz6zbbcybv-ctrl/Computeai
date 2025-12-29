/**
 * Main application JavaScript for Groq Conversational AI.
 */
class ChatApp {
    constructor() {
        this.sessionId = null;
        this.eventSource = null;
        this.currentMessage = '';
        this.isStreaming = false;
        this.voiceChat = null;
        
        this.init();
    }
    
    init() {
        // Initialize voice chat
        if (typeof VoiceChat !== 'undefined') {
            this.voiceChat = new VoiceChat();
        }
        
        this.loadSession();
        this.setupEventListeners();
        this.checkHealth();
        this.loadAvailableModels();
    }
    
    async loadSession() {
        try {
            // Try to get existing session from localStorage
            const savedSessionId = localStorage.getItem('sessionId');
            
            if (savedSessionId) {
                // Verify session exists
                const response = await fetch(`/api/session/${savedSessionId}`);
                if (response.ok) {
                    this.sessionId = savedSessionId;
                    const data = await response.json();
                    this.loadMessages(data.messages || []);
                    return;
                }
            }
            
            // Create new session
            await this.createSession();
        } catch (error) {
            console.error('Failed to load session:', error);
            await this.createSession();
        }
    }
    
    async createSession() {
        try {
            const response = await fetch('/api/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                localStorage.setItem('sessionId', this.sessionId);
            } else {
                throw new Error('Failed to create session');
            }
        } catch (error) {
            console.error('Failed to create session:', error);
            this.updateStatus('connectionStatus', 'Error');
        }
    }
    
    async checkHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            
            if (data.status === 'healthy' && data.groq_configured) {
                this.updateStatus('connectionStatus', 'Connected to Groq');
            } else {
                this.updateStatus('connectionStatus', 'Degraded');
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateStatus('connectionStatus', 'Disconnected');
        }
    }
    
    async loadAvailableModels() {
        try {
            const response = await fetch('/api/models');
            if (response.ok) {
                const data = await response.json();
                // Store default model
                if (data.default) {
                    this.updateStatus('modelName', data.default);
                }
            }
        } catch (error) {
            console.error('Failed to load models:', error);
        }
    }
    
    loadMessages(messages) {
        const messagesContainer = document.getElementById('messages');
        messagesContainer.innerHTML = '';
        
        messages.forEach(msg => {
            this.addMessage(msg.content, msg.role);
        });
    }
    
    setupEventListeners() {
        const sendButton = document.getElementById('sendButton');
        const messageInput = document.getElementById('messageInput');
        const voiceRecordButton = document.getElementById('voiceRecordButton');
        const voiceLanguageSelect = document.getElementById('voiceLanguage');
        const voiceOutputToggle = document.getElementById('voiceOutputToggle');
        
        sendButton.addEventListener('click', () => this.sendMessage());
        
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        messageInput.addEventListener('input', () => {
            messageInput.style.height = 'auto';
            messageInput.style.height = messageInput.scrollHeight + 'px';
        });
        
        // Voice recording button
        if (voiceRecordButton && this.voiceChat) {
            let pressTimer = null;
            let isHolding = false;
            
            // Click to toggle recording
            voiceRecordButton.addEventListener('click', (e) => {
                if (!isHolding) {
                    if (this.voiceChat.isRecording) {
                        this.voiceChat.stopRecording();
                    } else {
                        this.voiceChat.startRecording();
                    }
                }
            });
            
            // Hold to record (alternative method)
            voiceRecordButton.addEventListener('mousedown', () => {
                isHolding = true;
                pressTimer = setTimeout(() => {
                    if (!this.voiceChat.isRecording) {
                        this.voiceChat.startRecording();
                    }
                }, 300);
            });
            
            voiceRecordButton.addEventListener('mouseup', () => {
                isHolding = false;
                if (pressTimer) {
                    clearTimeout(pressTimer);
                    pressTimer = null;
                }
            });
            
            voiceRecordButton.addEventListener('mouseleave', () => {
                isHolding = false;
                if (pressTimer) {
                    clearTimeout(pressTimer);
                    pressTimer = null;
                }
            });
            
            // Touch events for mobile
            voiceRecordButton.addEventListener('touchstart', (e) => {
                e.preventDefault();
                isHolding = true;
                pressTimer = setTimeout(() => {
                    if (!this.voiceChat.isRecording) {
                        this.voiceChat.startRecording();
                    }
                }, 300);
            });
            
            voiceRecordButton.addEventListener('touchend', (e) => {
                e.preventDefault();
                isHolding = false;
                if (pressTimer) {
                    clearTimeout(pressTimer);
                    pressTimer = null;
                }
            });
        }
        
        // Language selector
        if (voiceLanguageSelect && this.voiceChat) {
            voiceLanguageSelect.addEventListener('change', (e) => {
                this.voiceChat.setLanguage(e.target.value);
            });
            // Set initial language
            this.voiceChat.setLanguage(voiceLanguageSelect.value);
        }
        
        // Voice output toggle
        if (voiceOutputToggle && this.voiceChat) {
            voiceOutputToggle.addEventListener('change', (e) => {
                this.voiceChat.setVoiceOutputEnabled(e.target.checked);
            });
        }
    }
    
    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || this.isStreaming) {
            return;
        }
        
        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Add user message to UI
        this.addMessage(message, 'user');
        
        // Start streaming
        this.isStreaming = true;
        this.currentMessage = '';
        this.setAvatarState('thinking');
        
        // Create assistant message element
        const messageElement = this.createMessageElement('', 'assistant');
        const messagesContainer = document.getElementById('messages');
        messagesContainer.appendChild(messageElement);
        const contentElement = messageElement.querySelector('.message-content');
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            // Read SSE stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        this.handleStreamEvent(data, contentElement);
                    }
                }
            }
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.addMessage('Error: Failed to send message. Please try again.', 'assistant');
            this.setAvatarState('error');
        } finally {
            this.isStreaming = false;
            this.setAvatarState('idle');
        }
    }
    
    handleStreamEvent(event, contentElement) {
        switch (event.type) {
            case 'token':
                this.currentMessage += event.content;
                contentElement.textContent = this.currentMessage;
                this.setAvatarState('streaming');
                break;
                
            case 'status':
                if (event.state === 'thinking') {
                    this.setAvatarState('thinking');
                } else if (event.state === 'complete') {
                    this.setAvatarState('speaking');
                    if (event.metrics) {
                        this.updateStatus('latency', `${event.metrics.latency.toFixed(2)}s`);
                    }
                    
                    // Speak the complete message
                    if (this.voiceChat && this.currentMessage) {
                        // Detect language from message for TTS
                        const detectedLang = this.detectLanguageFromText(this.currentMessage);
                        this.voiceChat.speak(this.currentMessage, detectedLang);
                    }
                    
                    // Reset to idle after a delay
                    setTimeout(() => this.setAvatarState('idle'), 2000);
                } else if (event.state === 'error') {
                    this.setAvatarState('error');
                    contentElement.textContent = this.currentMessage + '\n\n[Error: ' + event.message + ']';
                }
                break;
        }
    }
    
    createMessageElement(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        metaDiv.textContent = role === 'user' ? 'You' : 'Assistant';
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(metaDiv);
        
        return messageDiv;
    }
    
    addMessage(content, role) {
        const messagesContainer = document.getElementById('messages');
        const messageElement = this.createMessageElement(content, role);
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    setAvatarState(state) {
        const avatar = document.getElementById('avatar');
        const avatarState = document.getElementById('avatarState');
        
        // Remove all state classes
        avatar.className = 'avatar';
        
        // Add new state class
        if (state !== 'idle') {
            avatar.classList.add(state);
        }
        
        avatarState.textContent = state;
    }
    
    updateStatus(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }
    
    detectLanguageFromText(text) {
        // Simple language detection based on Devanagari script
        const devanagariRegex = /[\u0900-\u097F]/;
        const devanagariCount = (text.match(devanagariRegex) || []).length;
        const totalChars = text.replace(/\s/g, '').length;
        
        if (totalChars === 0) {
            return 'en';
        }
        
        const devanagariRatio = devanagariCount / totalChars;
        
        if (devanagariCount === 0) {
            return 'en';
        } else if (devanagariRatio > 0.3) {
            return 'hi';
        } else {
            return 'en'; // Default to English for mixed content
        }
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ChatApp();
    });
} else {
    new ChatApp();
}

