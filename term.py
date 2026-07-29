from lib import agent
import sys
from pathlib import Path
import readline
from lib import tui
import threading
from main import *
from dotenv import dotenv_values

args = sys.argv[1:]
def main():
    if len(args) == 1:
        chatPath = f"userdata/chats/{args[0]}"
    else:
        chatPath = "userdata/chats/fallback.json"
    tuiUtils = tui.TUI()
    threading.Thread(target=tuiUtils.loadingIcon).start()
    model = modelID()
    mainAgent = agent.Agent(chatHistoryPath=chatPath, model=model, apiKeys=readEnv())
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
            mainAgent.ask(message=uInput)
            print()
        except (KeyboardInterrupt, EOFError):
            print("bye!")
            return

def readEnv():
    payload = {}
    config = dotenv_values(".env")
    for key in config:
        payload[key] = config[key]
    return payload

if __name__ == "__main__":
    main()
