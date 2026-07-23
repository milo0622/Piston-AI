from lib import tui
print("\033[3GImporting libraries...", end="\r")
tempTui = tui.TUI()
import threading
threading.Thread(target=tempTui.loadingIcon).start()
from lib import agent, stt
tempTui.stop = True
print("√")


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