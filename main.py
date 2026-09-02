from lib import tui
print("\033[3GImporting libraries...", end="\r")
tempTui = tui.TUI()
import threading
threading.Thread(target=tempTui.loadingIcon).start()
if __name__ == "__main__":
    from lib import agent, stt, wakeword, SFX
from pathlib import Path
import json
import os
import sys
from dotenv import dotenv_values
tempTui.stop = True
print("√")

args = sys.argv[1:]

class Piston:   
    def __init__(self, chatHistoryPath="userdata/chats/fallback.json"):
        print("\033[3GInit...", end="\r")
        self.tui = tui.TUI()
        self.apiKeys = None
        self.readDotEnv()
        self.model = modelID()
        self.agent = agent.Agent(chatHistoryPath=chatHistoryPath, model=self.model, apiKeys=self.apiKeys)
        soundfiles = ["assets/startup.mp3", "assets/startSTT.mp3", "assets/stopSTT.mp3"]
        for idx, soundfile in enumerate(soundfiles):
            soundfiles[idx] = Path(soundfile).resolve()
        self.sfx = SFX.SFX(*soundfiles)
        self.tui.stop = True
        print("√")
        self.stt = stt.STT()
        self.wakeword = wakeword.Wakeword(threshold=0.6)
        if not self.wakeword.loadModel:
            print("Failed to load wakeword. Fallback to manual mode.")
            self.wakewordSuccess = False
        else:
            self.wakewordSuccess = True
        if "-m" in args:
            print("Manual mode enabled.")
            self.wakewordSuccess = False
        self.open = False
        self.sfx.playSound(0, blocking=True)
            
    def main(self):
        print("Welcome to Piston AI!")
        try:
            while True:
                if not self.open:
                    if not self.wakewordSuccess:
                        input("Press Enter to start STT.")
                    else:
                        print("\nListening for wakeword (Hey Piston)...")
                        self.wakeword.listenForWake()
                self.sfx.playSound(1, blocking=False)
                text, _ = self.stt.main(3)
                self.sfx.playSound(2, blocking=False)
                if text is None:
                    continue
                if text.strip().rstrip():
                    try:
                        self.open = self.agent.ask(message=text)
                        print()
                    except (KeyboardInterrupt, EOFError):
                        self.agent.tui.stop = True
                        print("Operation aborted")
                        continue
                    continue
                self.open = False
                continue
        except (KeyboardInterrupt, EOFError):
            self.tui.stop = True
            print("Bye!")
            sys.exit()  

    def readDotEnv(self):
        self.apiKeys = {}
        config = dotenv_values()
        for key in config:
            self.apiKeys[key] = config[key]

def modelID():
    filePath = "userdata/config.json"
    default = {
        "provider":"ollama",
        "model":"gemma4:e4b"
    }
    Path(os.path.dirname(filePath)).mkdir(parents=True, exist_ok=True)
    if not Path(filePath).exists():
        with open(filePath, "w") as f:
            json.dump(default, f, indent=4)
        file = default
    else:
        try:
            with open(filePath, "r") as f:
                file = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(filePath, "w") as f:
                json.dump(default, f, indent=4)
            file = default
        except (KeyboardInterrupt, EOFError):
            print("Operation aborted.")
            sys.exit()
    if file:
        model = file.get("model")
    else:
        model = "gemma:e4b"
    return model

if __name__ == "__main__":
    PistonAI = Piston()
    PistonAI.main()
