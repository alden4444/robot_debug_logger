#!/usr/bin/env python3

import time
import datetime
from evdev import InputDevice, categorize, ecodes, KeyEvent

# --- Configuration ---
# Path to your Xbox controller's input device.
# This typically looks like /dev/input/eventX where X is a number.
USB_CONTROLLER_DEVICE_PATH = "/dev/input/event4"

# Mapping of numerical key codes to specific action messages.
# These codes are found using 'sudo evtest' on your Raspberry Pi.
BUTTON_MAPPINGS = {
    304: "intersection",     # 'A' button (BTN_SOUTH)
    305: "lane_departure",   # 'B' button (BTN_EAST)
    308: "slow_down",        # 'X' button (BTN_WEST)
    307: "intervention",     # 'Y' button (BTN_NORTH)
    315: "other",            # 'Start' button (BTN_START)
}

# --- Main Program Function ---
def monitor_robot_actions():
    try:
        # Initialize the input device for the Xbox controller.
        dev = InputDevice(USB_CONTROLLER_DEVICE_PATH)
        print(f"Monitoring Xbox controller: {dev.name} ({dev.path}) for robot actions.")
        print("Press A, B, X, Y, or Start buttons to log an action. Press Ctrl+C to stop.")

        # Loop continuously to read events from the controller.
        for event in dev.read_loop():
            # Filter for key press/release events.
            if event.type == ecodes.EV_KEY:
                # Categorize the raw event into a KeyEvent object for easier access to properties.
                key_event = categorize(event)

                # Check if the event's numerical code is in our defined mappings
                # AND if the button was pressed down (not released).
                if event.code in BUTTON_MAPPINGS and key_event.keystate == KeyEvent.key_down:
                    # Retrieve the corresponding action message.
                    action_message = BUTTON_MAPPINGS[event.code]
                    # Get the current time and format it.
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # Print the timestamped action message.
                    print(f"[{current_time}] Action Logged: {action_message}")

    # --- Error Handling ---
    except FileNotFoundError:
        print(f"Error: Xbox controller device not found at {USB_CONTROLLER_DEVICE_PATH}.")
        print("Please ensure the controller is connected and the path is correct.")
    except PermissionError:
        print("\nERROR: Permission denied. You must run this script with 'sudo'.")
        print("Example: sudo ./venv/bin/python3 ./robot_action_logger.py")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Ensure a clean exit message.
        print("Exiting robot action logger.")

# --- Script Entry Point ---
if __name__ == "__main__":
    monitor_robot_actions()
