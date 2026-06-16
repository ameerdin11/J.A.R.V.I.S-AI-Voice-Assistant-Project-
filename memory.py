"""
memory.py

Manages in-memory conversation history for Jarvis.
Stores messages as a list of dicts: [{"role": "user"/"assistant", "content": "..."}]
Allows adding messages, retrieving the full history, clearing it, and trimming it to avoid token overflow.
"""

import sys

# Module-level variable to store conversation messages
_history = []

def get_history():
    """
    Returns the current conversation history.
    """
    try:
        return _history
    except Exception as e:
        print(f"[Memory Error] Failed to get history: {e}", file=sys.stderr)
        return []

def add_message(role: str, content: str):
    """
    Appends a new message to the history and automatically trims if it exceeds the limit.
    """
    try:
        if role not in ["user", "assistant", "system"]:
            print(f"[Memory Warning] Unknown role: {role}", file=sys.stderr)
        _history.append({"role": role, "content": content})
        trim_history()
    except Exception as e:
        print(f"[Memory Error] Failed to add message: {e}", file=sys.stderr)

def clear_history():
    """
    Resets the conversation history list.
    """
    global _history
    try:
        _history = []
    except Exception as e:
        print(f"[Memory Error] Failed to clear history: {e}", file=sys.stderr)

def trim_history(max_turns=20):
    """
    Trims the conversation history to keep only the last `max_turns` messages.
    If system message is included at the beginning, we make sure to handle it correctly.
    Note: Usually, llm_brain prepends the system prompt dynamically, so this history
    contains only the user and assistant turns.
    """
    global _history
    try:
        if len(_history) > max_turns:
            # Keep the last max_turns messages
            _history = _history[-max_turns:]
    except Exception as e:
        print(f"[Memory Error] Failed to trim history: {e}", file=sys.stderr)

if __name__ == "__main__":
    # Quick module test
    print("Testing Memory module...")
    clear_history()
    add_message("user", "Hello Jarvis")
    add_message("assistant", "Hello Ameer! Aap kaise hain?")
    
    print(f"History length: {len(get_history())}")
    print(get_history())
    
    # Test trimming
    for i in range(25):
        add_message("user", f"Message {i}")
        add_message("assistant", f"Response {i}")
        
    print(f"History length after exceeding limit: {len(get_history())}")
    print("First item in history now:", get_history()[0])
    print("Last item in history now:", get_history()[-1])
