"""
tts_response.py

Converts Jarvis text replies into spoken audio responses.
Supports:
1. Online Mode: gTTS (Google Text-to-Speech) saved to MP3 and played via pygame.
2. Offline Mode: pyttsx3 (Native system speech, fast, zero dependency setup).
3. Offline Mode (Advanced): Coqui TTS (High quality local deep learning TTS).
Ensures safe audio playback and release of file locks.
"""

import os
import sys
import time
import tempfile
import config

# Try importing gTTS and pygame
gtts_available = False
pygame_available = False

try:
    from gtts import gTTS
    gtts_available = True
except ImportError:
    print("[TTS Warning] 'gtts' library not found. Online TTS will be unavailable.")

try:
    import pygame
    pygame_available = True
except ImportError:
    print("[TTS Warning] 'pygame' library not found. Audio playback for online TTS will fall back to system commands.")

# Try importing pyttsx3
pyttsx_available = False
pyttsx_engine = None
try:
    import pyttsx3
    pyttsx_available = True
except ImportError:
    print("[TTS Warning] 'pyttsx3' library not found. Native offline TTS will be unavailable.")

# Try importing Coqui TTS
coqui_available = False
coqui_tts_instance = None
try:
    from TTS.api import TTS
    coqui_available = True
except ImportError:
    # Do not print warning here unless requested, as Coqui is heavy
    pass


def play_audio_file(file_path):
    """
    Plays an MP3 or WAV file using pygame mixer, falling back to system calls if needed.
    """
    if not os.path.exists(file_path):
        print(f"[TTS Play Error] Audio file not found: {file_path}", file=sys.stderr)
        return

    played = False
    
    # Try Pygame
    if pygame_available:
        try:
            # Initialize mixer if not already initialized
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            pygame.mixer.music.unload()  # Critical: Release lock on the file
            played = True
        except Exception as e:
            print(f"[TTS Play Warning] Pygame playback failed: {e}. Trying system fallback.")
            try:
                pygame.mixer.quit()
            except Exception:
                pass

    # Platform specific fallbacks
    if not played:
        try:
            if sys.platform == "win32":
                # Windows built-in command to play audio (powershell soundplayer handles WAV, start command handles MP3)
                if file_path.endswith(".wav"):
                    cmd = f'powershell -c "(New-Object Media.SoundPlayer \'{os.path.abspath(file_path)}\').PlaySync()"'
                    os.system(cmd)
                else:
                    # Launch default player minimized and close it after some time
                    os.system(f'start /min "" "{os.path.abspath(file_path)}"')
                    # Wait approximate duration
                    time.sleep(3.0)
            elif sys.platform == "darwin":
                # macOS play command
                os.system(f'afplay "{file_path}"')
            else:
                # Linux play command
                os.system(f'aplay "{file_path}"')
            played = True
        except Exception as sys_e:
            print(f"[TTS Play Error] System fallback playback failed: {sys_e}", file=sys.stderr)


def speak_offline_pyttsx3(text):
    """
    Uses native SAPI5/AVSpeechSynthesizer via pyttsx3 to speak offline.
    """
    global pyttsx_engine
    try:
        if pyttsx_engine is None:
            pyttsx_engine = pyttsx3.init()
            # Set properties (optional: customize speed/volume)
            pyttsx_engine.setProperty('rate', 160)  # Speed percent (default is ~200)
            pyttsx_engine.setProperty('volume', 1.0) # Volume 0-1
            
            # Check available voices
            voices = pyttsx_engine.getProperty('voices')
            if voices:
                # Try to find a Hinglish or English voice
                # SAPI5 English/Hinglish voices are usually index 0/1
                pyttsx_engine.setProperty('voice', voices[0].id)
                
        print(f"[TTS Offline (pyttsx3)] Speaking: '{text}'")
        pyttsx_engine.say(text)
        pyttsx_engine.runAndWait()
        return True
    except Exception as e:
        print(f"[TTS Error] pyttsx3 speaking failed: {e}", file=sys.stderr)
        return False


def speak_offline_coqui(text):
    """
    Uses Coqui TTS model to generate audio and plays it.
    """
    global coqui_tts_instance
    if not coqui_available:
        print("[TTS Error] Coqui TTS package not installed. Cannot use Coqui backend.", file=sys.stderr)
        return False

    temp_wav = os.path.join(tempfile.gettempdir(), "jarvis_reply_coqui.wav")
    
    try:
        if coqui_tts_instance is None:
            print(f"[TTS Coqui] Loading model '{config.COQUI_MODEL_NAME}'...")
            coqui_tts_instance = TTS(model_name=config.COQUI_MODEL_NAME, gpu=False)
            print("[TTS Coqui] Model loaded successfully.")
            
        print(f"[TTS Offline (Coqui)] Generating audio for: '{text}'")
        coqui_tts_instance.tts_to_file(text=text, file_path=temp_wav)
        print("[TTS Offline (Coqui)] Audio generated. Playing...")
        play_audio_file(temp_wav)
        
        # Cleanup
        try:
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
        except OSError:
            pass
        return True
    except Exception as e:
        print(f"[TTS Error] Coqui TTS failed: {e}", file=sys.stderr)
        return False


def speak_online_gtts(text):
    """
    Uses Google Translate Text-to-Speech (gTTS) online API.
    Generates an MP3 file and plays it.
    """
    if not gtts_available:
        print("[TTS Error] gTTS package is unavailable. Cannot speak online.", file=sys.stderr)
        return False
        
    temp_mp3 = os.path.join(tempfile.gettempdir(), f"jarvis_reply_{int(time.time())}.mp3")
    
    try:
        print(f"[TTS Online (gTTS)] Generating audio for: '{text}'")
        # gTTS parameters (lang='en' or 'hi' for Hinglish, 'en' works well for mixed english/hindi)
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(temp_mp3)
        
        print("[TTS Online (gTTS)] Playing response...")
        play_audio_file(temp_mp3)
        
        # Try to delete the temp file
        try:
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)
        except OSError:
            # Sometime Windows holds the lock for a fraction of a second, retry in a bit
            time.sleep(0.5)
            try:
                if os.path.exists(temp_mp3):
                    os.remove(temp_mp3)
            except OSError:
                pass
        return True
    except Exception as e:
        print(f"[TTS Error] gTTS failed: {e}", file=sys.stderr)
        return False


def speak(text: str):
    """
    Entry point to speak response text back to the user.
    Chooses the appropriate backend based on system config and availability.
    """
    if not text:
        return

    print(f"\nJarvis: {text}\n")

    # 1. Online Mode (gTTS)
    if config.TTS_MODE == "online":
        success = speak_online_gtts(text)
        if success:
            return
        print("[TTS Warning] Online TTS failed. Falling back to offline TTS...")

    # 2. Offline Mode (pyttsx3 or Coqui)
    if config.OFFLINE_TTS_BACKEND == "coqui" and coqui_available:
        success = speak_offline_coqui(text)
        if success:
            return
        print("[TTS Warning] Coqui offline TTS failed. Falling back to native pyttsx3...")

    # Fallback to pyttsx3 (or primary offline)
    if pyttsx_available:
        success = speak_offline_pyttsx3(text)
        if success:
            return

    # Print if all audio backends fail
    print(f"[TTS Error] No working audio TTS backend found to say: '{text}'")


if __name__ == "__main__":
    # Test speaking online and offline
    print("Testing TTS Response...")
    speak("Hello Ameer, how are you? Main bilkul theek hoon!")
