import requests
import geocoder

class Weather:
    def __init__(self):
        self.lat, self.lon = self.fetchLocation()
        self.url = "https://api.open-meteo.com/v1/forecast"

    def fetchLocation(self):
        g = geocoder.ip("me")
        if g.latlng:
            return g.latlng
    
    def fetchWeather(self):
        """
        Retrieves the real-time weather
        """
        print("Fetching weather...")
        if self.lat is None or self.lon is None:
            print("Failed to fetch: Please provide latitude and longitude.")
            return "Failed to fetch: Please provide latitude and longitude."
        params = {
            "latitude":self.lat, 
            "longitude":self.lon,
            "current":["temperature_2m", "relative_humidity_2m", "wind_speed_10m"]
        }
        response = requests.get(self.url, params=params)
        if response.status_code == 200:
            data = response.json()
            current_weather = data["current"]
            return current_weather
        else:
            return f"Failed to fetch weather. Error code: {response.status_code}"

def fetchWeather():
    """Retrieves current real-time weather."""
    weather = Weather()
    currentWeather = weather.fetchWeather()
    return currentWeather
