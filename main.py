#!/usr/bin/env python3

import os
import time
import datetime
import subprocess
import threading
import requests
from evdev import InputDevice, categorize, ecodes, KeyEvent

# --- Configuration ---
LOG_FILE_PATH = "/home/pattern/alden_debug_logger/robot_actions.log"
VIDEO_DIR_PATH = "/home/pattern/videos"
DATADOG_API_KEY = "055ab7597b8643faa926dcd3a229996f"
DATADOG_LOG_URL = "https://http-intake.logs.datadoghq.com/api/v2/logs"
USB_CONTROLLER_DEVICE_PATH = "/dev/input/event0"  # Change based on sudo evtest output
DEBUG_MODE = False

BUTTON_MAPPINGS = {
    2: "intersection",
    3: "lane_departure",
    4: "slow_down",
    5: "intervention",
    6: "other",

    000: "display_dashboard",
    000: "clear_log_history",
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

# --- Datadog Upload ---
def is_wifi_connected():
    # Check if wlan0 is up and has an IP address
    try:
        with open('/sys/class/net/wlan0/operstate') as f:
            if f.read().strip() == 'up':
                return True
    except FileNotFoundError:
        pass
    return False

def upload_logs_to_datadog():
    if not is_wifi_connected():
        print("WiFi not connected, skipping Datadog upload.")
        return
    if not os.path.exists(LOG_FILE_PATH):
        print("No log file to upload.")
        return
    with open(LOG_FILE_PATH, "r") as f:
        log_content = f.read()
    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": DATADOG_API_KEY
    }
    payload = [{"message": log_content, "ddsource": "raspi_robot_logger"}]
    try:
        resp = requests.post(DATADOG_LOG_URL, json=payload, headers=headers)
        print("Datadog upload status:", resp.status_code)
    except Exception as e:
        print("Failed to upload logs to Datadog:", e)

def periodic_datadog_uploader(stop_event):
    # Periodically upload logs to Datadog when WiFi is available
    while not stop_event.is_set():
        upload_logs_to_datadog()
        # upload every 10 minutes
        for _ in range(60):
            if stop_event.is_set():
                break
            time.sleep(10)

# --- Video Handling ---
def delete_old_videos():
    now = time.time()
    for filename in os.listdir(VIDEO_DIR_PATH):
        filepath = os.path.join(VIDEO_DIR_PATH, filename)
        if os.path.isfile(filepath):
            if now - os.path.getmtime(filepath) > 3 * 24 * 3600:  # older than 3 days
                print(f"Deleting old video: {filename}")
                os.remove(filepath)

def video_recorder_loop(stop_event):
    # Loop: record 5-minute videos until stop_event is set
    while not stop_event.is_set():
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"myvideo_{timestamp}.h264"
        video_filepath = os.path.join(VIDEO_DIR_PATH, video_filename)
        print(f"Recording video: {video_filename}")
        proc = subprocess.Popen(
            ["libcamera-vid", "-t", str(5*60*1000), "-o", video_filepath],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        start_time = time.time()
        while proc.poll() is None:
            if stop_event.is_set():
                proc.terminate()
                break
            time.sleep(1)
        delete_old_videos()  # delete old videos at each rotation

# --- Main Action Logger ---
def monitor_robot_actions(stop_event):
    try:
        dev = InputDevice(USB_CONTROLLER_DEVICE_PATH)
        print(f"Monitoring: {dev.name} ({dev.path})")
        print("Press keys to log actions | Ctrl+C to stop") 

        while not stop_event.is_set():
            for event in dev.read_loop():
                if stop_event.is_set():
                    break
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

# --- Main Entrypoint ---
def main():
    os.makedirs(VIDEO_DIR_PATH, exist_ok=True)

    stop_event = threading.Event()

    # Start video recorder in a thread
    video_thread = threading.Thread(target=video_recorder_loop, args=(stop_event,))
    video_thread.start()

    # Start Datadog uploader in a thread
    datadog_thread = threading.Thread(target=periodic_datadog_uploader, args=(stop_event,))
    datadog_thread.start()

    # Start robot action logger in main thread
    try:
        monitor_robot_actions(stop_event)
    except KeyboardInterrupt:
        print("Exiting, stopping threads...")
        stop_event.set()
        video_thread.join()
        datadog_thread.join()

if __name__ == "__main__":
    main()
