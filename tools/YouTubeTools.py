import webbrowser
import json
from yt_dlp import YoutubeDL
from tools.media import *

class YouTubeTools:
    def __init__(self, searchParams:str):
        self.ytdlpOpts = {
            "extract_flat":True,
            "skip_download":True,
            "quiet":True
        }
        if searchParams.startswith("https://") and searchParams.startswith("http://"):
            self.query = searchParams
        else:
            self.query = f"ytsearch:{searchParams}"

    def extractInfo(self):
        print(f"Searching song '{self.query}'")
        with YoutubeDL(self.ytdlpOpts) as ydl:
            try:
                result = ydl.extract_info(self.query, download=False)
                if "entries" in result and result.get("entries", None):
                    videoData = result["entries"][0]

                    return {
                        "title":videoData.get("title", ""),
                        "streamURL": videoData.get("url", ""),
                        "status":"Success"
                    }
            except Exception as e:
                print(f"Failed to extract info: {e}")
                return {
                    "status":f"Failed to extract info: {e}"
                }

    def main(self):
        song = self.extractInfo()
        if song.get("title", "") and song.get("streamURL", ""):
            url = song.get("streamURL", "")
            url = url.replace("www.youtube.com", "music.youtube.com")
            if not "music.youtube.com" in url:
                url = url.replace("youtube.com", "music.youtube.com")
            print(url)
            result = json.loads(fetchCurrentPlaying())
            print(result)
            if result.get("playing", False):
                pauseMedia()
            webbrowser.open(url)
            return {
                "status":f"Playing {song.get("title", "")}"
            }
        return {
            "status":f"Failed to play {self.query}"
        }

def playSong(query:str):
    """Searches and plays song in YouTube Music"""
    yt = YouTubeTools(query)
    result = yt.main()
    return json.dumps(result)
