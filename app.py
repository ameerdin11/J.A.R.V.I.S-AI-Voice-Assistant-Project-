"""
app.py

Flask-based web server for the Jarvis AI Voice Assistant.
Serves a responsive glassmorphic dashboard UI at http://localhost:5000.
Exposes JSON API endpoints for:
- System performance metrics (CPU, RAM, Disk, Uptime)
- Dialogue chat execution (routing to LLM or NLU action executor)
- Backend microphone recording trigger
- Simulated webcam toggle and weather data
"""

import os
import sys
import time
import threading
from datetime import datetime
import psutil
from flask import Flask, jsonify, request, render_template

import config
import memory
import audio_capture
import preprocessor
import asr_model
import router
import nlu_engine
import command_mapper
import tts_response

# Initialize Flask App
# We configure it to serve static and template files from the current folder structure
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)

# Global states
start_time = datetime.now()
commands_counter = 0
current_status = "Listening for wake word..."
camera_active = False
recorder_instance = None
asr_instance = None

# Thread lock for audio capture triggers to avoid concurrent mic access
audio_lock = threading.Lock()

def get_uptime_str():
    """
    Calculates and returns the server running duration in HH:MM:SS format.
    """
    delta = datetime.now() - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@app.route('/')
def index():
    """
    Serves the main cybernetic J.A.R.V.I.S dashboard.
    """
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"[Web Error] Failed to render index.html: {e}", file=sys.stderr)
        # Dynamic basic template fallback in case folder doesn't exist
        return "<h3>Jarvis Dashboard Templates directory loading. Please wait.</h3>"

@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Returns system stats, status messages, and session uptime.
    """
    global current_status
    try:
        cpu_usage = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return jsonify({
            "status": "success",
            "assistant_status": current_status,
            "uptime": get_uptime_str(),
            "commands_executed": commands_counter,
            "camera_active": camera_active,
            "metrics": {
                "cpu_percent": cpu_usage,
                "ram_percent": ram.percent,
                "ram_used_gb": round(ram.used / (1024**3), 1),
                "ram_total_gb": round(ram.total / (1024**3), 1),
                "disk_used_gb": round(disk.used / (1024**3), 1),
                "disk_total_gb": round(disk.total / (1024**3), 1)
            }
        })
    except Exception as e:
        print(f"[Web Error] /api/status failed: {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """
    Returns simulated weather matching the mock design parameters (or custom data).
    """
    return jsonify({
        "status": "success",
        "temperature": "25.2",
        "location": "Quezon City, PH",
        "condition": "overcast clouds",
        "humidity": "94",
        "wind_speed": "5.8",
        "feels_like": "26.3"
    })

@app.route('/api/toggle_camera', methods=['POST'])
def toggle_camera():
    """
    Toggles the simulated camera active state.
    """
    global camera_active
    camera_active = not camera_active
    return jsonify({
        "status": "success",
        "camera_active": camera_active
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Executes a typed message through the router and intent execution pipeline.
    """
    global commands_counter, current_status
    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"status": "error", "message": "Empty message text"}), 400

    print(f"[Web Chat] Received input: '{message}'")
    current_status = "Processing command..."

    try:
        # Determine Mode
        mode = router.route_input(message)
        reply = ""

        if mode == "command":
            commands_counter += 1
            nlu_res = nlu_engine.parse_intent_and_entities(message)
            action_func, args = command_mapper.get_action_callable(nlu_res)
            
            if action_func:
                reply = action_func(*args)
            else:
                reply = "Ameer, ye command mere mapping database me nahi mili."
                
            # Log command to memory
            memory.add_message("user", message)
            memory.add_message("assistant", reply)
        else:
            # Conversation mode
            import llm_brain
            reply = llm_brain.generate_llm_response(message)

        # Reset state to listening shortly after processing
        def reset_state():
            time.sleep(3)
            global current_status
            current_status = "Listening for wake word..."
        threading.Thread(target=reset_state, daemon=True).start()

        return jsonify({
            "status": "success",
            "mode": mode,
            "reply": reply
        })

    except Exception as e:
        print(f"[Web Chat Error] Processing failed: {e}", file=sys.stderr)
        current_status = "Listening for wake word..."
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/trigger_voice', methods=['POST'])
def trigger_voice():
    """
    Triggers physical mic capture on the server.
    Fails gracefully if mic libraries are missing or in fallback mode.
    """
    global recorder_instance, asr_instance, commands_counter, current_status
    
    if not audio_lock.acquire(blocking=False):
        return jsonify({"status": "error", "message": "Microphone is already recording. Please wait."}), 409

    try:
        current_status = "Listening..."
        
        # Load models if not initialized
        if recorder_instance is None:
            recorder_instance = audio_capture.AudioRecorder()
        if asr_instance is None:
            asr_instance = asr_model.WhisperASR()

        # Audio file destinations
        raw_wav = "web_raw_speech.wav"
        clean_wav = "web_clean_speech.wav"

        # Cleanup past files
        for f in [raw_wav, clean_wav]:
            if os.path.exists(f):
                try: os.remove(f)
                except OSError: pass

        # Record audio
        # If in keyboard/disabled mode, this block defaults to prompt which can hang the web request,
        # so we check if recorder is enabled, if not we return early.
        if not recorder_instance.enabled:
            current_status = "Listening for wake word..."
            return jsonify({
                "status": "warning",
                "message": "Mic hardware is disabled or unavailable. Please type your query in the chat panel."
            })

        print("[Web Voice] Mic recording active...")
        # Record until silence (max 10s)
        recorder_instance.record_until_silence(raw_wav, silence_duration=1.2)

        if not os.path.exists(raw_wav):
            current_status = "Listening for wake word..."
            return jsonify({"status": "error", "message": "No audio was captured."}), 400

        # Preprocess
        current_status = "Processing..."
        preprocess_success = preprocessor.preprocess_audio(raw_wav, clean_wav)
        if not preprocess_success or not os.path.exists(clean_wav):
            current_status = "Listening for wake word..."
            return jsonify({"status": "error", "message": "Audio preprocessing failed."}), 500

        # Transcribe
        transcribed_text = asr_instance.transcribe(clean_wav)
        if not transcribed_text or len(transcribed_text.strip()) == 0:
            current_status = "Listening for wake word..."
            return jsonify({"status": "success", "user_text": "", "reply": "Ameer, mujhe aapki awaaz sunai nahi di."})

        # Process the transcribed text
        print(f"[Web Voice] Transcribed: '{transcribed_text}'")
        
        # Strip wake word if present (e.g. "hey jarvis open chrome" -> "open chrome")
        command_text = transcribed_text.lower().strip()
        wake_word = config.WAKE_WORD.lower()
        if wake_word in command_text:
            idx = command_text.find(wake_word)
            transcribed_text = transcribed_text[idx + len(wake_word):].strip().lstrip(",.?! ")

        # If user said only "hey jarvis"
        if not transcribed_text:
            reply = "Ji Ameer, boliye? Main sun raha hoon."
            return jsonify({
                "status": "success",
                "user_text": config.WAKE_WORD,
                "reply": reply
            })

        # Run pipeline
        mode = router.route_input(transcribed_text)
        reply = ""

        if mode == "command":
            commands_counter += 1
            nlu_res = nlu_engine.parse_intent_and_entities(transcribed_text)
            action_func, args = command_mapper.get_action_callable(nlu_res)
            if action_func:
                reply = action_func(*args)
            else:
                reply = "Ameer, ye command mere mapping database me nahi mili."
            memory.add_message("user", transcribed_text)
            memory.add_message("assistant", reply)
        else:
            import llm_brain
            reply = llm_brain.generate_llm_response(transcribed_text)

        # Reset state helper
        def reset_state():
            time.sleep(3)
            global current_status
            current_status = "Listening for wake word..."
        threading.Thread(target=reset_state, daemon=True).start()

        return jsonify({
            "status": "success",
            "user_text": transcribed_text,
            "reply": reply
        })

    except Exception as e:
        print(f"[Web Voice Error] Capture pipeline failed: {e}", file=sys.stderr)
        current_status = "Listening for wake word..."
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        audio_lock.release()
        # Clean temp voice wavs
        for f in ["web_raw_speech.wav", "web_clean_speech.wav"]:
            if os.path.exists(f):
                try: os.remove(f)
                except OSError: pass

if __name__ == "__main__":
    print("=========================================================")
    print("      J.A.R.V.I.S Dashboard Server Startup")
    print(f"      Access dashboard at: http://localhost:5000")
    print("=========================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)
