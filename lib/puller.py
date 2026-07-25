import requests
import threading
from lib import tui
from pathlib import Path
import os

class Puller:
    def __init__(self, url:str, outputPath:str):
        self.url = url
        self.out = outputPath
        self.tui = tui.TUI()

    def pull(self):
        try:
            Path(os.path.dirname(self.out)).mkdir(exist_ok=True, parents=True)
            threading.Thread(target=self.tui.loadingIcon).start()
            print(f"\033[3GDownloading file from {self.url}, output path: {self.out}")
            with requests.get(self.url, stream=True) as response:
                response.raise_for_status()
                with open(self.output, "wb") as f:
                    for chunk in response.iter_content(chunk_size=4096):
                        if chunk:
                            f.write(chunk)
        except (KeyboardInterrupt, EOFError):
            self.tui.stop = True
            print(f"Operation aborted.")
        except Exception as e:
            self.tui.stop = True
            print(f"Error pulling file from {self.url}: {e}")
