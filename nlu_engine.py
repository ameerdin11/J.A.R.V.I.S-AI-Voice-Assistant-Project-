"""
nlu_engine.py

Parses transcribed text to extract intents (e.g., device_control, pc_control)
and entities (e.g., device, action, app, value).
Uses robust rule-based keyword matching first, and optionally integrates spaCy if available.
"""

import re
import sys

# Optional spaCy import
spacy_available = False
nlp = None
try:
    import spacy
    # Try loading English model
    try:
        nlp = spacy.load("en_core_web_sm")
        spacy_available = True
    except OSError:
        print("[NLU Warning] spaCy model 'en_core_web_sm' not found. Will use rule-based matching only.")
except ImportError:
    print("[NLU Warning] 'spacy' library not installed. Will use rule-based matching only.")

def parse_intent_and_entities(text: str) -> dict:
    """
    Parses user text to extract intent and entities.
    Returns:
        dict: {"intent": str, "device": str/None, "action": str/None, "value": str/None, "app": str/None}
    """
    # Initialize response dictionary
    result = {
        "intent": "chitchat",
        "device": None,
        "action": None,
        "value": None,
        "app": None
    }

    try:
        if not text:
            return result

        clean_text = text.lower().strip()
        
        # 1. Check for Greetings
        greetings = ["hello", "hi", "hey", "how are you", "kya hal hai", "kya haal", "kya chal", "wassup"]
        if any(greet in clean_text for greet in greetings):
            result["intent"] = "greeting"

        # 2. Extract Value (e.g., numbers for AC temperature)
        digits = re.findall(r'\d+', clean_text)
        if digits:
            result["value"] = digits[0]

        # 3. Extract Device
        devices_map = {
            "fan": ["fan", "pankha", "pankhe"],
            "lights": ["light", "lights", "bulb", "bijli"],
            "ac": ["ac", "air conditioner", "cool"],
            "tv": ["tv", "television", "screen"]
        }
        for dev_key, dev_aliases in devices_map.items():
            if any(alias in clean_text for alias in dev_aliases):
                result["device"] = dev_key
                result["intent"] = "device_control"
                break

        # 4. Extract App / Target
        apps_map = {
            "chrome": ["chrome", "google chrome", "browser"],
            "youtube": ["youtube", "yt"],
            "music": ["music", "song", "songs", "gaana", "gaane", "playlist"]
        }
        for app_key, app_aliases in apps_map.items():
            if any(alias in clean_text for alias in app_aliases):
                result["app"] = app_key
                result["intent"] = "pc_control"
                break

        # 5. Extract Action
        actions_map = {
            "on": ["on", "chalao", "chala", "start", "turn on", "switch on", "kholo", "khol"],
            "off": ["off", "band", "stop", "turn off", "switch off"],
            "open": ["open", "launch", "kholo", "khol"],
            "close": ["close", "exit", "band karo"],
            "play": ["play", "baja", "bajao", "start playing"],
            "set": ["set", "change", "karlo", "kardo", "tempera"]
        }
        for act_key, act_aliases in actions_map.items():
            for alias in act_aliases:
                # Use boundary check or substring check
                if alias in clean_text:
                    result["action"] = act_key
                    break
            if result["action"]:
                break

        # Adjust intent based on entities found
        if result["device"]:
            result["intent"] = "device_control"
        elif result["app"]:
            result["intent"] = "pc_control"
            
        # Optional: spaCy NER processing to extract numeric value or other entities
        if spacy_available and nlp:
            try:
                doc = nlp(text)
                # If value is not set, look for CARDINAL/QUANTITY
                if not result["value"]:
                    for ent in doc.ents:
                        if ent.label_ in ["CARDINAL", "QUANTITY"]:
                            result["value"] = ent.text
                            break
            except Exception as e:
                print(f"[NLU Warning] spaCy processing failed: {e}", file=sys.stderr)

        return result

    except Exception as e:
        print(f"[NLU Error] Parsing failed: {e}", file=sys.stderr)
        return result

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "Hey Jarvis, how are you?",
        "fan on karo",
        "turn off the lights",
        "open Chrome",
        "play music",
        "set AC temperature to 24",
        "close browser",
        "Hey Jarvis, I am feeling very tired today"
    ]
    
    print("Testing NLU Engine...")
    for tc in test_cases:
        res = parse_intent_and_entities(tc)
        print(f"Text: '{tc}'\nParsed: {res}\n")
