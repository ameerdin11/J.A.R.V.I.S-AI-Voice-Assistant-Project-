"""
audio_capture.py

Handles recording audio from the microphone using PyAudio (with sounddevice fallback).
Monitors mic energy levels to detect when the user starts speaking and stops recording
after a period of silence.
Provides a terminal keyboard input fallback if audio libraries are unavailable.
"""

import os
import wave
import time
import math
import sys
import numpy as np
from pathlib import Path
import config

# Try importing pyaudio, then sounddevice
pyaudio_available = False
sounddevice_available = False

try:
    import pyaudio
    pyaudio_available = True
except ImportError:
    try:
        import sounddevice as sd
        sounddevice_available = True
    except ImportError:
        pass

# Constants for recording
FORMAT = 8  # Equivalent to pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Whisper and VAD prefer 16000 Hz
CHUNK_SIZE = 1024

class AudioRecorder:
    def __init__(self):
        global pyaudio_available, sounddevice_available
        self.p = None
        self.stream = None
        self.enabled = False
        
        if pyaudio_available:
            try:
                self.p = pyaudio.PyAudio()
                self.enabled = True
                print("[Audio] Initialized PyAudio successfully.")
            except Exception as e:
                print(f"[Audio Warning] Failed to initialize PyAudio: {e}. Trying sounddevice...")
                pyaudio_available = False
                
        if not pyaudio_available and sounddevice_available:
            try:
                self.enabled = True
                print("[Audio] Using sounddevice fallback.")
            except Exception as e:
                print(f"[Audio Warning] Failed to initialize sounddevice: {e}.")
                sounddevice_available = False
                
        if not self.enabled:
            print("[Audio Warning] No microphone backend available. Jarvis will run in TEXT INPUT mode.")

    def calculate_rms(self, audio_bytes):
        """
        Calculates the Root Mean Square (RMS) of the audio chunk to determine volume/energy.
        """
        try:
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            if len(audio_data) == 0:
                return 0
            # Cast to float64 to prevent overflow during squaring
            rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
            return rms
        except Exception as e:
            # Fallback in case of numpy error
            return 0

    def record_until_silence(self, output_path, energy_threshold=None, silence_duration=1.5, max_duration=10.0):
        """
        Listens to the mic. Starts recording when energy exceeds threshold,
        and saves when silence is detected for `silence_duration` seconds.
        """
        if not self.enabled:
            # Fallback: prompt user for keyboard input in the terminal
            print("\n[Jarvis Keyboard Input Mode]")
            text = input("Ameer: ")
            # Save a dummy WAV file (since Whisper or main loop expects one) and return text
            self._write_dummy_wav(output_path)
            return text

        if energy_threshold is None:
            energy_threshold = config.MIC_ENERGY_THRESHOLD

        print(f"[Audio] Listening... (Threshold: {energy_threshold})")
        
        # Audio frames buffer
        frames = []
        
        if pyaudio_available:
            try:
                # Open audio stream
                self.stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=config.MIC_INDEX,
                    frames_per_buffer=CHUNK_SIZE
                )
            except Exception as e:
                print(f"[Audio Error] Failed to open PyAudio stream: {e}. Falling back to keyboard input.")
                self.enabled = False
                return self.record_until_silence(output_path, energy_threshold, silence_duration, max_duration)
        
        # Listening loop variables
        speaking = False
        silence_start_time = None
        start_time = time.time()
        
        # We also want to record a tiny bit of pre-trigger buffer
        pre_trigger_buffer = []
        pre_trigger_len = 5  # keep last 5 chunks
        
        try:
            while True:
                # Read chunk from mic
                if pyaudio_available:
                    try:
                        data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    except Exception as stream_e:
                        print(f"[Audio Stream Warning] Read error: {stream_e}")
                        continue
                elif sounddevice_available:
                    try:
                        # Record short duration with sounddevice
                        duration_sec = CHUNK_SIZE / RATE
                        recording = sd.rec(int(CHUNK_SIZE), samplerate=RATE, channels=CHANNELS, dtype='int16')
                        sd.wait()
                        data = recording.tobytes()
                    except Exception as sd_e:
                        print(f"[Audio SD Error] sounddevice read failed: {sd_e}")
                        self.enabled = False
                        return self.record_until_silence(output_path, energy_threshold, silence_duration, max_duration)

                # Calculate energy
                rms = self.calculate_rms(data)
                
                if not speaking:
                    # Keep a small buffer before speech begins
                    pre_trigger_buffer.append(data)
                    if len(pre_trigger_buffer) > pre_trigger_len:
                        pre_trigger_buffer.pop(0)
                        
                    if rms > energy_threshold:
                        speaking = True
                        print("[Audio] Speech detected! Recording...")
                        frames.extend(pre_trigger_buffer)
                        frames.append(data)
                        start_time = time.time()
                else:
                    frames.append(data)
                    
                    # Check for silence
                    if rms < energy_threshold:
                        if silence_start_time is None:
                            silence_start_time = time.time()
                        elif time.time() - silence_start_time > silence_duration:
                            print("[Audio] Silence detected. Stopping recording.")
                            break
                    else:
                        silence_start_time = None
                        
                    # Max duration limit
                    if time.time() - start_time > max_duration:
                        print("[Audio] Maximum recording duration reached.")
                        break
                        
                # If we've been listening for 30s with absolutely nothing, just sleep a bit to save CPU
                if not speaking and time.time() - start_time > 30.0:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("[Audio] Recording interrupted by user.")
        finally:
            if pyaudio_available and self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None
                
        # Save recording to WAV
        if len(frames) > 0:
            try:
                os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                with wave.open(output_path, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    if pyaudio_available:
                        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                    else:
                        wf.setsampwidth(2)  # 16-bit is 2 bytes
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))
                print(f"[Audio] Audio saved to {output_path}")
            except Exception as e:
                print(f"[Audio Error] Failed to save WAV file: {e}")
        else:
            print("[Audio Warning] No audio was recorded.")
            
        return None

    def _write_dummy_wav(self, output_path):
        """
        Writes a tiny silent WAV file for compatibility with other modules in text-input fallback mode.
        """
        try:
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(RATE)
                # 0.1 seconds of silence
                wf.writeframes(b'\x00' * int(RATE * 2 * 0.1))
        except Exception as e:
            print(f"[Audio Error] Failed to write dummy WAV: {e}")

    def close(self):
        if pyaudio_available and self.p:
            try:
                self.p.terminate()
            except Exception:
                pass

if __name__ == "__main__":
    print("Testing AudioRecorder module. Speak into microphone...")
    recorder = AudioRecorder()
    temp_wav = "temp_test.wav"
    result = recorder.record_until_silence(temp_wav, silence_duration=1.5)
    
    if result is not None:
        print(f"Fallback Mode Input captured: '{result}'")
    else:
        print(f"Recorded file exists: {os.path.exists(temp_wav)}")
        if os.path.exists(temp_wav):
            size = os.path.getsize(temp_wav)
            print(f"WAV File size: {size} bytes")
            # Cleanup
            try:
                os.remove(temp_wav)
            except OSError:
                pass
    recorder.close()
