import time

class TUI:
    def __init__(self, loadingSpeed=0.1):
        self.loadingSpeed = loadingSpeed
        self.stop = False
    def loadingIcon(self):
        icons = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        while True:
            if self.stop: break            
            try:
                for icon in icons:
                    if self.stop: break
                    print(icon, end="\r", flush=True)
                    time.sleep(self.loadingSpeed)
            except (KeyboardInterrupt, EOFError):
                self.stop = True
                break
