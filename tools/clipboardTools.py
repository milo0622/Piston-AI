import pyperclip
import json

class ClipboardTools:
    def __init__(self):
        self.clipboardContent = None

    def writeText(self, text:str):
        try:
            pyperclip.copy(text)
            print(f"Copied successfully")
            return {"status":"Success"}
        except Exception as e:
            print(f"Failed to copy text")
            return {"status":f"Failed to copy text {e}"}

    def readText(self):
        try:
            self.clipboardContent = pyperclip.paste()
            return {"status":"Success", "content":self.clipboardContent}
        except Exception as e:
            print(f"Failed to read text from clipboard {e}")
            return {"status":f"Failed to read text from clipboard: {e}"}

clipTools = ClipboardTools()
def readTextFromClipboard():
    payload = clipTools.readText()
    return json.dumps(payload)

def writeTextToClipboard(text:str):
    payload = clipTools.writeText(text)
    return json.dumps(payload)
