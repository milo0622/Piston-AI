if __name__ == "__main__":
    import tui
else:
    from lib import tui
from pathlib import Path
import sounddevice as sd
import soundfile as sf
import os
import threading
import requests
from piper import PiperVoice, SynthesisConfig
import asyncio

class TTS:
    def __init__(self, voiceDir="voices/"):
        self.voiceDir = voiceDir
        self.model = f"{voiceDir}/jarvis.onnx"
        self.config = f"{voiceDir}/jarvis.onnx.json"
        self.tui = tui.TUI()

        self.voice = None
        self.checkModels()
        self.loadModel()

    def checkModels(self):
        Path(os.path.dirname(self.voiceDir)).mkdir(exist_ok=True, parents=True)
        if not Path(self.model).exists():
            try:
                Path(self.model).unlink(missing_ok=True)
                print("\033[3GPulling TTS model...", end="\r")
                threading.Thread(target=self.tui.loadingIcon).start()
                url = "https://raw.githubusercontent.com/cklam12345/jarvis_llama/main/jarvis.onnx"
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    with open(self.model, "wb") as f:
                        for chunk in response.iter_content(chunk_size=4096):
                            if chunk:
                                f.write(chunk)
                print("√")
            except (KeyboardInterrupt, EOFError):
                self.tui.stop = True
                print("Operation aborted.")
            except Exception as e:
                self.tui.stop = True
                print(f"An error occurred: {e}")

        if not Path(self.config).exists():
            try:
                Path(self.voice).unlink(missing_ok=True)
                print("\033[3GPulling TTS config...")
                threading.Thread(target=self.tui.loadingIcon).start()
                url = "https://raw.githubusercontent.com/cklam12345/jarvis_llama/main/jarvis.onnx.json"
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    with open(self.config, "wb") as f:
                        for chunk in response.iter_content(chunk_size=4096):
                            if chunk:
                                f.write(chunk)
                print("√")
            except (KeyboardInterrupt, EOFError):
                self.tui.stop = True
                print("Operation aborted.")
            except Exception as e:
                self.tui.stop = True
                print(f"An error occurred: {e}")

    def loadModel(self, path="voices/jarvis.onnx"):
        print("\033[3GLoading TTS model...", end="\r")
        threading.Thread(target=self.tui.loadingIcon).start()
        self.voice = PiperVoice.load(path)
        self.tui.stop = True
        print("\r√")

    async def speak(self, text:str) -> None:
        if self.model is None:
            print("Please load model first.")
        try:
            if not text.strip():
                return
            SynConfig = SynthesisConfig(
                volume=1.0,
                length_scale=0.8
            )
            sampleRate = self.voice.config.sample_rate

            with sd.RawOutputStream(samplerate=sampleRate, channels=1, dtype="int16") as stream:
                stream.start()

                for chunk in self.voice.synthesize(text, syn_config=SynConfig):
                    stream.write(chunk.audio_int16_array)

                stream.stop()
        except Exception as e:
            print(f"Failed to synthsize: {e}")

if __name__ == "__main__":
    tts = TTS()
    asyncio.run(tts.speak("Hi! I'm Piston AI. You're personal helper friend!"))
