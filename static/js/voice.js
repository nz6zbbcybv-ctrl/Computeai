/**
 * Voice chat functionality using Web Speech API.
 * Supports Hindi and English for both speech-to-text and text-to-speech.
 */
class VoiceChat {
    constructor() {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isRecording = false;
        this.currentUtterance = null;
        this.voiceLanguage = 'en';
        this.voiceOutputEnabled = true;
        
        this.init();
    }
    
    init() {
        // Check browser support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Speech recognition not supported in this browser');
            return;
        }
        
        // Initialize speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        
        // Set up recognition event handlers
        this.recognition.onstart = () => {
            this.isRecording = true;
            this.updateRecordingUI(true);
        };
        
        this.recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            this.handleTranscript(transcript, event.results[event.results.length - 1].isFinal);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.handleRecognitionError(event.error);
            this.stopRecording();
        };
        
        this.recognition.onend = () => {
            this.isRecording = false;
            this.updateRecordingUI(false);
        };
        
        // Load available voices
        this.loadVoices();
        this.synthesis.onvoiceschanged = () => this.loadVoices();
    }
    
    loadVoices() {
        this.voices = this.synthesis.getVoices();
    }
    
    getVoiceForLanguage(language) {
        if (!this.voices || this.voices.length === 0) {
            return null;
        }
        
        // Prefer native voices for the language
        const langCode = language === 'hi' ? 'hi-IN' : 'en-US';
        const langPrefix = language === 'hi' ? 'hi' : 'en';
        
        // Try to find a voice matching the language
        let voice = this.voices.find(v => 
            v.lang.startsWith(langCode) || v.lang.startsWith(langPrefix)
        );
        
        // Fallback to any available voice
        if (!voice) {
            voice = this.voices.find(v => v.lang.includes(langPrefix)) || this.voices[0];
        }
        
        return voice;
    }
    
    setLanguage(language) {
        this.voiceLanguage = language;
        if (this.recognition) {
            // Set recognition language
            const langCode = language === 'hi' ? 'hi-IN' : 'en-US';
            this.recognition.lang = langCode;
        }
    }
    
    startRecording() {
        if (!this.recognition) {
            this.showVoiceStatus('Speech recognition not supported in this browser', 'error');
            return;
        }
        
        if (this.isRecording) {
            this.stopRecording();
            return;
        }
        
        try {
            this.recognition.start();
            this.showVoiceStatus('Listening...', 'listening');
        } catch (error) {
            console.error('Failed to start recognition:', error);
            this.showVoiceStatus('Failed to start recording', 'error');
        }
    }
    
    stopRecording() {
        if (this.recognition && this.isRecording) {
            this.recognition.stop();
        }
    }
    
    handleTranscript(transcript, isFinal) {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            if (isFinal) {
                messageInput.value = transcript.trim();
                this.showVoiceStatus('Transcript ready', 'success');
                // Auto-send if there's content
                setTimeout(() => {
                    this.showVoiceStatus('', '');
                }, 1000);
            } else {
                // Show interim results
                this.showVoiceStatus(`Listening: ${transcript}`, 'listening');
            }
        }
    }
    
    handleRecognitionError(error) {
        let message = 'Recording error';
        switch (error) {
            case 'no-speech':
                message = 'No speech detected';
                break;
            case 'audio-capture':
                message = 'Microphone not found';
                break;
            case 'not-allowed':
                message = 'Microphone permission denied';
                break;
            case 'network':
                message = 'Network error';
                break;
        }
        this.showVoiceStatus(message, 'error');
    }
    
    speak(text, language = null) {
        if (!this.voiceOutputEnabled || !this.synthesis) {
            return;
        }
        
        // Cancel any ongoing speech
        if (this.currentUtterance) {
            this.synthesis.cancel();
        }
        
        const lang = language || this.voiceLanguage;
        const voice = this.getVoiceForLanguage(lang);
        
        if (!voice) {
            console.warn('No voice available for language:', lang);
            return;
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.voice = voice;
        utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-US';
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        utterance.onstart = () => {
            console.log('Speech started');
        };
        
        utterance.onend = () => {
            this.currentUtterance = null;
            console.log('Speech ended');
        };
        
        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event.error);
            this.currentUtterance = null;
        };
        
        this.currentUtterance = utterance;
        this.synthesis.speak(utterance);
    }
    
    stopSpeaking() {
        if (this.synthesis) {
            this.synthesis.cancel();
            this.currentUtterance = null;
        }
    }
    
    updateRecordingUI(recording) {
        const button = document.getElementById('voiceRecordButton');
        if (button) {
            if (recording) {
                button.classList.add('recording');
                button.title = 'Click to stop recording';
            } else {
                button.classList.remove('recording');
                button.title = 'Hold to record';
            }
        }
    }
    
    showVoiceStatus(message, type = '') {
        const statusEl = document.getElementById('voiceStatus');
        const statusTextEl = document.getElementById('voiceStatusText');
        
        if (!statusEl || !statusTextEl) {
            return;
        }
        
        if (message) {
            statusTextEl.textContent = message;
            statusEl.style.display = 'block';
            statusEl.className = `voice-status ${type}`;
        } else {
            statusEl.style.display = 'none';
        }
    }
    
    setVoiceOutputEnabled(enabled) {
        this.voiceOutputEnabled = enabled;
        if (!enabled) {
            this.stopSpeaking();
        }
    }
}

// Export for use in app.js
if (typeof window !== 'undefined') {
    window.VoiceChat = VoiceChat;
}

