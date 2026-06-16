/*
  app.js
  J.A.R.V.I.S Cybernetic Dashboard Controller
  Manages UI interactions, clocks, active polling, API requests, 
  and webcam integrations.
*/

document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const currentTimeEl = document.getElementById("current-time");
    const currentDateEl = document.getElementById("current-date");
    
    // Header Weather Elements
    const headerTempEl = document.getElementById("header-temp");
    const headerLocationEl = document.getElementById("header-location");
    
    // Card Weather Elements
    const weatherTempEl = document.getElementById("weather-temp-val");
    const weatherLocationEl = document.getElementById("weather-location-val");
    const weatherDescEl = document.getElementById("weather-desc-val");
    const weatherHumidityEl = document.getElementById("weather-humidity-val");
    const weatherWindEl = document.getElementById("weather-wind-val");
    const weatherFeelsEl = document.getElementById("weather-feels-val");
    
    // System Metrics Elements
    const cpuProgress = document.getElementById("cpu-progress");
    const cpuPercentLabel = document.getElementById("cpu-percent-label");
    const ramProgress = document.getElementById("ram-progress");
    const ramUsedLabel = document.getElementById("ram-used-label");
    const cpuStatVal = document.getElementById("cpu-stat-val");
    const ramStatVal = document.getElementById("ram-stat-val");
    const diskStatVal = document.getElementById("disk-stat-val");
    
    // Assistant Elements
    const assistantStatusText = document.getElementById("assistant-status-text");
    const assistantStatusPill = document.getElementById("assistant-status-pill");
    const jarvisVoiceOrb = document.getElementById("jarvis-voice-orb");
    
    // Uptime and Commands
    const uptimeCounter = document.getElementById("uptime-counter");
    const uptimeMini = document.getElementById("uptime-mini");
    const commandsExecutedVal = document.getElementById("commands-executed-val");
    const systemLoadText = document.getElementById("system-load-text");
    const loadProgressBar = document.getElementById("load-progress-bar");
    
    // Chat Elements
    const chatMessagesContainer = document.getElementById("chat-messages-container");
    const chatInputField = document.getElementById("chat-input-field");
    const chatSendBtn = document.getElementById("chat-send-btn");
    const clearChatBtn = document.getElementById("clear-chat-btn");
    const exportChatBtn = document.getElementById("export-chat-btn");
    
    // Control Buttons
    const micTriggerBtn = document.getElementById("mic-trigger-btn");
    const keyboardFocusBtn = document.getElementById("keyboard-focus-btn");
    const cameraPowerBtn = document.getElementById("camera-power-btn");
    const cameraPowerHeader = document.getElementById("toggle-camera-btn-header");
    
    // Camera Elements
    const cameraFeed = document.getElementById("camera-feed");
    const webcamVideo = document.getElementById("webcam-video");
    const cameraMsg = document.getElementById("camera-msg");
    const cameraHUD = cameraFeed.querySelector(".camera-hud-overlay");
    const cameraOffOverlay = cameraFeed.querySelector(".camera-off-overlay");
    
    // Camera Stream Variable
    let webcamStream = null;
    let cameraActive = false;

    // Start-up message time setup
    const startMsgTime = document.getElementById("start-msg-time");
    if (startMsgTime) {
        startMsgTime.textContent = formatTime(new Date());
    }

    // Initialize systems
    initClock();
    fetchWeather();
    pollStatus();
    setInterval(pollStatus, 1500); // Poll every 1.5 seconds

    // ==========================================
    // CLOCK MANAGER
    // ==========================================
    function initClock() {
        updateClock();
        setInterval(updateClock, 1000);
    }

    function updateClock() {
        const now = new Date();
        currentTimeEl.textContent = formatTime(now);
        currentDateEl.textContent = formatDate(now);
    }

    function formatTime(date) {
        let hours = date.getHours();
        let minutes = date.getMinutes();
        let seconds = date.getSeconds();
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // 12 instead of 0
        minutes = minutes < 10 ? '0'+minutes : minutes;
        seconds = seconds < 10 ? '0'+seconds : seconds;
        return `${hours}:${minutes}:${seconds} ${ampm}`;
    }

    function formatDate(date) {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    // ==========================================
    // WEATHER FETCH
    // ==========================================
    function fetchWeather() {
        fetch("/api/weather")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    // Header weather
                    headerTempEl.textContent = `${data.temperature}°C`;
                    headerLocationEl.textContent = data.location;
                    
                    // Card weather
                    weatherTempEl.textContent = `${data.temperature}°C`;
                    weatherLocationEl.textContent = data.location;
                    weatherDescEl.textContent = data.condition;
                    weatherHumidityEl.textContent = `${data.humidity}%`;
                    weatherWindEl.textContent = `${data.wind_speed} m/s`;
                    weatherFeelsEl.textContent = `${data.feels_like}°C`;
                }
            })
            .catch(err => console.error("Error fetching weather:", err));
    }

    // ==========================================
    // METRICS POLLING
    // ==========================================
    function pollStatus() {
        fetch("/api/status")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    // Update Assistant Status Text & Classes
                    const statusStr = data.assistant_status;
                    assistantStatusText.textContent = statusStr;
                    updateOrbState(statusStr);
                    
                    // Uptime & Counters
                    uptimeCounter.textContent = data.uptime;
                    uptimeMini.textContent = data.uptime;
                    commandsExecutedVal.textContent = data.commands_executed;
                    
                    // System Performance Metrics
                    const m = data.metrics;
                    
                    // CPU progress
                    cpuProgress.style.width = `${m.cpu_percent}%`;
                    cpuPercentLabel.textContent = `${m.cpu_percent}%`;
                    cpuStatVal.textContent = `${m.cpu_percent}%`;
                    
                    // RAM progress
                    ramProgress.style.width = `${m.ram_percent}%`;
                    ramUsedLabel.textContent = `${m.ram_used_gb} GB`;
                    ramStatVal.textContent = `${m.ram_percent}%`;
                    
                    // Disk stats
                    diskStatVal.textContent = `${m.disk_used_gb}/${m.disk_total_gb} GB`;

                    // Dynamic system load calculation
                    updateSystemLoad(m.cpu_percent);
                }
            })
            .catch(err => console.error("Error polling status:", err));
    }

    function updateOrbState(status) {
        jarvisVoiceOrb.className = "voice-orb"; // Clear states
        
        const lowerStatus = status.toLowerCase();
        if (lowerStatus.includes("listening")) {
            jarvisVoiceOrb.classList.add("listening");
        } else if (lowerStatus.includes("speaking") || lowerStatus.includes("speak")) {
            jarvisVoiceOrb.classList.add("speaking");
        } else if (lowerStatus.includes("processing") || lowerStatus.includes("searching")) {
            jarvisVoiceOrb.classList.add("processing");
        }
    }

    function updateSystemLoad(cpu) {
        let load = "Low";
        let fillClass = "progress-bar-fill";
        let textClass = "load-text";

        if (cpu > 60) {
            load = "High";
            fillClass += " load-fill-high"; // We can define these red fills
            textClass += " load-high";
            loadProgressBar.style.background = "#ff3333";
        } else if (cpu > 25) {
            load = "Moderate";
            fillClass += " load-fill-moderate";
            textClass += " load-moderate";
            loadProgressBar.style.background = "#ffcc00";
        } else {
            load = "Low";
            loadProgressBar.style.background = "#00ff7f";
        }

        systemLoadText.textContent = load;
        systemLoadText.className = textClass;
        loadProgressBar.style.width = `${cpu + 10}%`; // simulation padding
    }

    // ==========================================
    // BROWSER-SIDE TEXT-TO-SPEECH (SPEECH SYNTHESIS)
    // ==========================================
    let synthesisActive = false;

    // Load voices
    if ('speechSynthesis' in window) {
        window.speechSynthesis.getVoices();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = () => {
                window.speechSynthesis.getVoices();
            };
        }
    }

    function speakText(text) {
        if (!('speechSynthesis' in window)) {
            console.warn("Speech synthesis is not supported in this browser.");
            return;
        }

        // Stop any currently playing speech
        window.speechSynthesis.cancel();

        // Clean text (remove brackets/meta info)
        let cleanText = text.replace(/\[Simulation Mode\]/gi, "").trim();
        if (!cleanText) return;

        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Try to get dynamic voices list
        const voices = window.speechSynthesis.getVoices();
        let englishVoice = voices.find(v => v.lang.includes("en-US") || v.lang.includes("en-GB"));
        
        if (englishVoice) {
            utterance.voice = englishVoice;
        }
        
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        utterance.onstart = () => {
            synthesisActive = true;
            assistantStatusText.textContent = "Speaking...";
            jarvisVoiceOrb.className = "voice-orb";
            jarvisVoiceOrb.classList.add("speaking");
        };

        utterance.onend = () => {
            synthesisActive = false;
            assistantStatusText.textContent = "Listening for wake word...";
            jarvisVoiceOrb.className = "voice-orb";
        };

        utterance.onerror = () => {
            synthesisActive = false;
            assistantStatusText.textContent = "Listening for wake word...";
            jarvisVoiceOrb.className = "voice-orb";
        };

        window.speechSynthesis.speak(utterance);
    }

    // ==========================================
    // CONVERSATION MANAGER (CHAT)
    // ==========================================
    function appendMessage(sender, text) {
        const timeStr = formatTime(new Date());
        
        const msgWrapper = document.createElement("div");
        msgWrapper.classList.add("chat-message");
        msgWrapper.classList.add(sender === "jarvis" ? "jarvis-msg" : "user-msg");
        
        const bubble = document.createElement("div");
        bubble.classList.add("msg-bubble");
        bubble.textContent = text;
        
        const timeSpan = document.createElement("span");
        timeSpan.classList.add("msg-time");
        timeSpan.textContent = timeStr;
        
        msgWrapper.appendChild(bubble);
        msgWrapper.appendChild(timeSpan);
        
        chatMessagesContainer.appendChild(msgWrapper);
        // Scroll to bottom
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    }

    function sendMessage() {
        const text = chatInputField.value.trim();
        if (!text) return;
        
        // Append user query to UI
        appendMessage("user", text);
        chatInputField.value = "";
        
        // Disable send button during processing
        chatSendBtn.disabled = true;

        fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                appendMessage("jarvis", data.reply);
                speakText(data.reply);
            } else {
                appendMessage("jarvis", "Ameer, backend error aa raha hai.");
            }
        })
        .catch(err => {
            console.error("Error sending chat:", err);
            appendMessage("jarvis", "Connection error, Ameer.");
        })
        .finally(() => {
            chatSendBtn.disabled = false;
        });
    }

    // Chat event listeners
    chatSendBtn.addEventListener("click", sendMessage);
    chatInputField.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    clearChatBtn.addEventListener("click", () => {
        chatMessagesContainer.innerHTML = "";
        appendMessage("jarvis", "Conversation history cleared.");
    });

    exportChatBtn.addEventListener("click", () => {
        const bubbles = chatMessagesContainer.querySelectorAll(".chat-message");
        let conversationText = "=== J.A.R.V.I.S Conversation Log ===\n";
        conversationText += `Date: ${new Date().toLocaleDateString()}\n\n`;
        
        bubbles.forEach(bubble => {
            const role = bubble.classList.contains("jarvis-msg") ? "Jarvis" : "Ameer";
            const text = bubble.querySelector(".msg-bubble").textContent;
            const time = bubble.querySelector(".msg-time").textContent;
            conversationText += `[${time}] ${role}: ${text}\n`;
        });
        
        const blob = new Blob([conversationText], { type: "text/plain;charset=utf-8" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `jarvis_conversation_${Date.now()}.txt`;
        a.click();
    });

    // Keyboard focus toggle
    keyboardFocusBtn.addEventListener("click", () => {
        chatInputField.focus();
        // Visual indicator
        keyboardFocusBtn.classList.add("active");
        setTimeout(() => keyboardFocusBtn.classList.remove("active"), 400);
    });

    // ==========================================
    // MICROPHONE TRIGGER (BROWSER ASR WITH BACKEND FALLBACK)
    // ==========================================
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let browserRecognition = null;

    if (SpeechRecognition) {
        browserRecognition = new SpeechRecognition();
        browserRecognition.continuous = false;
        browserRecognition.lang = 'en-US'; // Works well for Hinglish too
        browserRecognition.interimResults = false;

        browserRecognition.onstart = () => {
            micTriggerBtn.classList.add("active");
            assistantStatusText.textContent = "Listening (Browser Mic)...";
            jarvisVoiceOrb.className = "voice-orb";
            jarvisVoiceOrb.classList.add("listening");
        };

        browserRecognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (transcript.trim()) {
                console.log("[Browser Voice] Transcribed text: ", transcript);
                
                // Strip wake word "hey jarvis" if spoken
                let cleanTranscript = transcript.trim();
                let lowerText = cleanTranscript.toLowerCase();
                const wakeWord = "hey jarvis";
                if (lowerText.startsWith(wakeWord)) {
                    cleanTranscript = cleanTranscript.substring(wakeWord.length).trim().replace(/^[,.?! ]+/, "");
                }
                
                if (cleanTranscript) {
                    appendMessage("user", cleanTranscript);
                    
                    // Send text to backend chat API
                    assistantStatusText.textContent = "Processing...";
                    jarvisVoiceOrb.className = "voice-orb";
                    jarvisVoiceOrb.classList.add("processing");
                    
                    fetch("/api/chat", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ message: cleanTranscript })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.status === "success") {
                            appendMessage("jarvis", data.reply);
                            speakText(data.reply);
                        } else {
                            appendMessage("jarvis", "Ameer, backend error aa raha hai.");
                        }
                    })
                    .catch(err => {
                        console.error("Error sending browser chat:", err);
                        appendMessage("jarvis", "Connection error, Ameer.");
                    });
                } else {
                    // Spoke only "hey jarvis"
                    const reply = "Ji Ameer, boliye? Main sun raha hoon.";
                    appendMessage("jarvis", reply);
                    speakText(reply);
                }
            }
        };

        browserRecognition.onerror = (event) => {
            console.warn("[Browser Voice] Speech recognition error: ", event.error);
            // If browser mic permission is denied or blocked, fall back to backend mic trigger
            if (event.error === 'not-allowed') {
                triggerBackendVoiceCapture();
            } else {
                assistantStatusText.textContent = "Listening for wake word...";
                jarvisVoiceOrb.className = "voice-orb";
                micTriggerBtn.classList.remove("active");
            }
        };

        browserRecognition.onend = () => {
            micTriggerBtn.classList.remove("active");
        };
    }

    function triggerBackendVoiceCapture() {
        // Trigger visual orb state
        assistantStatusText.textContent = "Listening (PC Mic)...";
        jarvisVoiceOrb.className = "voice-orb";
        jarvisVoiceOrb.classList.add("listening");
        micTriggerBtn.classList.add("active");
        
        fetch("/api/trigger_voice", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    if (data.user_text) {
                        appendMessage("user", data.user_text);
                        appendMessage("jarvis", data.reply);
                    } else {
                        appendMessage("jarvis", data.reply);
                    }
                    speakText(data.reply);
                } else if (data.status === "warning") {
                    appendMessage("jarvis", data.message);
                } else {
                    appendMessage("jarvis", "Voice capture error: " + (data.message || "Unknown error"));
                }
            })
            .catch(err => {
                console.error("Error triggering voice capture:", err);
                appendMessage("jarvis", "Failed to contact voice capture server, Ameer.");
            })
            .finally(() => {
                micTriggerBtn.classList.remove("active");
                assistantStatusText.textContent = "Listening for wake word...";
                jarvisVoiceOrb.className = "voice-orb";
            });
    }

    // Toggle trigger: try browser mic first, fallback to PC mic
    micTriggerBtn.addEventListener("click", () => {
        if (browserRecognition) {
            try {
                browserRecognition.start();
            } catch (e) {
                // If already running or throws error, try backend mic
                console.log("[Browser Voice] Browser mic start failed, falling back to PC mic...");
                triggerBackendVoiceCapture();
            }
        } else {
            triggerBackendVoiceCapture();
        }
    });

    // ==========================================
    // WEBCAM CONTROLLER
    // ==========================================
    function toggleWebcam() {
        if (!cameraActive) {
            // Activate camera
            cameraActive = true;
            cameraPowerBtn.classList.add("active");
            cameraPowerHeader.classList.add("active");
            cameraOffOverlay.style.display = "none";
            webcamVideo.style.display = "block";
            cameraHUD.style.display = "block";
            cameraMsg.textContent = "Webcam active. SCANNING SYSTEM...";

            // Access browser media device webcam
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 180 } })
                    .then(stream => {
                        webcamStream = stream;
                        webcamVideo.srcObject = stream;
                    })
                    .catch(err => {
                        console.warn("Could not access camera hardware:", err);
                        cameraMsg.textContent = "Hardware camera access blocked. Simulating grid scanning...";
                        showMockStaticScanning();
                    });
            } else {
                showMockStaticScanning();
            }
        } else {
            // Deactivate camera
            cameraActive = false;
            cameraPowerBtn.classList.remove("active");
            cameraPowerHeader.classList.remove("active");
            cameraOffOverlay.style.display = "flex";
            webcamVideo.style.display = "none";
            cameraHUD.style.display = "none";
            cameraMsg.textContent = "Camera is inactive. Click the power button to start.";

            if (webcamStream) {
                webcamStream.getTracks().forEach(track => track.stop());
                webcamStream = null;
            }
        }
        
        // Sync with backend API toggler state
        fetch("/api/toggle_camera", { method: "POST" }).catch(() => {});
    }

    function showMockStaticScanning() {
        // Shows fallback cyber scanning indicator
        webcamVideo.style.display = "none";
        // We can just keep HUD running on a dark blue canvas, or draw mock waves
        const canvas = document.getElementById("webcam-canvas");
        canvas.style.display = "block";
        const ctx = canvas.getContext("2d");
        
        canvas.width = 320;
        canvas.height = 180;
        
        // Draw static cyber scanner target grids
        function drawGrid() {
            if (!cameraActive) return;
            ctx.fillStyle = "rgba(6, 12, 24, 0.4)";
            ctx.fillRect(0, 0, 320, 180);
            
            // Draw crosshairs
            ctx.strokeStyle = "rgba(0, 240, 255, 0.25)";
            ctx.lineWidth = 1;
            
            ctx.beginPath();
            ctx.moveTo(160, 20); ctx.lineTo(160, 160);
            ctx.moveTo(30, 90); ctx.lineTo(290, 90);
            ctx.stroke();
            
            // Draw circle grid
            ctx.beginPath();
            ctx.arc(160, 90, 45, 0, 2 * Math.PI);
            ctx.arc(160, 90, 15, 0, 2 * Math.PI);
            ctx.stroke();

            // Draw noise / dots
            ctx.fillStyle = "rgba(0, 240, 255, 0.1)";
            for (let i = 0; i < 15; i++) {
                let x = Math.random() * 320;
                let y = Math.random() * 180;
                ctx.fillRect(x, y, 2, 2);
            }
            
            requestAnimationFrame(drawGrid);
        }
        drawGrid();
    }

    cameraPowerBtn.addEventListener("click", toggleWebcam);
    cameraPowerHeader.addEventListener("click", toggleWebcam);
});
