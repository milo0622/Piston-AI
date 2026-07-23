from lib import agent
import sys
from pathlib import Path
import readline
from lib import tui
import threading

args = sys.argv[1:]
def main():
    if len(args) == 1:
        chatPath = f"userdata/chats/{args[0]}"
    else:
        chatPath = "userdata/chats/fallback.json"
    tuiUtils = tui.TUI()
    threading.Thread(target=tuiUtils.loadingIcon).start()
    mainAgent = agent.Agent(chatHistoryPath=chatPath, model="llama3.1:8b")
    tuiUtils.stop = True
    print("", end="", flush=True)

    while True:
        try:
            uInput = input("Ask me anything> ")
            if not uInput.strip():
                continue
            if uInput.lower() == "/exit":
                print('bye!')
                break
            mainAgent.ask(uInput)
            print()
        except (KeyboardInterrupt, EOFError):
            print("bye!")
            break

if __name__ == "__main__":
    main()
