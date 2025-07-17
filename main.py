#!/usr/bin/env python3

import datetime
from evdev import InputDevice, categorize, ecodes, KeyEvent

# find device path using 'ls -l /dev/input/by-id/'
USB_CONTROLLER_DEVICE_PATH = "/dev/input/event4"

# map button codes (from 'sudo evtest') to actions
BUTTON_MAPPINGS = {
    304: "intersection",
    305: "lane_departure",
    308: "slow_down",
    307: "intervention",
    315: "other",
}

def monitor_robot_actions():
    try:
        dev = InputDevice(USB_CONTROLLER_DEVICE_PATH)
        print(f"Monitoring Xbox controller: {dev.name} ({dev.path}) for robot actions.")
        print("Press A, B, X, Y, or Start buttons. Ctrl+C to stop.")

        for event in dev.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)

                if event.code in BUTTON_MAPPINGS and key_event.keystate == KeyEvent.key_down:
                    action_message = BUTTON_MAPPINGS[event.code]
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{current_time}] Action Logged: {action_message}")

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
