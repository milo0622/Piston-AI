import subprocess
import os
import platform
import shutil
import threading

class persistentShell:
    def __init__(self):
        self.platform = platform.system()
        self.shell = self.shellDetection()
        
    def shellDetection(self) -> list[str]:
        if self.platform == "Windows":
            return [str(os.getenv("COMSPEC", "powershell.exe"))]
        else:
            shell = os.getenv("SHELL", "/bin/zsh" if self.platform == "Darwin" else "/bin/bash")
            if shutil.which(shell, mode=os.F_OK | os.X_OK, path=None):
                return shell
            else:
                return "/bin/sh"
    
    def setupShell(self):
            pass
    
    def execute(self, command:str="", parallel:bool=False):
        if not command or not isinstance(command, str):
            return "Failed to run command: No command provided"
        
        
        