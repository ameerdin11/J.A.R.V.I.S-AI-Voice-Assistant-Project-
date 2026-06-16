# Jarvis — AI Voice Assistant (Conversational + Command Control)

Jarvis is a fully functional, highly intelligent AI-powered voice assistant tailored for **Ameer**. It supports real-time microphone capture, wake-word activation ("Hey Jarvis"), noise reduction/VAD preprocessing, local Whisper ASR, router intent parsing, PC & smart home command mapping, and natural Hinglish voice output.

It can be run in **Online Mode** (OpenAI GPT-4 + Google TTS) or **Offline Mode** (Ollama Llama3 + pyttsx3/Coqui local TTS).

---

## Folder Structure

```text
jarvis/
├── main.py                  # Entry point — orchestrates the voice loop lifecycle
├── audio_capture.py         # Mic recording, energy start detection, keyboard fallback
├── preprocessor.py          # Denoising, VAD, and volume normalization
├── asr_model.py             # Whisper speech-to-text model loader and transcription
├── router.py                # Classifies input: command mode vs conversation mode
├── nlu_engine.py            # Extracts intents and entities from command text
├── llm_brain.py             # OpenAI GPT-4 / Ollama Hinglish chat client
├── command_mapper.py        # Maps parsed NLU entities to executor functions
├── action_executor.py       # Executes PC commands, apps, or smart home GPIO pins
├── tts_response.py          # Voice output engine (gTTS, pyttsx3, or Coqui TTS)
├── memory.py                # Stores session-based conversation history (max 20 turns)
├── config.py                # Handles settings, system prompt, and .env loading
├── system_prompt.txt        # Jarvis Hinglish personality rules
├── requirements.txt         # Project dependencies list
└── README.md                # This setup and instruction guide
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or 3.11 (Python 3.12+ is supported, but PyAudio/noisereduce installation is easiest on 3.10/3.11).
- Visual C++ Build Tools (required by PyAudio and webrtcvad compilation on Windows).

### 1. Clone the project or navigate to the workspace
Open your terminal inside the workspace:
```bash
cd "d:/project/Jarvis — AI Voice Assistant"
```

### 2. Install dependencies
Install all required libraries using pip:
```bash
pip install -r requirements.txt
```

> [!NOTE]
> If `pyaudio` fails to install due to compiler errors on Windows, download a precompiled PyAudio wheel matching your Python version from [Christoph Gohlke's archive](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) or install it via pipwin:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```
> If PyAudio is still not available, Jarvis will automatically fall back to **Keyboard Text-Input Mode**, enabling you to test the entire system via console typing.

### 3. Configure the environment variables
Copy the `.env.example` file to `.env`:
```bash
copy .env.example .env
```
Open `.env` and configure your settings:
- Add your `OPENAI_API_KEY` (if using OpenAI brain).
- Adjust the audio `MIC_ENERGY_THRESHOLD` (increase if Jarvis triggers too easily on background noise).
- Set `SIMULATION_MODE=True` if you are running on a standard PC without Raspberry Pi GPIO pins connected.

---

## Configuration Modes

### Option A: Online Mode (Recommended for best quality)
- In `.env`, set:
  ```env
  LLM_MODE=openai
  TTS_MODE=online
  OPENAI_API_KEY=sk-...
  ```
- Make sure you have active internet connection.

### Option B: Offline Mode (No internet needed)
1. **ASR:** Local Whisper (`tiny`) runs locally. It will automatically download the small model weight file to your cache directory on the first execution.
2. **Local LLM (Ollama):**
   - Download and install [Ollama](https://ollama.com).
   - In terminal, pull the Llama3 model:
     ```bash
     ollama pull llama3
     ```
   - Make sure Ollama service is running.
3. **Local TTS (pyttsx3):**
   - In `.env`, set:
     ```env
     LLM_MODE=ollama
     TTS_MODE=offline
     OFFLINE_TTS_BACKEND=pyttsx3
     ```
   - Pyttsx3 loads instantly and uses the system's native text-to-speech voice (Windows SAPI5).
4. **Local TTS (Coqui - Optional Premium Voice):**
   - If you prefer high-quality deep learning voices offline, install Coqui TTS and configure:
     ```env
     OFFLINE_TTS_BACKEND=coqui
     COQUI_MODEL_NAME=tts_models/en/ljspeech/vits
     ```

---

## Running the Assistant

Execute the entry point module:
```bash
python main.py
```

### Interaction Flows

1. **Single-Breath Command/Chitchat:**
   - Speak your wake word and query together: *"Hey Jarvis, how are you today?"* or *"Hey Jarvis, fan on karo"*.
   - Jarvis will detect the trigger, strip "Hey Jarvis", and immediately process your request.

2. **Multi-Step Dialog:**
   - Say *"Hey Jarvis"* and stop speaking.
   - Jarvis will respond with: *"Ji Ameer, boliye?"* (Yes Ameer, tell me?).
   - A secondary listening window will open. Speak your command: *"Open Chrome"* or *"AC temperature 22 degrees kar do"*.

3. **Text Input Fallback:**
   - If no microphone backend is available or configured, Jarvis starts in a console prompt mode. You can type commands directly (e.g., typing `open chrome` or `Hey Jarvis, fan on karo`) to check the responses and triggers.

---

## Personality Rules (Injects in every LLM call)
- Always addresses the user as **Ameer**.
- Speaks in casual, friendly **Hinglish** (English + Urdu/Hindi mix).
- Limits replies to 1-3 sentences in conversation mode.
- Confirms execution directly and briefly in command mode.
- Empathizes when Ameer reports feeling tired, sad, or stressed.
