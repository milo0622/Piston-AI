import platform
import subprocess
import ctypes
if platform.system() == "Darwin":
    import Quartz
import time
import json
from pynput.keyboard import Key, Controller

class MediaControl:
    def __init__(self):
        self.OS = platform.system() if platform.system() in ("Linux", "Windows") else "macOS"
        self.Key = Controller()

    def mediaButton(self, action):
        if action == "pause":
            keycode = 16
            mediaBtn = 0xB3
            event = "xdotool key XF86AudioPlay".split()
        elif action == "next":
            keycode = 17
            mediaBtn = 0xB0
            event = "xdotool key XF86AudioNext".split()
        elif action == "previous":
            keycode = 18
            mediaBtn = 0xB1
            event = "xdotool key XF86AudioPrev".split()

        if self.OS == "macOS":
            eventDown = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(14, (0,0), 0xa00, 0, 0, None, 8, (keycode << 16) | (0xa << 8), -1)
            eventUp = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(14, (0, 0), 0xb00, 0, 0, None, 8, (keycode << 16) | (0xb << 8), -1)

            Quartz.CGEventPost(Quartz.kCGHIDEventTap, eventDown.CGEvent())
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, eventUp.CGEvent())
        elif self.OS == "Windows":
            extendedKey = 0x0001
            keyup = 0x0002
            mediaBtn = 0xB3

            ctypes.windll.user32.keybd_event(mediaBtn, 0, extendedKey, 0)
            time.sleep(0.3)
            ctypes.windll.user32.keybd_event(mediaBtn, 0, extendedKey|keyup, 0)
        elif self.OS == "Linux":
            try:
                subprocess.run(event)
            except subprocess.CalledProcessError:
                pass
def playpauseMedia():
    mc = MediaControl()
    try:
        mc.mediaButton("pause")
        payload = {
            "status":"Success"
        }
    except Exception as e:
        print(f"Failed to play/pause media: {e}")
        payload = {
            "status":f"Failed to play/pause media: {e}"
        }
    return json.dumps(payload)

def nextTrack():
    mc = MediaControl()
    try:
        mc.mediaButton("next")
        payload = {
            "status":"Success"
        }
    except Exception as e:
        print(f"Failed to skip to next track: {e}")
        payload = {
            "status":f"Failed to skip to next track: {e}"
        }
    return json.dumps(payload)

def previousTrack():
    mc = MediaControl()
    try:
        mc.mediaButton("previous")
        payload = {
            "status":"Success"
        }
    except Exception as e:
        print(f"Failed to return to previous track: {e}")
        payload = {
            "status":f"Failed to return to previous track: {e}"
        }
    return json.dumps(payload)
    