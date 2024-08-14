// HTML elements selection
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const micButton = document.getElementById('mic-button');
const chatMessages = document.getElementById('chat-messages');
const micStatus = document.getElementById('mic-status'); // For microphone status message

// New buttons for voice control
const pauseVoiceButton = document.getElementById('pause-voice-button'); // Pause button element
const resumeVoiceButton = document.getElementById('resume-voice-button'); // Resume button element


// Web Speech API for Speech Recognition (Speech-to-Text)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;
let isListening = false; // Flag to track if microphone is actively listening

// Web Speech API for Speech Synthesis (Text-to-Speech)
const synth = window.speechSynthesis;
let currentUtterance = null; // To keep track of the current speech utterance
let availableVoices = []; // Array to store available voices

// Populate available voices once they are loaded
// This event might fire before DOMContentLoaded, so listen early
synth.onvoiceschanged = () => {
    availableVoices = synth.getVoices();
    console.log("Available voices:", availableVoices);
    // You can inspect this array in the console to pick a preferred voice.
    // For example, to find an English (US) female voice:
    // let preferredVoice = availableVoices.find(voice => voice.lang === 'en-US' && voice.name.includes('Google US English'));
};


// Function to initialize the chat interface (bot's welcome message)
async function startChat() {
    try {
        // URL is made absolute using window.location.origin
        const response = await fetch(`${window.location.origin}/start`, {
            method: 'GET',
        });
        
        // Ensure the response is JSON before parsing
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const errorText = await response.text();
            console.error("Backend returned non-JSON for /start:", errorText);
            addMessage('Backend error: Could not start chat. Expected JSON, got HTML or plain text. Please check server logs.', 'bot');
            if (micStatus) { 
                micStatus.textContent = "Error occurred."; 
            }
            return;
        }

        const data = await response.json();
        addMessage(data.response, 'bot'); // Display the bot's first message
        speakMessage(data.response); // Make the bot speak its welcome message
    } catch (error) {
        console.error('Error starting chat:', error);
        addMessage('Sorry, the chat could not be started.', 'bot');
        if (micStatus) { 
            micStatus.textContent = "Error starting chat.";
        }
        // Ensure mic is active for user input if chat fails to start and recognition is supported
        if (recognition && !isListening) {
            if (micButton) { 
                 micButton.classList.remove('bg-gray-400', 'cursor-not-allowed');
            }
            try {
                recognition.start();
            } catch (e) {
                console.error("Error restarting microphone after chat start error:", e);
            }
        }
    }
}

// Function to add a message to the chat box
function addMessage(text, sender) {
    const messageWrapper = document.createElement('div');
    messageWrapper.classList.add('flex', 'mb-4', 'items-end'); 

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('p-3', 'rounded-xl', 'max-w-[80%]', 'break-words', 'relative', 'message-bubble', 'shadow-md'); 
    messageDiv.textContent = text;

    // Sender specific styles
    if (sender === 'user') {
        messageDiv.classList.add('bg-blue-500', 'text-white', 'ml-auto', 'rounded-br-none', 'user-message');
        messageWrapper.classList.add('justify-end'); 
    } else {
        messageDiv.classList.add('bg-gray-200', 'text-gray-800', 'rounded-bl-none', 'bot-message');
        messageWrapper.classList.add('justify-start'); 
    }

    messageWrapper.appendChild(messageDiv);
    chatMessages.appendChild(messageWrapper);

    // Auto-scroll to the bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Function to make the bot speak the message using Web Speech API (SpeechSynthesis)
function speakMessage(text) {
    if (synth.speaking) { // If bot is already speaking, stop it
        synth.cancel();
    }
    currentUtterance = new SpeechSynthesisUtterance(text);
    currentUtterance.lang = 'en-US'; // Set speech language to English. (Change to 'tr-TR' for Turkish if needed.)

    // --- Voice Customization (Web Speech API) ---
    // You can pick a specific voice here. Open your browser's console (F12)
    // and inspect the 'availableVoices' array after the page loads to see options.
    // Example for a potentially more natural voice:
    const selectedVoice = availableVoices.find(voice => 
        voice.lang === 'en-US' && 
        (voice.name.includes('Google US English') || 
         voice.name.includes('Microsoft Zira') || 
         voice.name.includes('Samantha')) // Example voice names
    );
    if (selectedVoice) {
        currentUtterance.voice = selectedVoice;
    } else {
        console.warn('Preferred voice not found, using default. Check availableVoices array in console.');
    }

    currentUtterance.pitch = 1.0; // Adjust pitch (0 to 2, 1 is default)
    currentUtterance.rate = 1.0; // Adjust speaking rate (0.1 to 10, 1 is default)
    // --- End Voice Customization ---


    // Event listener for when the bot finishes speaking
    currentUtterance.onend = () => {
        console.log('Bot finished speaking. Re-enabling microphone if not listening.');
        // After bot finishes speaking, automatically start listening again if not already listening
        if (recognition && !isListening) {
             if (micButton) { 
                micButton.classList.remove('bg-gray-400', 'cursor-not-allowed');
             }
             try {
                recognition.start(); // Restart listening
             } catch (e) {
                 console.error("Error restarting microphone after speech:", e);
                 if (micStatus) {
                    micStatus.textContent = "Error restarting microphone.";
                 }
             }
        } else if (!recognition) {
            if (micStatus) {
                micStatus.textContent = "Your browser does not support speech recognition.";
            }
        } else {
            if (micStatus) {
                micStatus.textContent = "Press the microphone button to start speaking.";
            }
        }
    };

    currentUtterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        if (micStatus) {
            micStatus.textContent = "Error speaking response.";
        }
        // Even on error, try to enable microphone for user input
        if (recognition && !isListening) {
            if (micButton) {
                micButton.classList.remove('bg-gray-400', 'cursor-not-allowed');
            }
            try {
                recognition.start();
            } catch (e) {
                console.error("Error restarting microphone after speech error:", e);
            }
        }
    };

    synth.speak(currentUtterance);
    if (micStatus) {
        micStatus.textContent = "Bot is speaking...";
    }
    // When bot starts speaking, stop the microphone from listening
    if (recognition && isListening) {
        recognition.stop();
        if (micButton) {
            micButton.classList.add('bg-gray-400', 'cursor-not-allowed'); // Visually disable mic button
        }
    }
}

// Function to pause bot speech
function pauseVoice() {
    if (synth.speaking && !synth.paused) {
        synth.pause();
        if (micStatus) {
            micStatus.textContent = "Bot voice paused.";
        }
        console.log("Bot voice paused.");
    }
}

// Function to resume bot speech
function resumeVoice() {
    if (synth.paused) {
        synth.resume();
        if (micStatus) {
            micStatus.textContent = "Bot is speaking...";
        }
        console.log("Bot voice resumed.");
    }
}


// Function to send message (for both text input and speech recognition text)
async function sendMessage(messageFromSpeech = null) {
    let message;
    if (messageFromSpeech !== null) {
        message = messageFromSpeech.trim(); // Use message from speech recognition
        if (userInput) { 
            userInput.value = message; // Update the text input field with the transcribed text
        }
    } else {
        if (userInput) { 
            message = userInput.value.trim(); // Use message from text input
        } else {
            message = ''; 
        }
    }

    if (message === '') return;

    // Stop current bot speech if any when user is about to send a message
    if (synth.speaking) { // Use synth.speaking for Web Speech API
        synth.cancel();
    }

    addMessage(message, 'user');
    if (userInput) { 
        userInput.value = ''; // Clear the message input box after sending
    }

    // Display a "bot thinking" message
    const thinkingMessageWrapper = document.createElement('div');
    thinkingMessageWrapper.classList.add('flex', 'mb-4', 'items-end', 'justify-start'); 
    const thinkingMessageDiv = document.createElement('div');
    thinkingMessageDiv.classList.add('p-3', 'rounded-xl', 'bg-gray-200', 'text-gray-800', 'max-w-[80%]', 'break-words', 'rounded-bl-none', 'shadow-md');
    thinkingMessageDiv.innerHTML = '<span class="animate-pulse">Bot thinking...</span>';
    chatMessages.appendChild(thinkingMessageWrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight; 

    try {
        // URL is made absolute using window.location.origin
        const response = await fetch(`${window.location.origin}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        });

        // Ensure the response is JSON before parsing
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const errorText = await response.text();
            console.error("Backend returned non-JSON for /chat:", errorText);
            chatMessages.removeChild(thinkingMessageWrapper);
            addMessage('Backend error: Response could not be retrieved. Expected JSON, got HTML or plain text. Please check server logs.', 'bot');
            if (micStatus) { 
                micStatus.textContent = "Error occurred.";
            }
            return;
        }

        const data = await response.json();
        
        // Remove the thinking message and add the actual response
        chatMessages.removeChild(thinkingMessageWrapper);
        addMessage(data.response, 'bot');
        // Bot speaks its response using Web Speech API
        speakMessage(data.response); 
        
    } catch (error) {
        console.error('Error sending message:', error);
        chatMessages.removeChild(thinkingMessageWrapper); // Remove thinking message even on error
        addMessage('Sorry, I cannot respond at the moment.', 'bot');
        if (micStatus) { 
            micStatus.textContent = "Error processing request.";
        }
        // On error, make sure mic is enabled for user input
        if (recognition && !isListening) {
            if (micButton) { 
                micButton.classList.remove('bg-gray-400', 'cursor-not-allowed');
            }
            try {
                recognition.start();
            } catch (e) {
                console.error("Error restarting microphone after send message error:", e);
            }
        }
    }
}

// ---- Speech Recognition (Web Speech API) Code ----
// Initial status update for micStatus on load.
// This ensures micStatus has a default text even before startChat finishes or if recognition is unsupported.
if (micStatus) {
    micStatus.textContent = "Press the microphone button to start speaking.";
}


// Check if Web Speech API is supported
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false; 
    recognition.lang = 'en-US'; // Set language to English. (Change to 'tr-TR' for Turkish if needed)
    recognition.interimResults = false; 

    // When speech recognition starts
    recognition.onstart = () => {
        isListening = true;
        if (micButton) { 
            micButton.classList.add('bg-red-700', 'animate-pulse'); 
        }
        if (micStatus) { 
            micStatus.textContent = "Listening... Please speak.";
        }
        if (userInput) { 
            userInput.placeholder = "Listening... Please speak."; 
        }
    };

    // When speech recognition ends
    recognition.onend = () => {
        isListening = false;
        if (micButton) { 
            micButton.classList.remove('bg-red-700', 'animate-pulse');
        }
        // Only set status if bot is not currently speaking
        if (!synth.speaking) { 
            if (micStatus) { 
                micStatus.textContent = "Press the microphone button to start speaking.";
            }
            if (userInput) { 
                userInput.placeholder = "Type your message or press the microphone..."; 
            }
        }
    };

    // When an error occurs
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isListening = false;
        if (micButton) { 
            micButton.classList.remove('bg-red-700', 'animate-pulse');
        }
        if (micStatus) { 
            micStatus.textContent = "An error occurred. Please try again.";
        }
        if (userInput) { 
            userInput.placeholder = "Type your message or press the microphone..."; 
        }
        
        let errorMessage = '';
        if (event.error === 'no-speech') {
            if (micStatus) { 
                micStatus.textContent = "No speech detected. Please try again.";
            }
        } else if (event.error === 'not-allowed') {
            errorMessage = 'Microphone access denied. Please allow it in your browser settings.';
            addMessage(errorMessage, 'bot'); 
            if (micStatus) { 
                micStatus.textContent = "Microphone permission required.";
            }
        } else if (event.error === 'network') {
            errorMessage = 'Network error. Speech recognition is not working currently.';
            addMessage(errorMessage, 'bot');
            if (micStatus) { 
                micStatus.textContent = "Network error.";
            }
        } else {
            errorMessage = 'A speech recognition error occurred: ' + event.error;
            addMessage(errorMessage, 'bot');
            if (micStatus) { 
                micStatus.textContent = "Error: " + event.error;
            }
        }
    };

    // When results are available
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript.trim() !== '') { 
            sendMessage(transcript); 
        } else {
            if (micStatus) { 
                micStatus.textContent = "Empty speech detected. Please try again.";
            }
        }
    };

    // Click event for microphone button
    if (micButton) { 
        micButton.addEventListener('click', () => {
            if (isListening) {
                recognition.stop(); 
            } else {
                // If bot is speaking, stop it before starting recognition
                if (synth.speaking) { 
                    synth.cancel();
                }
                try {
                    recognition.start(); 
                } catch (e) {
                    console.error("Error starting microphone:", e);
                    addMessage('Microphone could not be started. Please check if it\'s already listening or your browser permissions.', 'bot');
                    if (micStatus) { 
                        micStatus.textContent = "Microphone start error.";
                    }
                }
            }
        });
    }

} else {
    // If browser does not support Web Speech API
    if (micButton) { 
        micButton.disabled = true;
        micButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                            </svg>`; 
        micButton.classList.remove('bg-red-500', 'hover:bg-red-600');
        micButton.classList.add('bg-gray-400', 'cursor-not-allowed');
    }
    if (micStatus) { 
        micStatus.textContent = "Your browser does not support speech recognition.";
    }
    if (userInput) { 
        userInput.placeholder = "Voice input unavailable. Use text input."; 
    }
    console.warn('Your browser does not support the Web Speech API. Voice input feature is unavailable.');
    
    const unsupportedBrowserText = 'Your browser does not fully support voice features. Please use text input or a modern browser like Chrome or Edge.';
    addMessage(unsupportedBrowserText, 'bot');
}

// Event listener for sending text message on button click
if (sendButton) { 
    sendButton.addEventListener('click', () => sendMessage(null)); 
}

// Event listener for sending text message on Enter key press in input field
if (userInput) { 
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); 
            sendMessage(null); 
        }
    });
}

// New event listeners for pause and resume buttons
if (pauseVoiceButton) {
    pauseVoiceButton.addEventListener('click', pauseVoice);
}

if (resumeVoiceButton) {
    resumeVoiceButton.addEventListener('click', resumeVoice);
}


// Start chat when the page loads (display bot's first message)
document.addEventListener('DOMContentLoaded', startChat);
