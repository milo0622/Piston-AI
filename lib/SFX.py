import sounddevice as sd
import soundfile as sf
import io

class SFX:
    def __init__(self, *args):
        self.audFiles = []
        for item in args:
            try:
                with open(item, "rb") as f:
                    sound = f.read()
                    self.audFiles.append(sf.read(io.BytesIO(sound)))
            except:
                continue


    def playSound(self, idx=0, blocking:bool=False):
        if len(self.audFiles) > idx+1:
            sd.play(*self.audFiles[idx], blocking=blocking)
