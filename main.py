#!/usr/bin/env python3

import datetime
import os
from evdev import InputDevice, categorize, ecodes, KeyEvent

# --- Configuration ---
USB_CONTROLLER_DEVICE_PATH = "/dev/input/event4"
LOG_FILE_PATH = "/home/pattern/pi/robot_actions.log"
DEBUG_MODE = False

BUTTON_MAPPINGS = {
    304: "intersection",
    305: "lane_departure",
    308: "slow_down",
    307: "intervention",
    314: "display_dashboard",
    315: "other",
    167: "clear_log_history", # Changed button code for clearing logs to 167
}

# --- Logging and Dashboard Functions ---
def log_action(message):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{current_time}] Action Logged: {message}"
    print(log_entry)
    try:
        with open(LOG_FILE_PATH, "a") as f:
            f.write(log_entry + "\n")
    except IOError as e:
        print(f"Error writing to log file {LOG_FILE_PATH}: {e}")

def display_dashboard():
    print("\n--- Robot Actions Dashboard (Past 7 Days) ---")
    if not os.path.exists(LOG_FILE_PATH):
        print("No log file found. Perform actions first!")
        print("-------------------------------------------\n")
        return

    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    try:
        found_actions = False
        with open(LOG_FILE_PATH, "r") as f:
            for line in f:
                try:
                    timestamp_str = line[1:20]
                    log_time = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    if log_time >= seven_days_ago:
                        print(line.strip())
                        found_actions = True
                except (ValueError, IndexError):
                    pass
            if not found_actions:
                print("No actions logged in the past 7 days.")
        print("-------------------------------------------\n")
    except IOError as e:
        print(f"Error reading log file {LOG_FILE_PATH}: {e}")

def clear_action_log():
    """Deletes the action log file."""
    print("\n--- Clearing Action Log History ---")
    if os.path.exists(LOG_FILE_PATH):
        try:
            os.remove(LOG_FILE_PATH)
            print(f"Action log file '{LOG_FILE_PATH}' cleared successfully.")
        except OSError as e:
            print(f"Error clearing log file '{LOG_FILE_PATH}': {e}")
    else:
        print("No log file found to clear.")
    print("-----------------------------------\n")


# --- Main Program ---
def monitor_robot_actions():
    try:
        dev = InputDevice(USB_CONTROLLER_DEVICE_PATH)
        print(f"Monitoring Xbox controller: {dev.name} ({dev.path})")
        # Updated prompt to reflect the new button code for clearing logs
        print("A, B, X, Y: actions | Select/Back: dashboard | Start: 'other' | Button 167: clear log | Ctrl+C: stop") 

        for event in dev.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                if event.code in BUTTON_MAPPINGS and key_event.keystate == KeyEvent.key_down:
                    action_type = BUTTON_MAPPINGS[event.code]
                    
                    if DEBUG_MODE:
                        print(f"DEBUG: Detected {action_type} (code {event.code})")

                    if action_type == "display_dashboard":
                        display_dashboard()
                    elif action_type == "clear_log_history":
                        clear_action_log()
                    else:
                        log_action(action_type)

    except FileNotFoundError:
        print(f"Error: Controller not found at {USB_CONTROLLER_DEVICE_PATH}. Check connection and path.")
    except PermissionError:
        print("Error: Permission denied. Run with 'sudo'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Exiting robot action logger.")

if __name__ == "__main__":
    monitor_robot_actions()
