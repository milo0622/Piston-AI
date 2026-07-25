from litellm import completion
from pathlib import Path
import json
from lib import tui
import threading
from tools.fetchWeather import *
from tools.websearch import *
from tools.systemChecks import *
from lib import tts
import asyncio
import os
from pathlib import Path
import copy
import importlib
import asyncio
import inspect
from lib.puller import *

class Agent:
    def __init__(self, providers:str="providers/providers.json", model="llama3.1:8b", chatHistoryPath="userdata/chats/fallback.json", toolPath="tools/tools.json"):
        self.defProviders = {
            "ollama":{
                "api":"ollama",
                "baseURLENV":"OLLAMA_HOST",
                "fallback":"http://localhost:11434",
                "endpoint":"/v1"
            },
            "lmstudio":{
                "api":"lmstudio",
                "baseURLENV":"LMSTUDIO_BASE_URL",
                "fallback":"http://localhost:1234",
                "endpoint":"/v1"
            }
        }
        self.providersPath = providers
        self.providers = None
        self.provider = "ollama"
        self.providerConfig = {}
        self.loadedProvider = None
        self.model = model

        self.chatHistoryPath = chatHistoryPath
        self.tui = tui.TUI()
        self.toolPath = toolPath
        self.tools = []
        self.tts = tts.TTS()

        self.systemPrompt = None

        self.checkProviders()
        self.fetchTools()
        self.fetchSystemPrompt()

    def checkProviders(self):
        url = "https://raw.githubusercontent.com/milo0622/Piston-AI/main/providers/providers.json"
        output = "providers/providers.json"
        Path(os.path.dirname(Path(self.providersPath).resolve())).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(Path("userdata/config.json").resolve())).mkdir(parents=True, exist_ok=True)
        if not Path(self.providersPath).exists():
            Puller(url=url, outputPath=output).pull()
            with open(output, "r") as f:
                self.providers = json.load(f)
        else:
            with open(self.providersPath, "r") as f:
                try:
                    self.providers = json.load(f)
                except json.JSONDecodeError:
                    Puller(url=url, outputPath=output).pull()
                    with open(output, "r") as f:
                        self.providers = json.load(f)
        defaultConfig = {
            "provider":"ollama"
        }
        if not Path("userdata/config.json").exists():
            with open("userdata/config.json", "w") as f:
                json.dump(defaultConfig, f, indent=4)
                self.provider = "ollama"
        else:
            try:
                with open("userdata/config.json", "r") as f:
                    self.provider = json.load(f).get("provider", "ollama")
            except (json.JSONDecodeError, FileNotFoundError, AttributeError):
                with open("userdata/config.json", "w") as f:
                    json.dump(defaultConfig, f, indent=4)
                self.provider = "ollama"
        self.providerConfig = self.providers.get(self.provider, "ollama")
        self.loadedProvider = importlib.import_module(f"providers.{self.provider}")

        self.envVarName = self.providerConfig.get("baseURLENV", "OLLAMA_HOST")
        fallback = self.providerConfig.get("fallback", "http://127.0.0.1:11434")
        self.baseURL = os.getenv(self.envVarName, fallback)
        self.endpoint = self.providerConfig.get("endpoint", "/v1")
        self.api = self.providerConfig.get("api", "ollama").strip() 

        className = f"{self.provider[0].upper()}{self.provider[1:]}"
        providerClass = getattr(self.loadedProvider, className)
        providerClass(model=self.model)

    def verifyHistoryPath(self):
        if not self.chatHistoryPath.strip():
            self.chatHistoryPath = "userdata/chats/fallback.json"
        

    def writeHistory(self, messages:list[dict]):
        for message in messages:
            if message.get("role", "") == "system":
                messages.remove(message)
                break
            else: continue
        with open(self.chatHistoryPath, "w") as f:
            json.dump(messages, f, indent=4)

    def readHistory(self):
        try:
            with open(self.chatHistoryPath, "r") as f:
                messages = json.load(f)
                return messages
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self.chatHistoryPath, "w") as f:
                f.write("[]")
            return []

    def fetchTools(self):
        url = "https://raw.githubusercontent.com/milo0622/Piston-AI/main/tools/tools.json"
        outputPath = "tools/tools.json"
        Path(Path(os.path.dirname(self.toolPath)).resolve()).mkdir(parents=True, exist_ok=True)

        try:
            if not Path(self.toolPath).exists():
                Puller(url=url, outputPath=outputPath).pull()
            with open(self.toolPath, "r") as f:
                self.tools:list[dict] = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            with open(self.toolPath, "w") as f:
                json.dump([], f, indent=4)
            print(f"Failed to read tools: {e}")
            self.tools = []

    def fetchSystemPrompt(self):
        sysPromptPath = "lib/systemPrompt.txt"
        url = "https://raw.githubusercontent.com/milo0622/Piston-AI/main/lib/systemPrompt.txt"
        Path(os.path.dirname(sysPromptPath)).mkdir(parents=True, exist_ok=True)

        try:
            if not Path(sysPromptPath).exists():
                Puller(url, outputPath=sysPromptPath).pull()
            with open(sysPromptPath, "r") as f:
                self.systemPrompt = f.read()
        except Exception as e:
            print("Failed to obtain system prompt: {e}")
            self.systemPrompt = """"""

    def ask(self, message):
        try:
            open = None
            self.fetchSystemPrompt()
            messages = self.readHistory()
            messages.insert(0, {
                "role":"system",
                "content":self.systemPrompt
            })
            messages.append({
                "role":"user",
                "content":message
            })
            threading.Thread(target=self.tui.loadingIcon).start()
            stream = completion(model=f"openai/{self.model}", stream=True, base_url=f"{self.baseURL}{self.endpoint}", api_key=self.api, messages=messages, tools=self.tools, tool_choice="auto")
            content = ""
            toolCalls = []
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    self.tui.stop = True
                    print(chunk.choices[0].delta.content, end="")
                    content += chunk.choices[0].delta.content
                
                if chunk.choices[0].delta.tool_calls:
                    self.tui.stop = True
                    toolCalls.append(chunk.choices[0].delta.tool_calls[0])
            if content:
                if content.lower().endswith("[open]"):
                    content = content[:-6]
                    open = True
                elif content.lower().endswith("[close]"):
                    content = content[:-7]
                    open = False
                asyncio.run(self.tts.speak(content))
            payload = {
                "role":"assistant",
                "content": None if not content else content,
                "tool_calls":[] if toolCalls else None
            }
            messages.append(payload)
            if toolCalls:
                toolCallResults = []
                for call in toolCalls:
                    messages[-1]["tool_calls"].append({
                        "id":call.id,
                        "type":call.type,
                        "function":{
                            "name":call.function.name,
                            "arguments": call.function.arguments
                        }
                    })
                    execution = globals().get(call.function.name, None)
                    if not execution:
                        continue
                    availableParameters = inspect.signature(execution).parameters.values()
                    argumentCalls = json.loads(call.function.arguments)
                    if len(availableParameters) > 0:
                        result = execution(**argumentCalls)
                    else:
                        result = execution()
                    toolCallResults.append({
                        "role":"tool",
                        "tool_call_id":call.id,
                        "content":json.dumps(result) if isinstance(result, (dict, list)) else result
                    })
                messages.extend(toolCallResults)
                threading.Thread(target=self.tui.loadingIcon).start()
                stream = completion(model=f"openai/{self.model}", stream=True, base_url=f"{self.baseURL}{self.endpoint}", api_key=self.api, messages=messages, tools=self.tools, tool_choice="auto")
                content = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        self.tui.stop = True
                        print(chunk.choices[0].delta.content, end="")
                        content += chunk.choices[0].delta.content
                if content:
                    if content.lower().endswith("[open]"):
                        content = content[:-6]
                        open = True
                    elif content.lower().endswith("[close]"):
                        content = content[:-7]
                        open = False
                    asyncio.run(self.tts.speak(content))
                    messages.append({
                        "role":"assistant",
                        "content":content
                    })
            self.writeHistory(messages=messages)
            return open
        except Exception as e:
            self.tui.stop = True
            if e in (KeyboardInterrupt, EOFError):
                print("Operation aborted")
            else:
                print(f"Failed to ask agent: {e}")

if __name__ == "__main__":
    agent = Agent()
    agent.ask("Fetch me the weather please") 
