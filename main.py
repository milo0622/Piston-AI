from lib import tui
print("\033[3GImporting libraries...", end="\r")
tempTui = tui.TUI()
import threading
threading.Thread(target=tempTui.loadingIcon).start()
print("√")
from lib import agent, stt
tempTui.stop = True

class Piston:
    def __init__(self, model="llama3.1:8b", chatHistoryPath="userdata/chats/fallback.json"):
        print("\033[3GInit...")
        self.tui = tui.TUI()
        self.agent = agent.Agent(model=model, chatHistoryPath=chatHistoryPath)
        self.tui.stop = True
        self.stt = stt.STT()
        self.open = False

    def main(self):
        print("Welcome to Piston AI!")
        try:
            while True:
                if not self.open:
                    input("Press Enter to start STT.")
                text, _ = self.stt.main(3)
                if text:
                    response = self.agent.ask(message=text)
                if not response:
                    self.open = False
                    continue
                if response.endswith("[CLOSE]"):
                    self.open = False
                    continue
                if response.endswith("[OPEN]"):
                    self.open = True
                    continue
                self.open = False
                continue
        except (KeyboardInterrupt, EOFError):
            self.tui.stop = True
            print("Bye!")
            return

if __name__ == "__main__":
    PistonAI = Piston(model="llama3.2:3b")
    PistonAI.main()