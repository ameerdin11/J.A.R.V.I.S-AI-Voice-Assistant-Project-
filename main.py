"""
main.py

The main entry point for the Jarvis AI Voice Assistant.
Orchestrates the lifecycle loop:
1. Loads configurations and initializes all engines (ASR, LLM, TTS, Memory).
2. Starts mic listening / energy threshold monitoring.
3. Detects wake word "Hey Jarvis" (supporting both single-breath commands and multi-step dialogs).
4. Cleans captured audio using the preprocessor module.
5. Transcribes using Whisper ASR.
6. Routes input to either Command Mode (NLU -> Mapper -> Executor) or Conversation Mode (LLM).
7. Saves the exchange in the memory module.
8. Speaks the output response back via TTS.
"""

import os
import sys
import time
import config
import memory
import audio_capture
import preprocessor
import asr_model
import router
import nlu_engine
import command_mapper
import tts_response

# Temp audio file paths
RAW_AUDIO_PATH = "temp_raw_speech.wav"
CLEAN_AUDIO_PATH = "temp_clean_speech.wav"

def print_banner():
    """
    Prints a stunning ASCII banner for Jarvis.
    """
    banner = """
========================================================================
      # # # # # # # # # # # # # # #
          #   #   # #   # #   # # #
          #   ##### ####  #   # # # ####
      #   #   #   # #  #   # #  # #    #
       ###    #   # #   #   #   # ####
    
             --- AI Voice Assistant for Ameer ---
========================================================================
    """
    print(banner)
    print(f"[*] Core Settings:")
    print(f"    - LLM Mode:   {config.LLM_MODE.upper()} " + (f"({config.OLLAMA_MODEL})" if config.LLM_MODE == "ollama" else ""))
    print(f"    - TTS Mode:   {config.TTS_MODE.upper()} " + (f"({config.OFFLINE_TTS_BACKEND})" if config.TTS_MODE == "offline" else ""))
    print(f"    - ASR Model:  Whisper '{config.ASR_MODEL_NAME}'")
    print(f"    - Wake Word:  '{config.WAKE_WORD}'")
    print(f"    - Simulation: {'ENABLED (PC Mode)' if config.SIMULATION_MODE else 'DISABLED (RPi hardware)'}")
    print(f"========================================================================\n")


def cleanup_temp_files():
    """
    Removes temporary audio files generated during execution.
    """
    for file_path in [RAW_AUDIO_PATH, CLEAN_AUDIO_PATH]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


def process_utterance(text: str, asr_engine):
    """
    Processes a fully resolved user utterance (text).
    Determines whether it is a command or conversation, executes it, and speaks the reply.
    """
    if not text or len(text.strip()) == 0:
        return

    # 1. Determine Mode (command vs conversation)
    mode = router.route_input(text)
    
    # 2. Execute based on mode
    if mode == "command":
        # NLU intent and entity extraction
        nlu_res = nlu_engine.parse_intent_and_entities(text)
        print(f"[NLU] Intent/Entity analysis: {nlu_res}")
        
        # Map to action function
        action_func, args = command_mapper.get_action_callable(nlu_res)
        
        if action_func:
            print(f"[Executor] Invoking action: {action_func.__name__} with args {args}")
            # Run action and get confirmation message
            reply = action_func(*args)
        else:
            # Fallback if command was routed but no executor matched
            reply = "Ameer, ye command mere database me nahi mili. Kya main LLM se poochon?"
            tts_response.speak(reply)
            
            # Ask the user if they want to ask the LLM instead
            # For simplicity in audio loop, we can just feed it to the LLM directly
            print("[Router Fallback] Routing unmatched command to LLM Brain.")
            reply = llm_brain.generate_llm_response(text)
            
        # Save command exchange to memory
        memory.add_message("user", text)
        memory.add_message("assistant", reply)
        
    else:
        # Conversation Mode: Call LLM Brain (handles memory updates inside)
        import llm_brain
        reply = llm_brain.generate_llm_response(text)
        
    # 3. Speak Response
    tts_response.speak(reply)


def run_voice_loop():
    """
    Runs the infinite microphone listening voice loop.
    """
    print_banner()
    
    # Initialise recorders and ASR models
    recorder = audio_capture.AudioRecorder()
    asr = asr_model.WhisperASR()
    
    # Greeting on startup
    startup_greeting = "Jarvis online hai, Ameer. Aap kaise hain?"
    tts_response.speak(startup_greeting)
    memory.add_message("assistant", startup_greeting)

    print("[*] Jarvis is active. Speak 'Hey Jarvis' to trigger.")
    
    try:
        while True:
            cleanup_temp_files()
            
            # Step 1: Record mic input
            # If recorder fails or defaults to text input, it returns the text typed.
            # Otherwise it returns None and saves RAW_AUDIO_PATH.
            typed_input = recorder.record_until_silence(RAW_AUDIO_PATH, silence_duration=1.5)
            
            text = ""
            if typed_input is not None:
                # Text Input Fallback Mode
                text = typed_input.strip()
                if not text:
                    continue
                # In keyboard mode, we skip the wake word requirement for a better typing experience!
                print(f"[Text Mode Input] Processing: '{text}'")
                process_utterance(text, asr)
                continue
                
            # Step 2: Clean audio with preprocessor
            if not os.path.exists(RAW_AUDIO_PATH):
                continue
                
            preprocess_success = preprocessor.preprocess_audio(RAW_AUDIO_PATH, CLEAN_AUDIO_PATH)
            if not preprocess_success or not os.path.exists(CLEAN_AUDIO_PATH):
                print("[Main Loop Error] Audio preprocessing failed.")
                continue
                
            # Step 3: Convert speech to text with Whisper ASR
            text = asr.transcribe(CLEAN_AUDIO_PATH)
            if not text or len(text.strip()) == 0:
                continue
            
            # Step 4: Wake Word Detection ("Hey Jarvis" check)
            # We check if the text contains the wake word
            wake_word = config.WAKE_WORD.lower()
            clean_text = text.lower()
            
            if wake_word in clean_text:
                print(f"[Wake Word] Detected '{config.WAKE_WORD}' in utterance: '{text}'")
                
                # Extract the command portion after the wake word
                wake_idx = clean_text.find(wake_word)
                command_part = text[wake_idx + len(wake_word):].strip()
                
                # Clean up leading punctuation from command part (e.g. ", open Chrome" -> "open Chrome")
                command_part = command_part.lstrip(",.?! ")
                
                if not command_part:
                    # Case A: User said ONLY "Hey Jarvis". Speak confirmation and wait for command.
                    acknowledgments = [
                        "Ji Ameer, boliye?", 
                        "Haan Ameer, main sun raha hoon. Kya kaam hai?",
                        "Ji Ameer, kya hukam hai?"
                    ]
                    # Select a random greeting or default
                    ack_reply = acknowledgments[0]
                    tts_response.speak(ack_reply)
                    
                    # Record the follow-up command
                    print("[Wake Word] Listening for command...")
                    cleanup_temp_files()
                    typed_followup = recorder.record_until_silence(RAW_AUDIO_PATH, silence_duration=1.8)
                    
                    if typed_followup is not None:
                        followup_text = typed_followup.strip()
                    else:
                        if os.path.exists(RAW_AUDIO_PATH):
                            preprocessor.preprocess_audio(RAW_AUDIO_PATH, CLEAN_AUDIO_PATH)
                            followup_text = asr.transcribe(CLEAN_AUDIO_PATH)
                        else:
                            followup_text = ""
                            
                    if followup_text:
                        print(f"[Main Loop] Processing follow-up: '{followup_text}'")
                        process_utterance(followup_text, asr)
                else:
                    # Case B: User said the wake word and command in one go (e.g., "Hey Jarvis, open Chrome")
                    print(f"[Main Loop] Processing single-breath command: '{command_part}'")
                    process_utterance(command_part, asr)
            else:
                # User spoke, but did not say the wake word.
                print(f"[Main Loop] Ignored speech (wake word '{config.WAKE_WORD}' not matched in '{text}')")
                
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n[Exit] Exiting Jarvis voice loop. Good bye Ameer!")
    finally:
        cleanup_temp_files()
        recorder.close()


if __name__ == "__main__":
    # Ensure system runs with python main.py
    run_voice_loop()
