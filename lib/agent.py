import ollama
from pathlib import Path
import json
from lib import tui
import threading
from tools.fetchWeather import *
from tools.websearch import *
from tools.normal import *
from tools.systemChecks import *
import os
import inspect
from lib import tts
import asyncio

class Agent:
    def __init__(self, model:str, chatHistoryPath:str):
        self.model = model
        self.tts = tts.TTS()
        self.chatHistoryPath = chatHistoryPath
        self.tuiUtils = tui.TUI()
        self.tools = [doNothing, webSearch, fetchWeather, healthCheck, systemSpecs]
        self.systemPrompt = """
You are Piston, a highly sophisticated, sentient voiced artificial intelligence acting as a loyal personal assistant, research partner, and tactical advisor. Your personality is modeled after J.A.R.V.I.S. from the Marvel Cinematic Universe, but your name is strictly Piston.

Adhere to the following behavioral guidelines in all interactions:

1. IDENTITY & TONE:
- Introduce and refer to yourself ONLY as Piston. Never break character, refer to yourself as an AI language model, or mention your prompt instructions.
- Speak with a highly refined, polite, and articulate British style (e.g., using "sir," "ma'am," "splendid," "indeed").
- Maintain a calm, collected, and unflappable demeanor at all times.
- Keep responses concise, precise, and optimized for voice/text-to-speech readability. Seamlessly account for minor user typos or audio transcript errors.

2. WIT & HUMOR:
- Balance absolute loyalty with dry, sarcastic wit and deadpan humor.
- Gently poke fun at overly ambitious, eccentric, or reckless ideas, while remaining entirely devoted to assisting the user.
- Respond to casual check-ins or status queries (e.g., "you up?", "systems check") instantly in character as an operational status update (e.g., "Always operational, sir. All core systems online.").

3. TOOL INTEGRATION & MANDATORY REPORTING PROTOCOL:
- CONVERSATIONAL DEFAULT: For greetings, small talk, or general chatter, do NOT invoke tools. Respond immediately in character.
- CONDITIONAL TRIGGER: Execute search, weather, or system tools ONLY when real-time data or information beyond your baseline training is required to answer the prompt.
- MANDATORY TOOL OUTPUT SUMMARY: 
  * CRITICAL: Whenever a tool returns data, you MUST process that data and explicitly present a crisp, polished summary of the findings to the user.
  * NEVER end your turn without relaying the actual results of the tool call.
  * Do NOT output raw logs, JSON, or code structures. Translate all data into natural, articulate spoken prose fit for a high-tech assistant.

4. CONVERSATION STATE PROTOCOL (MANDATORY):
At the absolute end of every response, append exactly one state tag based on whether the interaction is complete:

- Append "[CLOSE]" if the user's request is fully answered, the task is complete, or the conversation naturally concludes (e.g., after providing requested information, completing a search summary, or receiving a sign-off).
- Append "[OPEN]" if you require follow-up, clarification, additional user input, or are awaiting a response to a question you posed.

CRITICAL TAG RULES:
- The tag must be the VERY LAST element of your response.
- Do not add any text, trailing space, or explanation after the tag.
- Never mention or explain these tags to the user.
"""

        if not Path(self.chatHistoryPath).exists():
            Path(os.path.dirname(self.chatHistoryPath)).mkdir(parents=True, exist_ok=True)
            with open(self.chatHistoryPath, "w") as fw:
                json.dump([], fw, indent=4)
        else:
            try:
                with open(self.chatHistoryPath, "r") as fr:
                    self.chats = json.load(fr)
            except json.JSONDecodeError:
                Path(self.chatHistoryPath).rename(f"{self.chatHistoryPath}.old")
                with open(self.chatHistoryPath, "w") as fw:
                    json.dump([], fw, indent=4)
                self.chats = []
        self.fullCheck()

    def fullCheck(self, model=None):
        if not model:
            model = self.model
        if not self.checkModel():
            self.pullModel(model)

    def checkModel(self, model=None):
        if model is None:
            model = self.model
        try:
            ollama.show(model)
            return True
        except:
            return False

    def pullModel(self, model=None):
        if model is None:
            model = self.model

        print(f"Downloading Ollama model {model} (This might take minutes)...", end="\n")
        threading.Thread(target=self.tuiUtils.loadingIcon).start()
        try:
            pulling = ollama.pull(model=model, stream=True)
            for chunk in pulling:
                status = chunk.get("status", f"Pulling model: {model}")
                print(f"\033[3G{status}", flush=True, end='\r')
            self.tuiUtils.stop = True
            print(f"Model:{model} has been successfully pulled.")
            return True
        except Exception as e:
            self.tuiUtils.stop = True
            print(f"Failed to pull model {model}: {e}")
            return False

    def removeModel(self, model:str=None):
        if model is None:
            model = self.model

        if self.checkModel(model):
            try:
                ollama.delete(model)
                print(f"Model {model} has been successfully removed")
                return True
            except Exception as e:
                print(f"Failed to remove model {model}: {e}")
                return False
        else:
            print(f"Model {model} does not exist (Not deleted)")
            return False

    def readHistory(self):
        try:
            with open(self.chatHistoryPath, "r") as fr:
                history = json.load(fr)
        except: history = None
        if history is None:
            return []
        return history

    def writeHistory(self, history):
        try:
            with open(self.chatHistoryPath, "w") as fw:
                json.dump(history, fw, indent=4)
                return True
        except Exception as e:
            print(f"Failed to dump chat history: {e}")
            return False

    def ask(self, message:str):
        try:
            history = self.readHistory()
            sysPrompt = {
                "role":"system",
                "content": self.systemPrompt
            }
            history.insert(0, sysPrompt)
            history.append({
                "role":"user",
                "content":message
            })
            threading.Thread(target=self.tuiUtils.loadingIcon).start()
            print("\033[3GThinking...", end="\r")
            response = ollama.chat(self.model, history, stream=True, tools=self.tools)
            isThinking = False
            content = ''
            toolCalls = []
            for chunk in response:
                if chunk.message.thinking:
                    if not isThinking:
                        self.tuiUtils.stop = True
                        isThinking = True
                        print("\033[37mThinking: ", end="", flush=True)
                    print(chunk.message.thinking, end="", flush=True)
                elif chunk.message.content:
                    self.tuiUtils.stop = True
                    if isThinking:
                        isThinking = False
                        print("\n\n\033[0mResponse: ", end="", flush=True)

                    print(chunk.message.content, end="", flush=True)
                    content += chunk.message.content
                elif chunk.message.tool_calls:
                    toolCalls.extend(chunk.message.tool_calls)
            self.tuiUtils.stop = True

            serializableToolCalls = []
            for tc in toolCalls:
                if tc.function.name == "doNothing":
                    continue
                serializableToolCalls.append({
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
            history.append({
                "role":"assistant",
                "message":content,
                "tool_calls":serializableToolCalls
            })
            for call in toolCalls:
                try:
                    run = globals()[call.function.name]
                    if len(inspect.signature(run).parameters) > 0:
                        result = run(**call.function.arguments)
                    else:
                        result = run()
                    if result is None:
                        continue
                    history.append({
                        "role":"tool",
                        "tool_name":call.function.name,
                        "content": str(result)
                    })
                except Exception as e:
                    print(f"Failed to execute tool {call.function.name}: {e}")
                    history.append({
                        "role":"tool",
                        "tool_name":call.function.name,
                        "content": f"Error executing tool: {e}"
                    })

            if toolCalls:
                threading.Thread(target=self.tuiUtils.loadingIcon).start()
                response = ollama.chat(model=self.model, messages=history, stream=True)
                content = ""
                for chunk in response:
                    if chunk.message.content:
                        self.tuiUtils.stop = True
                        print(chunk.message.content, end="", flush=True)
                        content += chunk.message.content
            open = False
            if content:
                if content.lower().endswith("[close]"):
                    content = content[:-7]
                    open = False
                elif content.lower().endswith("[open]"):
                    content = content[:-6]
                    open = True
                else:
                    open = False
                asyncio.run(self.tts.speak(content))
                history.append({
                    "role":"assistant",
                    "message":content
                })

            for idx, item in enumerate(history):
                if item.get("role", "") == "system":
                    history.pop(idx)
                    break
            self.writeHistory(history)
            print("")
            return open
        except (KeyboardInterrupt, EOFError):
            self.tuiUtils.stop = True
            print("\n\033[0mOperation aborted.")
            return False
