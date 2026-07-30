import subprocess
import platform
import json
import shutil
from pathlib import Path
from lib.puller import Puller
import importlib

class setup:
    def __init__(self):
        self.OS = "macOS" if platform.system() == "Darwin" else platform.system()
        self.externPackages = ["xclip", "ollama"]
        self.providers = None
        self.packageManagers = {
            "apt": {
                "install":"install",
                "update":"update",
                "assumeYes":[
                    "after",
                    "-y"
                ]
            },
            "pacman": {
                "install":"-S",
                "update":"-Sy",
                "assumeYes":[
                    "after",
                    "--noconfirm"
                ]
            },
            "dnf": {
                    "install":"install",
                "update":"makecache",
                "assumeYes":[
                    "after",
                    "-y"
                ]
            },
            "zypper": {
                "install":"in",
                "update":"refresh",
                "assumeYes":[
                    "before",
                    "--non-interactive"
                ]
            },
            "apk": {
                "install":"add",
                "update":"update",
                "assumeYes": None
            }
        }

        self.pacMan = None
        self.updateCommand = None
        
        if self.checkDistro():
            self.update()
            self.install(self.externPackages)

        if not self.installPip():
            print("Failed to install pip packages. Please install them manually.")
        else:
            self.questionary = importlib.import_module("questionary")
        
        self.gatherProviders()

    def checkDistro(self):
        if self.OS == "Linux":
            for manager in self.packageManagers:
                if bool(shutil.which(manager)):
                    self.pacMan = manager
                    break
        else:
            return False
        if shutil.which("sudo"):
            subprocess.run(["sudo", "-v"])
        if self.packageManagers[self.pacMan].get("assumeYes", None) is not None:
            position = self.packageManagers[self.pacMan].get("assumeYes", None)[0]
            if position == "before":
                updateCommand = ["sudo" if shutil.which("sudo") else "", self.pacMan, self.packageManagers[self.pacMan].get("assumeYes")[1], self.packageManagers[self.pacMan]["update"]]
                installCommand = ["sudo" if shutil.which("sudo") else "", self.pacMan, self.packageManagers[self.pacMan].get("assumeYes")[1], self.packageManagers[self.pacMan]["install"]]
            elif position == "after":
                updateCommand = ["sudo" if shutil.which("sudo") else "", self.pacMan, self.packageManagers[self.pacMan]["update"], self.packageManagers[self.pacMan].get("assumeYes")[1]]
                installCommand = ["sudo" if shutil.which("sudo") else "", self.pacMan, self.packageManagers[self.pacMan]["install"], self.packageManagers[self.pacMan].get("assumeYes")[1]]
        else:
            updateCommand = ["sudo" if shutil.which("sudo") else "", self.pacMan, self.packageManagers[self.pacMan]["update"]]
            installCommand = ["sudo" if shutil.which("sudo") else "", self.pacMan, self.packageManagers[self.pacMan]["install"]]
        
        self.updateCommand = [item for item in updateCommand if item.strip() != ""]
        self.installCommand = [item for item in installCommand if item.strip() != ""]
        return True
    
    def update(self):
        print(self.updateCommand)
        try:
            subprocess.run(self.updateCommand, check=True)
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to update repositories. Please update manually.")
            return False
    
    def install(self, packages:list[str]):
        try:
            self.installCommand.extend(self.externPackages)
            subprocess.run(self.installCommand, check=True)
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to install packages with {self.pacMan}: {" ".join(self.externPackages)}")
            return False

    def installPip(self, requirementsFile="requirements.txt"):
        if not Path(requirementsFile).exists():
            fileUrl = "https://raw.githubusercontent.com/milo0622/Piston-AI/main/requirements.txt"
            Puller(url=fileUrl, outputPath="requirements.txt").pull()
        
        try:
            pipInstall = ["pip3" if shutil.which("pip3") else "pip", "install", "-r", requirementsFile, "--break-system-packages"]
            print(pipInstall)
            subprocess.run(pipInstall, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
        
    def gatherProviders(self):
        if not Path("providers/providers.json").exists():
            url = "https://raw.githubusercontent.com/milo0622/Piston-AI/main/providers/providers.json"
            Puller(url, "providers/providers.json").pull()
        with open("providers/providers.json", "r") as f:
            self.providers = json.load(f)
    
    def config(self):
        providerQ = [provider for provider in self.providers]
        providerAns = self.questionary.select(
            "Which provider would you like to utilize? (Select Ollama if no preference)",
            choices=providerQ
        ).ask()
        print(providerAns)

        if providerAns == "ollama":
            modelAns = self.questionary.text("Select a model (Leave blank if no preference): ").ask()
            if not modelAns.strip():
                modelAns = "gemma4:e4b"
        else:
            apiQ = ["I have an API key", "Not suitable"]
            apiSelAns = self.questionary.select("Does this provider need an API key?", choices=apiQ).ask()
            if apiSelAns == apiQ[0]:
                apiAns = None
                while apiAns is None:
                    apiAns = self.questionary.text("Enter API key: ").ask()
                    if not apiAns:
                        print("Please enter API key.")
            modelAns = None
            while modelAns is None:
                modelAns = self.questionary.text("Select a model (necessary): ").ask()
                if modelAns is None:
                    print("Please enter model ID.")

        payload = {
            "provider":providerAns,
            "model": modelAns
        }
        
        if not Path("userdata").exists():
            Path("userdata").mkdir(parents=True, exist_ok=True)
        with open("userdata/config.json", "w") as f:
            json.dump(payload, f, indent=4)
        if apiAns:
            if Path(".env").exists():
                with open(".env", "r") as f:
                    lines = f.readlines()
            else:
                lines = []
            lines = [line for line in lines if not line.lower().startswith(providerAns) and not line.startswith("#")]
            lines.insert("# This file was automatically generated")
            lines.append(f"{providerAns.upper()}=\"{apiAns}\"")
            print("\nConfigurations:")
            for key in payload:
                print(f"{key}: {payload[key]}")
            with open(".env", "w") as f:
                f.write("\n".join(lines))

if __name__ == "__main__":
    s = setup()
    s.config()