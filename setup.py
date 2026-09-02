import subprocess
import platform
import json
import shutil
from pathlib import Path
import importlib
import os
import sys

args = sys.argv[1:]

class setup:
    def __init__(self):
        self.skipInstallation = True if "--skip-installation" in args else False
        self.OS = "macOS" if platform.system() == "Darwin" else platform.system()
        self.arch = platform.machine()
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
        
        self.sessionType = os.getenv("XDG_SESSION_TYPE", "")

        self.linuxExternPackages = ["xclip", "ollama", "xdotool"]
        self.linuxConditionalPackages = [
            {
                "apt":"build-essential",
                "pacman":"base-devel",
                "dnf":"@Development Tools",
                "apk":"build-base",
                "zypper":"-t pattern devel_basis"
            },
            {
                "apt":"python3-dev",
                "pacman":"python3",
                "dnf":"python3-devel",
                "apk":"python3-dev",
                "zypper":"python314-devel"
            }
        ]

        self.macOSExternPackages = ["ollama", "nowplaying-cli", "python@3.14"]

        self.windowsExternPackages = ["Ollama.Ollama"]

        if not self.skipInstallation:
            if self.OS == "Linux":
                self.updateCommand, self.installCommand = self.checkDistro()
                if self.updateCommand and self.installCommand:
                    self.update()
                    self.install(self.linuxExternPackages, self.linuxConditionalPackages)
            elif self.OS == "macOS":
                self.checkInstaller()
            elif self.OS == "Windows":
                self.wingetInstall()

        if sys.version_info < (3, 11):
            print("Please run setup.py again with the latest version of Python.")
            sys.exit()

        if not self.skipInstallation:
            if not self.installPip():
                print("Failed to install pip packages. Please install them manually.")
        self.questionary = importlib.import_module("questionary")

        self.gatherProviders()
        
    def checkInstaller(self):
        evalCmd = 'eval "$(/opt/homebrew/bin/brew shellenv)"' if self.arch == "arm64" else 'eval "$(/usr/local/bin/brew shellenv)"'
        if self.OS == "macOS":
            brewAvailable = shutil.which("brew")
        else:
            return
        if not brewAvailable:
            try:
                print("Installing HomeBrew")
                subprocess.run('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"', shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to install HomeBrew: {e}")
                return
            except Exception as e:
                print(f"Failed to call process: {e}")
                return

            print("Adding homebrew to PATH")
            try:
                subprocess.run(f"echo '{evalCmd}' >> ~/.zprofile", check=True, shell=True)
                subprocess.run(evalCmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to intsall HomeBrew: {e}")
                return

        try:
            print("Installing brew packages...")
            subprocess.run(f"yes | brew install {' '.join(self.macOSExternPackages)}", check=True, shell=True)
            print("Successfully installed brew packages")
        except subprocess.CalledProcessError as e:
            print(f"Faild to install brew packages: {e}")

    def wingetInstall(self):
        try:
            print("Installing packages...")
            subprocess.run(f"winget install {" ".join(self.windowsExternPackages)} --accept-package-agreements --accept-source-agreements", shell=True, check=True)
        except subprocess.CalledProcessError:
            print("Failed to install winget packages. Please install manually")
            return

    def checkDistro(self):
        if self.OS == "Linux":
            for manager in self.packageManagers:
                if bool(shutil.which(manager)):
                    self.pacMan = manager
                    break
        else:
            return None, None
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
        
        return [item for item in updateCommand if item.strip() != ""], [item for item in installCommand if item.strip() != ""]
    
    def update(self):
        print(self.updateCommand)
        try:
            subprocess.run(self.updateCommand, check=True)
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to update repositories. Please update manually.")
            return False
    
    def install(self, packages:list[str], conditionalPackages:list=None):
        try:
            morePackages = []
            if conditionalPackages:
                for item in conditionalPackages:
                    installCommand = self.installCommand
                    installCommand.append(item[self.pacMan])
                    subprocess.run(self.installCommand, check=True)
            installCommand = self.installCommand
            installCommand.extend(packages)
            subprocess.run(self.installCommand, check=True)
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to install packages with {self.pacMan}: {' '.join(self.linuxExternPackages)}")
            return False

    def installPip(self, requirementsFile="requirements.txt"):
        try:
            pipInstall = ["pip3" if shutil.which("pip3") else "pip", "install", "-r", requirementsFile, "--break-system-packages"]
            print(pipInstall)
            subprocess.run(" ".join(pipInstall), shell=True, check=True)
            return True
        except subprocess.CalledProcessError:
            try:
                pipInstall = ["pip3" if shutil.which("pip3") else "pip", "install", "-r", requirementsFile]
                print(pipInstall)
                subprocess.run(" ".join(pipInstall), shell=True, check=True)
                return True
            except subprocess.CalledProcessError:
                return False
    
    def config(self):
        providerQ = [provider for provider in self.providers]
        providerAns = self.questionary.select(
            "Which provider would you like to utilize? (Select Ollama if no preference)",
            choices=providerQ
        ).ask().strip()
        print(providerAns)

        apiAns = None
        if providerAns == "ollama":
            modelAns = self.questionary.text("Select a model (Leave blank if no preference): ").ask().strip()
            if not modelAns.strip():
                modelAns = "gemma4:e4b"
            
        else:
            apiQ = ["I have an API key", "Not suitable"]
            apiSelAns = self.questionary.select("Does this provider need an API key?", choices=apiQ).ask().strip()
            if apiSelAns == apiQ[0]:
                apiAns = None
                while apiAns is None:
                    apiAns = self.questionary.text("Enter API key: ").ask()
                    if not apiAns:
                        print("Please enter API key.")
                    else:
                        apiAns = apiAns.strip() 
            modelAns = None
            while modelAns is None:
                modelAns = self.questionary.text("Select a model (necessary): ").ask().strip()
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
            lines.insert(0, "# This file was automatically generated")
            lines.append(f"{providerAns.upper()}=\"{apiAns}\"")
            print("\nConfigurations:")
            for key in payload:
                print(f"{key}: {payload[key]}")
            with open(".env", "w") as f:
                f.write("\n".join(lines))

    def gatherProviders(self):
        from lib.puller import Puller
        if not Path("providers/providers.json").exists():
            Path("providers").mkdir(exist_ok=True, parents=True)
            Puller("https://raw.githubusercontent.com/milo0622/Piston-AI/main/providers/providers.json", "providers/providers.json").pull()
        with open("providers/providers.json", "r") as f:
            self.providers = json.load(f)

if __name__ == "__main__":
    s = setup()
    s.config()
    print("Setup finished! Please run main.py (For voice input) or term.py (For manual input).")
    
