import asyncio
import platform
import subprocess
import ctypes
if platform.system() == "Windows":
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager, GlobalSystemMediaTransportControlsSessionPlaybackStatus
if platform.system() == "Darwin":
    import Quartz
import time
import json
import shutil

class MediaControl:
    def __init__(self):
        self.OS = platform.system() if platform.system() in ("Linux", "Windows") else "macOS"

    def mediaButton(self, action):
        if action == "pause":
            keycode = "nowplaying-cli pause"
            mediaBtn = 0xB3
            event = "xdotool key XF86AudioPlay"
        elif action == "play":
            keycode = "nowplaying-cli play"
            mediaBtn = 0xB3
            event = "xdotool key XF86AudioPlay"
        elif action == "next":
            keycode = "nowplaying-cli next"
            mediaBtn = 0xB0
            event = "xdotool key XF86AudioNext"
        elif action == "previous":
            keycode = "nowplaying-cli previous"
            mediaBtn = 0xB1
            event = "xdotool key XF86AudioPrev"

        if self.OS == "macOS":
            try:
                subprocess.run(keycode, shell=True)
            except subprocess.CalledProcessError:
                pass
        elif self.OS == "Windows":
            extendedKey = 0x0001
            keyup = 0x0002
            mediaBtn = 0xB3

            ctypes.windll.user32.keybd_event(mediaBtn, 0, extendedKey, 0)
            time.sleep(0.3)
            ctypes.windll.user32.keybd_event(mediaBtn, 0, extendedKey|keyup, 0)
        elif self.OS == "Linux":
            try:
                subprocess.run(event, shell=True)
            except subprocess.CalledProcessError:
                pass

    def parseMetadata(self):
        if self.OS == "macOS":
            if shutil.which("nowplaying-cli"):
                try:
                    result = subprocess.run("nowplaying-cli get --json title album artist", shell=True, check=True, capture_output=True)
                    result = json.loads(result.stdout)

                    playing = subprocess.run("nowplaying-cli get playbackRate", shell=True, check=True, capture_output=True).stdout.decode("utf-8")
                    print(playing)
                    playing = True if playing else False

                    result["playing"] = playing
                    
                    if not result["title"] and not result["album"] and not result["artist"]:
                        result = { "status": "No media is currently playing"}
                except Exception as e:
                    result =  { "status": f"Failed to fetch metadata currently playing: {e}" }
                return result
            else:
                msg = "Please install nowplaying-cli via brew first"
                print(msg)
                return {
                    "status": msg
                }
        elif self.OS == "Windows":
            async def requestRemote():
                manager =  await GlobalSystemMediaTransportControlsSessionManager.request_async()
                session = manager.get_current_session()
                if not session:
                    return { "status": "No media currently playing" }, None
                return await session.try_get_media_properties_async(), session
            props, session = asyncio.run(requestRemote())
            if isinstance(props, dict):
                return props
            playing = session.get_playback_info().playback_status
            playing = playing == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
            if props:
                return {
                    "title": props.title,
                    "artist": props.artist,
                    "album": props.album_title,
                    "playing": playing
                }
            return {
                "status": "No metadata found"
            }
        else:
            return {
                "status": f"The OS {self.OS} is not supported"
            }

def playMedia():
    mc = MediaControl()
    try:
        mc.mediaButton("play")
        payload = {
            "status":"Success"
        }
    except Exception as e:
        print(f"Failed to play media: {e}")
        payload = {
            "status":f"Failed to play media: {e}"
        }
    return json.dumps(payload)

def pauseMedia():
    mc = MediaControl()
    try:
        mc.mediaButton("pause")
        payload = {
            "status":"Success"
        }
    except Exception as e:
        print(f"Failed to pause media: {e}")
        payload = {
            "status":f"Failed to pause media: {e}"
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

def fetchCurrentPlaying() -> str:
    mc = MediaControl()
    result = mc.parseMetadata()

    return json.dumps(result)