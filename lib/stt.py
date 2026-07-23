import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import sys
import queue
import threading
if __name__ == "__main__":
    import tui
else:
    from lib import tui

class STT:
    def __init__(self):
        self.SAMPLE_RATE = 16000
        self.CHUNK_DURATION = 1
        self.CHUNK_SIZE = int(self.SAMPLE_RATE * self.CHUNK_DURATION)

        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.text_output = ""

        self.stop = False

        self.tui = tui.TUI()

        threading.Thread(target=self.tui.loadingIcon).start()
        print("\033[3GLoading model...", end="\r")
        self.model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        print("\033[2K√ Model loaded.")
        self.tui.stop = True

    def audioWorker(self):
        try:
            with sd.InputStream(samplerate=self.SAMPLE_RATE, channels=1, dtype="float32") as stream:
                while not self.stop:
                    audio_chunk, _ = stream.read(self.CHUNK_SIZE)
                    if self.stop:
                        break
                    flat_chunk = np.squeeze(audio_chunk)
                    self.audio_queue.put(flat_chunk)
        except Exception as e:
            if not self.stop:
                print(f"\nAn error occurred: {e}")
                self.stop = True

    def main(self, MAX_SILENCE_CHUNKS:int=5):
        self.text_output = ""
        self.stop = False

        model = self.model
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                silence_count = 0
                break

        silence_count = 0
        
        audio_buffer = []

        recorder_thread = threading.Thread(target=self.audioWorker, daemon=True)
        recorder_thread.start()

        print("--> Start speaking, Ctrl-C to stop")

        try:
            while not self.stop:
                try:
                    flat_chunk = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                rms = np.sqrt(np.mean(flat_chunk**2))

                if rms < 0.007:
                    silence_count += 1
                    if silence_count > MAX_SILENCE_CHUNKS:
                        if text_output.rstrip():
                            print("\n\nSilence detected. Ending STT")
                            break
                        silence_count -= 1
                else:
                    silence_count = 0

                audio_buffer.append(flat_chunk)
                full_audio_data = np.concatenate(audio_buffer)

                segments, _ = model.transcribe(full_audio_data, beam_size=2, initial_prompt="Piston")
                text_output = "".join([segment.text for segment in segments])

                sys.stdout.write(f"\r\033[2K{text_output}")
                sys.stdout.flush()
        except KeyboardInterrupt:
            print("\nSTT ended")
            exitType = "manual"
        self.stop = True
        recorder_thread.join(timeout=1.0)
        if silence_count <= 0:
            exitType = "timeout"
        else:
            exitType = "normal"
        return text_output, exitType

if __name__ == "__main__":
    stt = STT()
    text, _ = stt.main()