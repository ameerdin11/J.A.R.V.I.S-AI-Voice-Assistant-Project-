"""
config.py

Loads and stores configuration settings from the .env file and reads the system prompt.
Provides robust fallback values in case environment variables or files are missing.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Workspace Root
ROOT_DIR = Path(__file__).resolve().parent

# OpenAI API Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Brain Settings
LLM_MODE = os.getenv("LLM_MODE", "openai").lower()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# TTS Settings
TTS_MODE = os.getenv("TTS_MODE", "online").lower()
OFFLINE_TTS_BACKEND = os.getenv("OFFLINE_TTS_BACKEND", "pyttsx3").lower()
COQUI_MODEL_NAME = os.getenv("COQUI_MODEL_NAME", "tts_models/en/ljspeech/vits")

# Whisper ASR Settings
ASR_MODEL_NAME = os.getenv("ASR_MODEL_NAME", "tiny")

# Audio Recording Settings
try:
    MIC_INDEX = int(os.getenv("MIC_INDEX")) if os.getenv("MIC_INDEX") else None
except ValueError:
    MIC_INDEX = None

try:
    MIC_ENERGY_THRESHOLD = int(os.getenv("MIC_ENERGY_THRESHOLD", "1500"))
except ValueError:
    MIC_ENERGY_THRESHOLD = 1500

WAKE_WORD = os.getenv("WAKE_WORD", "hey jarvis").lower()

# Simulation Mode Settings
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "True").lower() == "true"

# Load the system prompt from file
SYSTEM_PROMPT = ""
prompt_path = ROOT_DIR / "system_prompt.txt"
try:
    if prompt_path.exists():
        with open(prompt_path, "r", encoding="utf-8") as f:
            SYSTEM_PROMPT = f.read().strip()
    else:
        # Robust fallback prompt if the file does not exist
        SYSTEM_PROMPT = (
            "You are Jarvis, a highly intelligent and loyal AI assistant created by Ameer.\n"
            "- Always call the user \"Ameer\"\n"
            "- Speak in clear, professional, and friendly English only — do not use Hinglish, Hindi, or Urdu.\n"
            "- You have two modes: conversation mode and command mode\n"
            "- In conversation mode: reply like a witty, caring friend in 1-3 sentences\n"
            "- In command mode: give a short confirmation only (\"I have turned on the fan, Ameer!\")\n"
            "- Never say you are ChatGPT, Claude, or any other AI — you are always Jarvis\n"
            "- Remember previous messages in the conversation and refer back naturally\n"
            "- Show empathy if Ameer seems stressed, tired, or sad\n"
            "- Keep responses short and natural unless detail is explicitly asked for"
        )
except Exception as e:
    print(f"[Warning] Error reading system prompt file: {e}. Using default prompt.")
    SYSTEM_PROMPT = (
        "You are Jarvis, a highly intelligent and loyal AI assistant created by Ameer.\n"
        "- Always call the user \"Ameer\"\n"
        "- Speak in clear, professional, and friendly English only — do not use Hinglish, Hindi, or Urdu.\n"
        "- You have two modes: conversation mode and command mode\n"
        "- In conversation mode: reply like a witty, caring friend in 1-3 sentences\n"
        "- In command mode: give a short confirmation only (\"I have turned on the fan, Ameer!\")\n"
        "- Never say you are ChatGPT, Claude, or any other AI — you are always Jarvis\n"
        "- Remember previous messages in the conversation and refer back naturally\n"
        "- Show empathy if Ameer seems stressed, tired, or sad\n"
        "- Keep responses short and natural unless detail is explicitly asked for"
    )

if __name__ == "__main__":
    # Test configuration load
    print("=== Jarvis Configuration ===")
    print(f"LLM Mode: {LLM_MODE}")
    print(f"Ollama Host: {OLLAMA_HOST}")
    print(f"Ollama Model: {OLLAMA_MODEL}")
    print(f"TTS Mode: {TTS_MODE}")
    print(f"Offline TTS Backend: {OFFLINE_TTS_BACKEND}")
    print(f"ASR Model: {ASR_MODEL_NAME}")
    print(f"Mic Index: {MIC_INDEX}")
    print(f"Energy Threshold: {MIC_ENERGY_THRESHOLD}")
    print(f"Wake Word: '{WAKE_WORD}'")
    print(f"Simulation Mode: {SIMULATION_MODE}")
    print(f"OpenAI Key Configured: {bool(OPENAI_API_KEY)}")
    print(f"System Prompt Length: {len(SYSTEM_PROMPT)} chars")
