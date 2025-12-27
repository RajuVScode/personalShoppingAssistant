import httpx
import os
from typing import Optional, Dict, List, Any

class WeatherService:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_weather(self, latitude: float = 40.7128, longitude: float = -74.0060) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=10.0) as client:
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,precipitation,weather_code",
                    "timezone": "auto"
                }
                response = client.get(self.base_url, params=params)
                data = response.json()
                
                current = data.get("current", {})
                return {
                    "temperature": current.get("temperature_2m"),
                    "precipitation": current.get("precipitation"),
                    "weather_code": current.get("weather_code"),
                    "description": self._get_weather_description(current.get("weather_code", 0))
                }
        except Exception as e:
            return {"error": str(e), "description": "Unable to fetch weather data"}
    
    def _get_weather_description(self, code: int) -> str:
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            95: "Thunderstorm"
        }
        return weather_codes.get(code, "Unknown")

class EventsService:
    def __init__(self):
        self.api_key = os.getenv("TICKETMASTER_API_KEY")
        self.base_url = "https://app.ticketmaster.com/discovery/v2/events.json"
    
    def get_local_events(self, location: str = "New York", start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        if not self.api_key:
            return self._get_fallback_events()
        
        try:
            with httpx.Client(timeout=15.0) as client:
                params = {
                    "apikey": self.api_key,
                    "city": location,
                    "size": 10,
                    "sort": "date,asc"
                }
                
                if start_date:
                    params["startDateTime"] = f"{start_date}T00:00:00Z"
                if end_date:
                    params["endDateTime"] = f"{end_date}T23:59:59Z"
                
                response = client.get(self.base_url, params=params)
                data = response.json()
                
                events = []
                if "_embedded" in data and "events" in data["_embedded"]:
                    for event in data["_embedded"]["events"][:10]:
                        event_info = {
                            "name": event.get("name", "Unknown Event"),
                            "type": self._get_event_type(event),
                            "date": self._get_event_date(event),
                            "venue": self._get_venue(event),
                            "url": event.get("url", "")
                        }
                        events.append(event_info)
                
                return events if events else self._get_fallback_events()
                
        except Exception as e:
            print(f"Ticketmaster API error: {e}")
            return self._get_fallback_events()
    
    def _get_event_type(self, event: Dict) -> str:
        classifications = event.get("classifications", [])
        if classifications:
            segment = classifications[0].get("segment", {})
            return segment.get("name", "entertainment").lower()
        return "entertainment"
    
    def _get_event_date(self, event: Dict) -> str:
        dates = event.get("dates", {})
        start = dates.get("start", {})
        return start.get("localDate", "TBD")
    
    def _get_venue(self, event: Dict) -> str:
        embedded = event.get("_embedded", {})
        venues = embedded.get("venues", [])
        if venues:
            return venues[0].get("name", "")
        return ""
    
    def _get_fallback_events(self) -> List[Dict[str, Any]]:
        return [
            {"name": "Local Fashion Week", "type": "fashion", "date": "Upcoming", "venue": "Convention Center", "url": ""},
            {"name": "Tech Conference", "type": "business", "date": "Upcoming", "venue": "Expo Hall", "url": ""},
            {"name": "Music Festival", "type": "entertainment", "date": "Upcoming", "venue": "City Park", "url": ""}
        ]

class TrendsService:
    def get_fashion_trends(self) -> List[str]:
        return [
            "Sustainable fashion",
            "Oversized blazers",
            "Chunky sneakers",
            "Minimalist accessories",
            "Earth tones",
            "Athleisure wear"
        ]

class ExternalContextService:
    def __init__(self):
        self.weather_service = WeatherService()
        self.events_service = EventsService()
        self.trends_service = TrendsService()
    
    def get_environmental_context(self, location: Optional[str] = None, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        weather = self.weather_service.get_weather()
        events = self.events_service.get_local_events(location or "New York", start_date, end_date)
        trends = self.trends_service.get_fashion_trends()
        
        return {
            "weather": weather,
            "local_events": events,
            "trends": trends
        }
