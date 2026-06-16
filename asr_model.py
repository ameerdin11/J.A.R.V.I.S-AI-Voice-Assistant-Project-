"""
asr_model.py

Loads the OpenAI Whisper model once at startup (tiny, base, etc., based on config).
Provides the WhisperASR class with a transcribe() method to convert WAV files to text.
Includes robust error handling for CUDA/memory limits and missing library fallbacks.
"""

import os
import sys
import config

# Try to import whisper
whisper_available = False
try:
    import whisper
    whisper_available = True
except ImportError:
    print("[ASR Warning] 'whisper' library not found. Run 'pip install openai-whisper' to transcribe voice inputs.")

class WhisperASR:
    def __init__(self):
        self.model = None
        if whisper_available:
            model_name = config.ASR_MODEL_NAME
            print(f"[ASR] Loading Whisper model '{model_name}' (this may take a few seconds)...")
            try:
                # Load Whisper model (cpu/gpu auto-detected by whisper library)
                self.model = whisper.load_model(model_name)
                print(f"[ASR] Whisper model '{model_name}' loaded successfully.")
            except Exception as e:
                print(f"[ASR Error] Failed to load Whisper model '{model_name}': {e}.")
                print("[ASR Info] Running in simulation/fallback mode for speech recognition.")
        else:
            print("[ASR Info] Whisper is unavailable. Audio files will not be transcribed automatically.")

    def transcribe(self, audio_path):
        """
        Transcribes the given WAV file to text using Whisper.
        Returns the transcribed text string or empty string on failure.
        """
        if not os.path.exists(audio_path):
            print(f"[ASR Error] Audio file not found: {audio_path}")
            return ""

        # Check if the file is empty/near-empty
        try:
            if os.path.getsize(audio_path) < 1000:
                print("[ASR Warning] Audio file is too small/empty. Skipping transcription.")
                return ""
        except Exception:
            pass

        if not self.model:
            print("[ASR Warning] Whisper model is not loaded. Cannot transcribe audio.")
            # Prompt terminal input as fallback in case ASR fails but microphone recorded
            print("\n[ASR Fallback: Please type what you said]")
            fallback_text = input("Ameer (type input): ")
            return fallback_text

        try:
            print(f"[ASR] Transcribing {audio_path}...")
            # Run transcription
            # fp16=False enforces float32 execution (recommended for CPUs and avoids warning logs)
            result = self.model.transcribe(audio_path, fp16=False)
            transcription = result.get("text", "").strip()
            print(f"[ASR] Transcribed text: '{transcription}'")
            return transcription
        except Exception as e:
            print(f"[ASR Error] Transcription failed: {e}")
            # Terminal input fallback
            print("\n[ASR Fallback: Please type what you said]")
            fallback_text = input("Ameer (type input): ")
            return fallback_text

if __name__ == "__main__":
    # Test Whisper load and transcription
    print("Testing ASR Model...")
    asr = WhisperASR()
    
    # Test transcribing a dummy WAV if it exists
    dummy_wav = "dummy_test_speech.wav"
    if os.path.exists(dummy_wav):
        text = asr.transcribe(dummy_wav)
        print(f"Result: {text}")
    else:
        print("No dummy speech file found. ASR load test complete.")
