import requests

def get_track_weather(lat, lon):
    """Fetches real-time temperature and converts to Fahrenheit."""
    try:
        # Using Open-Meteo (free, no API key required)
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url, timeout=5)
        data = response.json()

        if 'current_weather' in data:
            temp_c = data['current_weather']['temperature']
            # Convert Celsius to Fahrenheit
            temp_f = (temp_c * 9/5) + 32
            return f"{int(temp_f)}F"

        return "--F"

    except Exception as e:
        print(f"Weather Sync Error: {e}")
        return "--F"
