import subprocess
from pathlib import Path
import os

class systemCalls:
    def __init__(self, shell:bool=False, sudo:bool=False):
        pass

    def listFiles(self, folder:str="."):
        if not Path(folder).exists():
            message = f"Folder: {folder}: No such file"
            print(message)
            return message
        if not Path(folder).is_dir():
            message = f"{folder}: Not a directory"
            print(message)
            return message
        
        ls = os.listdir()
        
        directories = [f for f in ls if Path(f).is_dir()]
        files = [f for f in ls if Path(f).is_file()]
        
        for idx, directory in enumerate(directories):
            directories[idx] = f"{directory.rstrip("/")}/"
        
        result = []
        result.extend(directories)
        result.extend(files)
        
        for file in result:
            print(file, end="    ")
        print()
        
        return result
    
def listFiles():
    s = systemCalls()
    s.listFiles()
    