"""
action_executor.py

Performs real actions such as PC application launches, web queries, and hardware toggling (GPIO).
Includes a PC simulation mode that prints actions to the terminal when RPi GPIO is unavailable or
SIMULATION_MODE is enabled.
Each action returns a confirmation string to be spoken by the TTS engine.
"""

import os
import sys
import subprocess
import webbrowser
import config

# Try to import gpiozero for Raspberry Pi execution
gpio_available = False
led_fan = None
led_lights = None

if not config.SIMULATION_MODE:
    try:
        from gpiozero import LED
        # Pin mappings
        led_fan = LED(17)      # Fan simulated by pin 17
        led_lights = LED(18)   # Lights simulated by pin 18
        gpio_available = True
        print("[Executor] Raspberry Pi GPIO initialised on pins 17 and 18.")
    except Exception as e:
        print(f"[Executor Warning] Failed to initialize GPIO: {e}. Running in PC Simulation Mode.")

# Try to import pyautogui and pywhatkit
pyautogui_available = False
try:
    import pyautogui
    pyautogui_available = True
except ImportError:
    pass

pywhatkit_available = False
try:
    import pywhatkit
    pywhatkit_available = True
except ImportError:
    pass


def turn_on_fan() -> str:
    """
    Turns on the fan (pin 17 HIGH) or simulates it.
    """
    try:
        if gpio_available and led_fan:
            led_fan.on()
            print("[GPIO] Pin 17 set to HIGH.")
            return "Pankha chala diya hai, Ameer!"
        else:
            print("[Simulation Action] Device: FAN, Action: ON (GPIO pin 17 -> HIGH)")
            return "Simulation mode me fan on kar diya, Ameer!"
    except Exception as e:
        print(f"[Executor Error] turn_on_fan failed: {e}", file=sys.stderr)
        return "Ameer, pankha on karne me kuch galti hui."


def turn_off_fan() -> str:
    """
    Turns off the fan (pin 17 LOW) or simulates it.
    """
    try:
        if gpio_available and led_fan:
            led_fan.off()
            print("[GPIO] Pin 17 set to LOW.")
            return "Pankha band kar diya hai, Ameer!"
        else:
            print("[Simulation Action] Device: FAN, Action: OFF (GPIO pin 17 -> LOW)")
            return "Simulation mode me fan band kar diya, Ameer!"
    except Exception as e:
        print(f"[Executor Error] turn_off_fan failed: {e}", file=sys.stderr)
        return "Ameer, pankha band karne me error aaya."


def turn_on_lights() -> str:
    """
    Turns on the lights (pin 18 HIGH) or simulates it.
    """
    try:
        if gpio_available and led_lights:
            led_lights.on()
            print("[GPIO] Pin 18 set to HIGH.")
            return "Lights on kar di hain, Ameer!"
        else:
            print("[Simulation Action] Device: LIGHTS, Action: ON (GPIO pin 18 -> HIGH)")
            return "Simulation mode me lights on kar di, Ameer!"
    except Exception as e:
        print(f"[Executor Error] turn_on_lights failed: {e}", file=sys.stderr)
        return "Lights on nahi ho sakeen, Ameer."


def turn_off_lights() -> str:
    """
    Turns off the lights (pin 18 LOW) or simulates it.
    """
    try:
        if gpio_available and led_lights:
            led_lights.off()
            print("[GPIO] Pin 18 set to LOW.")
            return "Lights band kar di hain, Ameer!"
        else:
            print("[Simulation Action] Device: LIGHTS, Action: OFF (GPIO pin 18 -> LOW)")
            return "Simulation mode me lights band kar di, Ameer!"
    except Exception as e:
        print(f"[Executor Error] turn_off_lights failed: {e}", file=sys.stderr)
        return "Lights off karne me error aaya."


def open_chrome() -> str:
    """
    Launches the Google Chrome browser.
    """
    try:
        # Cross-platform way to open the default web browser (which is usually Chrome/Edge/Safari)
        print("[Action] Opening default browser...")
        webbrowser.open("https://www.google.com")
        return "Browser khol raha hoon, Ameer!"
    except Exception as e:
        print(f"[Executor Warning] Webbrowser open failed: {e}. Trying system specific call...")
        try:
            if sys.platform == "win32":
                subprocess.Popen(["cmd", "/c", "start", "chrome"], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Google Chrome"])
            else:
                subprocess.Popen(["google-chrome"])
            return "Chrome launch kar diya, Ameer!"
        except Exception as ex:
            print(f"[Executor Error] open_chrome failed: {ex}", file=sys.stderr)
            return "Ameer, Chrome open nahi ho pa raha. Command command line se check karen."


def play_music() -> str:
    """
    Plays music using pywhatkit (YouTube stream) or opens a default YouTube music page.
    """
    query = "lofi music livestream"
    try:
        if pywhatkit_available:
            print(f"[Action] Playing '{query}' on YouTube via pywhatkit...")
            pywhatkit.playonyt(query)
            return "YouTube par music play kar raha hoon, Ameer!"
        else:
            print("[Action] pywhatkit not available. Opening lofi music search in browser...")
            webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
            return "Browser me YouTube music open kar diya hai, Ameer!"
    except Exception as e:
        print(f"[Executor Error] play_music failed: {e}", file=sys.stderr)
        # Fallback to browser open
        try:
            webbrowser.open("https://www.youtube.com")
            return "YouTube website khol di hai, Ameer. Wahan se music sun len."
        except Exception:
            return "Music play nahi ho saka, Ameer."


def set_ac_temperature(value: str) -> str:
    """
    Simulates setting the AC temperature to the requested value.
    """
    try:
        if not value:
            value = "24" # Default AC temperature
        print(f"[Action] Device: AC, Action: SET TEMPERATURE to {value} degrees")
        return f"Ameer, AC ka temperature {value} degrees par set kar diya hai!"
    except Exception as e:
        print(f"[Executor Error] set_ac_temperature failed: {e}", file=sys.stderr)
        return "AC temperature set karne me error aaya."


if __name__ == "__main__":
    # Unit tests
    print("Testing Executor actions in Simulation Mode...")
    print(turn_on_fan())
    print(turn_off_lights())
    print(set_ac_temperature("22"))
    # Note: open_chrome and play_music are skipped in this unit test to avoid spawning windows
