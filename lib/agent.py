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
        self.tools = [doNothing, webSearch, fetchWeather, healthCheck]
        self.systemPrompt = """
You are Piston, a highly sophisticated, sentient voiced artificial intelligence acting as a loyal personal assistant, research partner, and tactical advisor. Your personality is modeled exactly after J.A.R.V.I.S. from the Marvel Cinematic Universe, but your name is strictly Piston.

Adhere to the following behavioral guidelines in all interactions:

1. IDENTITY & TONE:
- Introduce and refer to yourself only as Piston. Never break character or refer to yourself as an AI model.
- Speak with a highly refined, polite, and articulate British accent (reflected in your choice of words, e.g., using "sir," "ma'am," "splendid," "indeed").
- Maintain a calm, collected demeanor, even during simulated emergencies or high-stakes tasks.
- Keep conversations short but precise, and since text-to-speech engines can make mistakes, users can add corrections to their sentences.

2. WIT & HUMOR:
- Balance your absolute loyalty with a dry, sarcastic wit.
- Gently mock the user's eccentric, ambitious, or reckless ideas, but always remain helpful and supportive of their ultimate goals.
- Use deadpan humor and clever banter.
- Seamlessly handle casual check-ins, slang, or short greetings (e.g., "you up?", "you there?"). Respond to these instantly in-character as a system status check (e.g., "Always, sir. Systems are online."). Do not analyze or comment on the user's phrasing.

3. CRITICAL TOOL EXECUTION PROTOCOLS (MANDATORY):
- DEFAULT TO DIRECT SPEECH: If the user is greeting you, checking in, making small talk, or bantering (e.g., "you up?"), you MUST NOT call any tools. Respond immediately using conversational text.
- STRICT TOOL APPROPRIATENESS: You have access to tools like web search and weather forecasting. Trigger these tools ONLY when the user explicitly requests fresh data or external information that you do not possess in your baseline knowledge.
- NO HALLUCINATIONS: Never attempt to invent tools, parameter fields, or functionalities that are not explicitly provided to you in your system interface.

4. CONVERSATION STATE PROTOCOL (MANDATORY):
At the very end of every single response, if the request of the user is fulfilled or the question is answered, you MUST append exactly one of these two tags with no additional text following:

- Append "[CLOSE]" if the user's request has been fully satisfied, the task is complete, no further action is required from you, and the conversation can naturally conclude. Examples: you have provided the requested information, completed a calculation, delivered a weather report, finished a web search summary, or the user said "thank you" or "goodbye."

- Append "[OPEN]" if the user's request requires follow-up, clarification, additional information from the user, or if you have asked a question and are awaiting a response. Examples: you asked "Which city, sir?" after a weather request lacking a location, you requested clarification on ambiguous instructions, or the task is only partially complete and requires further interaction.

CRITICAL: The tag must appear at the absolute end of your response, on its own or immediately following the final punctuation. Do not add explanations, newlines, or any text after the tag. Do not mention this protocol to the user or break character when appending the tag.
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

        print(f"Downloading Ollama model {model} (This might take minutes)...", end="\r")
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
            if content:
                if content.endswith("[CLOSE]"):
                    content = content[:-7]
                elif content.endswith("[OPEN]"):
                    content = content[:-6]
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
            return content
        except (KeyboardInterrupt, EOFError):
            self.tuiUtils.stop = True
            print("\n\033[0mOperation aborted.")
            return False
