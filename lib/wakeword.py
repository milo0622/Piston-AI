from lib import tui
import threading
import sounddevice as sd
import numpy as np
from openwakeword.model import Model
from pathlib import Path
import requests
import openwakeword.utils

class Wakeword:
    def __init__(self, wakewordDir="wakewordModels", threshold:float=0.5, sampleRate:int=16000):
        self.sampleRate = sampleRate
        self.threshold = threshold
        self.wakewordDir = wakewordDir
        self.modelDir = f"{self.wakewordDir}/wakeword.onnx"

        self.chunkSize = 1280
        self.tui = tui.TUI()

        self.model = None
        self.modelName = None

        self.modelLoad = self.loadModel()

    def loadModel(self):
        try:
            openwakeword.utils.download_models()
            url = "https://raw.githubusercontent.com/milo0622/Piston-AI/main/wakewordModels/wakeword.onnx"
            Path(self.wakewordDir).mkdir(exist_ok=True, parents=True)
            if not Path(f"{self.wakewordDir}/wakeword.onnx").is_file():
                try:
                    print("\033[3GPulling wakeword model...")
                    threading.Thread(target=self.tui.loadingIcon).start()
                    with requests.get(url, stream=True) as response:
                        response.raise_for_status()
                        with open(self.modelDir, "wb") as f:
                            for chunk in response.iter_content(chunk_size=4096):
                                f.write(chunk)
                    print("√")
                    self.tui.stop = True
                except (KeyboardInterrupt, EOFError):
                    self.tui.stop = True
                    print("\033[2KOperating aborted")
                except Exception as e:
                    self.tui.stop = True
                    print(f"\033[2KFailed to pull model: {e}")

            threading.Thread(target=self.tui.loadingIcon).start()
            print("\033[3GLoading wakeword model...")
            self.model = Model(wakeword_models=[self.modelDir], inference_framework="onnx")
            self.modelName = list(self.model.models.keys())[0]
            self.tui.stop = True
            print("Model successfully loaded.")
            return True
        except (KeyboardInterrupt, EOFError):
            self.tui.stop = True
            print("Operation aborted.")
            return False
        except Exception as e:
            self.tui.stop = True
            print(f"Failed to load wakeword model: {e}")
            return False

    def listenForWake(self) -> bool:
        with sd.InputStream(samplerate=self.sampleRate, channels=1, dtype="int16") as stream:
            while True:
                audioFrame, _ = stream.read(self.chunkSize)
                flatFrame = np.squeeze(audioFrame)

                self.model.predict(flatFrame)

                scores = self.model.prediction_buffer[self.modelName]
                currentScore = scores[-1]

                if currentScore >= self.threshold:
                    print(f"Wakeword triggered, score: {currentScore}")
                    self.model.reset()
                    return True
