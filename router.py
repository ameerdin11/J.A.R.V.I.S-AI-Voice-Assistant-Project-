"""
router.py

Decides whether the user's transcribed text represents a "command" or a "conversation".
Scans the text for device names and action words, including Hinglish variations.
"""

import sys

# Define keyword lists
DEVICES = ["fan", "light", "lights", "ac", "tv", "television", "temp", "temperature", "chrome", "browser", "music", "song", "youtube"]
ACTIONS = ["on", "off", "open", "close", "play", "stop", "set", "turn", "karo", "chalao", "band", "kholo", "khol", "kardoo", "kar"]

def route_input(text: str) -> str:
    """
    Analyzes the text and routes it to either "command" or "conversation".
    Returns 'command' or 'conversation'.
    """
    try:
        if not text:
            return "conversation"

        # Preprocess text: lower case and strip punctuation
        clean_text = text.lower().strip()
        for char in [".", ",", "?", "!", "-", "_"]:
            clean_text = clean_text.replace(char, " ")
            
        words = clean_text.split()
        
        # Check for commands like "open chrome", "play music", "set temperature"
        # We look for combinations of action words and target/device words
        has_device = any(dev in words for dev in DEVICES)
        has_action = any(act in words for act in ACTIONS)
        
        # Special command patterns (e.g. "open...", "play...")
        starts_with_action = False
        if words:
            starts_with_action = words[0] in ["open", "play", "set", "close", "turn"]
            
        # Specific combinations (e.g. "fan on", "light off", "open chrome")
        if (has_device and has_action) or starts_with_action:
            print(f"[Router] Routed as COMMAND. (Text: '{text}')")
            return "command"
            
        print(f"[Router] Routed as CONVERSATION. (Text: '{text}')")
        return "conversation"
        
    except Exception as e:
        print(f"[Router Error] Failed to route input: {e}", file=sys.stderr)
        # Default fallback to conversation
        return "conversation"

if __name__ == "__main__":
    # Test cases
    test_phrases = [
        "Hey Jarvis, how are you?",
        "fan on karo",
        "turn off the lights",
        "open Chrome",
        "what is machine learning?",
        "play some music",
        "I am feeling very tired today",
        "set AC temperature to 24",
        "tell me a joke about a fan"
    ]
    
    print("Testing Router...")
    for phrase in test_phrases:
        mode = route_input(phrase)
        print(f"Phrase: '{phrase}' -> Mode: {mode}")
