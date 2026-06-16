"""
preprocessor.py

Applies preprocessing to recorded WAV files before passing them to Whisper.
Performs:
1. Audio loading (using librosa).
2. Noise reduction (using noisereduce).
3. Volume normalization (peak amplitude scaling).
4. Voice Activity Detection (VAD) (using webrtcvad or amplitude-based fallback).
5. Saving the preprocessed/cleaned audio.
All steps are wrapped in try/except blocks with robust fallbacks to ensure Jarvis never crashes.
"""

import os
import sys
import wave
import numpy as np
import soundfile as sf

# Try importing librosa
librosa_available = False
try:
    import librosa
    librosa_available = True
except ImportError:
    print("[Preprocessor Warning] 'librosa' is not installed. Will use soundfile directly.")

# Try importing noisereduce
noisereduce_available = False
try:
    import noisereduce as nr
    noisereduce_available = True
except ImportError:
    print("[Preprocessor Warning] 'noisereduce' is not installed. Background noise reduction will be skipped.")

# Try importing webrtcvad
webrtcvad_available = False
try:
    import webrtcvad
    webrtcvad_available = True
except ImportError:
    print("[Preprocessor Warning] 'webrtcvad' is not installed. Using simple energy-based VAD fallback.")

def load_audio(file_path, target_sr=16000):
    """
    Loads an audio file and returns the signal and sample rate.
    Uses librosa if available, otherwise falls back to soundfile.
    """
    if librosa_available:
        try:
            y, sr = librosa.load(file_path, sr=target_sr)
            return y, sr
        except Exception as e:
            print(f"[Preprocessor Error] Librosa load failed: {e}. Trying soundfile...")
            
    # Fallback to soundfile
    try:
        y, sr = sf.read(file_path)
        # Convert to mono if stereo
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)
        # Resample if needed
        if sr != target_sr and librosa_available:
            y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
        return y, sr
    except Exception as e:
        print(f"[Preprocessor Error] Soundfile load failed: {e}")
        raise e

def apply_noise_reduction(y, sr):
    """
    Reduces background noise in the audio signal.
    """
    if not noisereduce_available:
        return y
        
    try:
        # We assume the first 0.3s contains background noise
        prop_noise_limit = min(0.3, len(y) / sr)
        if prop_noise_limit > 0.05:
            # Run noise reduction
            y_reduced = nr.reduce_noise(y=y, sr=sr, prop_decrease=0.8)
            return y_reduced
    except Exception as e:
        print(f"[Preprocessor Warning] Noise reduction failed: {e}. Returning original audio.")
    return y

def normalize_volume(y):
    """
    Normalizes the peak amplitude of the audio to prevent quiet speech.
    """
    try:
        max_val = np.max(np.abs(y))
        if max_val > 0.001:
            return y / max_val
    except Exception as e:
        print(f"[Preprocessor Warning] Normalization failed: {e}")
    return y

def apply_vad(y, sr, frame_duration_ms=30):
    """
    Uses webrtcvad to filter out non-speech segments.
    Falls back to a simple energy-based gate if webrtcvad is not available.
    """
    # 1. Webrtcvad approach
    if webrtcvad_available:
        try:
            # Initialize VAD with aggressiveness mode 2 (moderate) or 3 (aggressive)
            vad = webrtcvad.Vad(2)
            
            # Convert float32 array (-1.0 to 1.0) to 16-bit PCM bytes
            # Clip values to protect against scaling issues
            y_clipped = np.clip(y, -1.0, 1.0)
            pcm_data = (y_clipped * 32767).astype(np.int16).tobytes()
            
            # Calculate frame size
            # 16000Hz * 0.030s = 480 samples. 480 samples * 2 bytes = 960 bytes
            frame_len = int(sr * (frame_duration_ms / 1000.0))
            frame_bytes_len = frame_len * 2
            
            cleaned_y_parts = []
            
            # Slide through PCM data
            for i in range(0, len(pcm_data), frame_bytes_len):
                frame = pcm_data[i:i+frame_bytes_len]
                # Pad last frame if it's too short
                if len(frame) < frame_bytes_len:
                    frame = frame + b'\x00' * (frame_bytes_len - len(frame))
                
                # Check if speech
                is_speech = vad.is_speech(frame, sr)
                if is_speech:
                    # Convert back to float and append
                    frame_np = np.frombuffer(frame, dtype=np.int16).astype(np.float32) / 32767.0
                    cleaned_y_parts.append(frame_np)
            
            if len(cleaned_y_parts) > 0:
                y_speech = np.concatenate(cleaned_y_parts)
                # Ensure we have at least 0.5s of speech, otherwise return original normalized
                if len(y_speech) > (sr * 0.5):
                    return y_speech
        except Exception as e:
            print(f"[Preprocessor Warning] webrtcvad processing failed: {e}. Falling back to energy VAD.")

    # 2. Energy-based fallback VAD
    try:
        # Simple short-time energy thresholding
        frame_len = int(sr * 0.05)  # 50ms frames
        threshold = 0.02  # Amplitude threshold
        cleaned_y_parts = []
        
        for i in range(0, len(y), frame_len):
            frame = y[i:i+frame_len]
            if len(frame) == 0:
                continue
            rms = np.sqrt(np.mean(frame**2))
            if rms > threshold:
                cleaned_y_parts.append(frame)
                
        if len(cleaned_y_parts) > 0:
            y_speech = np.concatenate(cleaned_y_parts)
            return y_speech
    except Exception as e:
        print(f"[Preprocessor Warning] Fallback VAD failed: {e}")
        
    return y

def preprocess_audio(input_file_path, output_file_path):
    """
    Executes the full preprocessing pipeline on the input audio file
    and writes the resulting clean audio to the output file.
    """
    try:
        # 1. Load Audio
        y, sr = load_audio(input_file_path, target_sr=16000)
        
        # 2. Noise Reduction
        y_denoised = apply_noise_reduction(y, sr)
        
        # 3. VAD Speech Segmentation
        y_speech = apply_vad(y_denoised, sr)
        
        # 4. Volume Normalization
        y_final = normalize_volume(y_speech)
        
        # Save output file
        os.makedirs(os.path.dirname(output_file_path) or '.', exist_ok=True)
        sf.write(output_file_path, y_final, sr, format='WAV', subtype='PCM_16')
        
        # Verify saved file
        if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 0:
            return True
        return False
        
    except Exception as e:
        print(f"[Preprocessor Error] Pipeline failed for {input_file_path}: {e}")
        # If everything fails, attempt to copy the original file to output file path as fallback
        try:
            import shutil
            shutil.copy2(input_file_path, output_file_path)
            print("[Preprocessor] Fallback: Copied original file directly due to preprocessing pipeline failure.")
            return True
        except Exception as copy_e:
            print(f"[Preprocessor Critical Error] Fallback copy also failed: {copy_e}")
            return False

if __name__ == "__main__":
    # Test preprocessor with a dummy WAV file
    print("Testing Preprocessor...")
    dummy_in = "temp_dummy_in.wav"
    dummy_out = "temp_dummy_out.wav"
    
    # Write a dummy sine wave file with some silent sections
    sr = 16000
    t = np.linspace(0, 2, int(sr * 2))
    # 1 second of sine wave followed by 1 second of silence
    y_test = np.sin(2 * np.pi * 440 * t)
    y_test[int(sr):] = 0.001 * np.random.randn(int(sr))  # noise
    
    sf.write(dummy_in, y_test, sr)
    print(f"Created test WAV file: {dummy_in}")
    
    success = preprocess_audio(dummy_in, dummy_out)
    print(f"Preprocessing run success status: {success}")
    if success and os.path.exists(dummy_out):
        print(f"Output WAV size: {os.path.getsize(dummy_out)} bytes")
        
    # Cleanup
    for f in [dummy_in, dummy_out]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass
