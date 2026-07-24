from lib import tui
print("\033[3GImporting libraries...", end="\r")
tempTui = tui.TUI()
import threading
threading.Thread(target=tempTui.loadingIcon).start()
from lib import agent, stt, wakeword, SFX
from pathlib import Path
tempTui.stop = True
print("√")


class Piston:
    def __init__(self, model="llama3.1:8b", chatHistoryPath="userdata/chats/fallback.json"):
        print("\033[3GInit...", end="\r")
        self.tui = tui.TUI()
        self.agent = agent.Agent(model=model, chatHistoryPath=chatHistoryPath)
        soundfiles = ["assets/startup.mp3", "assets/startSTT.mp3", "assets/stopSTT.mp3"]
        for idx, soundfile in enumerate(soundfiles):
            soundfiles[idx] = Path(soundfile).resolve()
        self.sfx = SFX.SFX(*soundfiles)
        self.tui.stop = True
        print("√")
        self.stt = stt.STT()
        self.wakeword = wakeword.Wakeword(threshold=0.75)
        if not self.wakeword.loadModel:
            print("Failed to load wakeword. Fallback to manual mode.")
            self.wakewordSuccess = False
        else:
            self.wakewordSuccess = True
        self.open = False

    def main(self):
        print("Welcome to Piston AI!")
        try:
            while True:
                if not self.open:
                    if not self.wakewordSuccess:
                        input("Press Enter to start STT.")
                    else:
                        print("Listening for wakeword (Hey Piston)...")
                        self.wakeword.listenForWake()
                text, _ = self.stt.main(3)
                if text:
                    self.open = self.agent.ask(message=text)
                    continue
                self.open = False
                continue
        except (KeyboardInterrupt, EOFError):
            self.tui.stop = True
            print("Bye!")
            return

if __name__ == "__main__":
    PistonAI = Piston(model="llama3.1:8b")
    PistonAI.main()