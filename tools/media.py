import platform
import subprocess
import ctypes

class MediaControl:
    def __init__(self):
        self.OS = platform.system() if platform.system() in ("Linux", "Windows") else "macOS"

    
    