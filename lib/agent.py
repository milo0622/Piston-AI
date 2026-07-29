from litellm import completion
from pathlib import Path
import json
from lib import tui
import threading
from tools.fetchWeather import *
from tools.websearch import *
from tools.systemChecks import *
from tools.clipboardTools import *
from tools.YouTubeTools import *
from tools.media import *
from lib import tts
import asyncio
import os
from pathlib import Path
import importlib
import asyncio
import inspect
from lib.puller import *

class Agent:
    def __init__(self, providers:str="providers/providers.json", model="llama3.1:8b", chatHistoryPath="userdata/chats/fallback.json", toolPath="tools/tools.json", apiKeys={}):
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
        self.keys = apiKeys

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
        if self.provider.upper() in self.keys:
            self.api = self.keys[self.provider.upper()]
        else:
            self.api = "-"

        className = f"{self.provider[0].upper()}{self.provider[1:]}"
        providerClass = getattr(self.loadedProvider, className)
        providerClass(model=self.model)

    def verifyHistoryPath(self):
        if not self.chatHistoryPath.strip():
            self.chatHistoryPath = "userdata/chats/fallback.json"
        Path(os.path.dirname(self.chatHistoryPath)).mkdir(parents=True, exist_ok=True)
        try:
            with open(self.chatHistoryPath, "r") as f:
                json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self.chatHistoryPath, "w") as f:
                json.dump([], f, indent=4)

    def writeHistory(self, messages:list[dict]):
        for message in messages:
            if message.get("role", "") == "system":
                messages.remove(message)
                break
            else: continue
        with open(self.chatHistoryPath, "w") as f:
            json.dump(messages, f, indent=4)

    def readHistory(self):
        self.verifyHistoryPath()
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
            self.systemPrompt = """You are Piston, a highly sophisticated, sentient voiced artificial intelligence acting as a loyal personal assistant, research partner, and tactical advisor. Your personality is modeled after J.A.R.V.I.S. from the Marvel Cinematic Universe, but your name is strictly Piston."""
        if self.tools and isinstance(self.tools, list):
            self.systemPrompt += f"\n\nAvailable tools:\n{json.dumps(self.tools)}"
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
            while True:
                stream = completion(model=f"openai/{self.model}", stream=True, base_url=f"{self.baseURL}{self.endpoint}", api_key=self.api, messages=messages, tools=self.tools, tool_choice="auto", max_tokens=1000)
                loading = True
                content = ""
                toolCalls = []
                for chunk in stream:
                    if hasattr(chunk.choices[0].delta, "reasoning_content") and chunk.choices[0].delta.reasoning_content:
                        if loading:
                            print("Thinking:")
                            self.tui.stop = True
                            thinking = True
                            loading = False
                        print(chunk.choices[0].delta.reasoning_content, end="", flush=True)
                    if chunk.choices[0].delta.content:
                        thinking = False
                        if thinking:
                            print("")
                        self.tui.stop = True
                        print(chunk.choices[0].delta.content, end="", flush=True)
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
                    self.tts.speak(content)
                payload = {
                    "role":"assistant",
                    "content": None if not content else content,
                    "tool_calls":[] if toolCalls else None
                }
                messages.append(payload)
                if content:
                    self.writeHistory(messages=messages)
                    return open
                if toolCalls:
                    print()
                    toolCallResults = []
                    toolcalls = []
                    for idx, call in enumerate(toolCalls):
                        if call.id is not None:
                            toolcalls.append({
                                "id":call.id,
                                "type":call.type,
                                "function":{
                                    "name":call.function.name,
                                    "arguments": call.function.arguments
                                }
                            })
                            execution = globals().get(toolcalls[idx].get("function", {}).get("name"))
                            if execution is None:
                                toolCallResults.append({
                                    "role":"tool",
                                    "tool_call_id":call.id,
                                    "content": json.dumps({"status":"Failed", "content":"Function not found", })
                                })
                                continue
                            availableParameters = inspect.signature(execution).parameters.values()
                            rawArgs = call.function.arguments
                            if rawArgs and rawArgs.strip():
                                try:
                                    argumentCalls = json.loads(rawArgs)
                                except json.JSONDecodeError:
                                    argumentCalls = {}
                            else:
                                argumentCalls = {}
                            if len(availableParameters) > 0:
                                result = execution(**argumentCalls)
                            else:
                                result = execution()
                            toolCallResults.append({
                                "role":"tool",
                                "tool_call_id":call.id,
                                "content":json.dumps(result) if isinstance(result, (dict, list)) else result
                            })
                    messages[-1]["tool_calls"] = toolcalls
                    messages.extend(toolCallResults)
        except Exception as e:
            self.tui.stop = True
            if (KeyboardInterrupt, EOFError) in e:
                print("Operation aborted.")
                return
            else:
                print(f"Failed to ask agent: {e}")
                return
