"""
command_mapper.py

Maps NLU engine output (intents and entities dict) to real callable python functions in action_executor.py.
Handles arguments (e.g. temperature value) and returns the function reference along with its arguments.
"""

import sys
import action_executor

def get_action_callable(nlu_output: dict) -> tuple:
    """
    Parses the NLU engine output dictionary and matches it to a function in action_executor.py.
    Returns:
        tuple: (function_callable, list_of_arguments) or (None, None) if no match found.
    """
    try:
        intent = nlu_output.get("intent")
        device = nlu_output.get("device")
        action = nlu_output.get("action")
        value = nlu_output.get("value")
        app = nlu_output.get("app")

        # 1. Device Control Intent
        if intent == "device_control":
            if device == "fan":
                if action == "off":
                    return action_executor.turn_off_fan, []
                else:
                    # Default to turning on if action is unspecified or "on"
                    return action_executor.turn_on_fan, []
                    
            elif device == "lights":
                if action == "off":
                    return action_executor.turn_off_lights, []
                else:
                    return action_executor.turn_on_lights, []
                    
            elif device == "ac":
                # For AC, if a value (temp) is parsed or action is "set"
                if value or action == "set":
                    return action_executor.set_ac_temperature, [value]
                elif action == "off":
                    # We can print simulator off or set it to off
                    print("[Mapper] AC Off requested. Simulating via set_ac_temperature('OFF')")
                    return action_executor.set_ac_temperature, ["OFF"]
                else:
                    # Default on temperature
                    return action_executor.set_ac_temperature, ["24"]

        # 2. PC Control Intent
        elif intent == "pc_control" or action == "play":
            if app == "chrome":
                return action_executor.open_chrome, []
            elif app == "music" or app == "youtube" or action == "play":
                return action_executor.play_music, []

        print(f"[Mapper Warning] No executable action mapped for NLU output: {nlu_output}")
        return None, None

    except Exception as e:
        print(f"[Mapper Error] Mapping failed: {e}", file=sys.stderr)
        return None, None

if __name__ == "__main__":
    # Test mapping
    print("Testing Command Mapper...")
    
    test_nlu_dicts = [
        {"intent": "device_control", "device": "fan", "action": "on", "value": None, "app": None},
        {"intent": "device_control", "device": "lights", "action": "off", "value": None, "app": None},
        {"intent": "pc_control", "device": None, "action": "open", "value": None, "app": "chrome"},
        {"intent": "pc_control", "device": None, "action": "play", "value": None, "app": "music"},
        {"intent": "device_control", "device": "ac", "action": "set", "value": "22", "app": None}
    ]
    
    for nlu in test_nlu_dicts:
        func, args = get_action_callable(nlu)
        if func:
            print(f"Mapped {nlu} -> Function: {func.__name__}, Args: {args}")
        else:
            print(f"Mapped {nlu} -> No Function matched")
