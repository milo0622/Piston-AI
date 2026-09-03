import webbrowser
import json
from tools.media import *
from ytmusicapi import YTMusic

class YouTubeTools:
    def __init__(self, searchParams:str):
        self.searchParams = searchParams
        self.yt = YTMusic()

    def extractInfo(self):
        print(f"Searching song '{self.searchParams}'")
        results = self.yt.search(self.searchParams)

        for song in results:
            if song.get("resultType", None) == "song":
                return song
        return results[0]
    def main(self):
        song = self.extractInfo()
        if song.get("title", "") and song.get("videoId", ""):
            vidId = song.get("videoId", "")
            url = f"https://music.youtube.com/watch?v={vidId}"
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
            "status":f"Failed to play {self.searchParams}"
        }

def playSong(query:str):
    """Searches and plays song in YouTube Music"""
    yt = YouTubeTools(query)
    result = yt.main()
    return json.dumps(result)

