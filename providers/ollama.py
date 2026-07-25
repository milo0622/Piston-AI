import ollama
import threading
from lib import tui

class Ollama:
    def __init__(self, model="llama3.1:8b"):
        self.tuiUtils = tui.TUI()
        self.model = model
        self.fullCheck()

    def fullCheck(self, model=None):
        if not model:
            model = self.model
        if not self.checkModel():
            self.pullModel(model)

    def checkModel(self, model=None):
        if model is None:
            model = self.model
        try:
            ollama.show(model)
            return True
        except:
            return False

    def pullModel(self, model=None):
        if model is None:
            model = self.model

        print(f"Downloading Ollama model {model} (This might take minutes)...", end="\n")
        threading.Thread(target=self.tuiUtils.loadingIcon).start()
        try:
            pulling = ollama.pull(model=model, stream=True)
            for chunk in pulling:
                status = chunk.get("status", f"Pulling model: {model}")
                print(f"\033[3G{status}", flush=True, end='\r')
            self.tuiUtils.stop = True
            print(f"Model:{model} has been successfully pulled.")
            return True
        except Exception as e:
            self.tuiUtils.stop = True
            print(f"Failed to pull model {model}: {e}")
            return False

    def removeModel(self, model:str=None):
        if model is None:
            model = self.model

        if self.checkModel(model):
            try:
                ollama.delete(model)
                print(f"Model {model} has been successfully removed")
                return True
            except Exception as e:
                print(f"Failed to remove model {model}: {e}")
                return False
        else:
            print(f"Model {model} does not exist (Not deleted)")
            return False