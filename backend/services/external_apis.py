import httpx
import os
from typing import Optional, Dict, List, Any

class WeatherService:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    async def get_weather(self, latitude: float = 40.7128, longitude: float = -74.0060) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,precipitation,weather_code",
                    "timezone": "auto"
                }
                response = await client.get(self.base_url, params=params, timeout=10.0)
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
    async def get_local_events(self, location: str = "New York") -> List[Dict[str, Any]]:
        return [
            {"name": "Summer Fashion Week", "type": "fashion", "date": "2025-01-15"},
            {"name": "Tech Conference 2025", "type": "business", "date": "2025-01-20"},
            {"name": "Outdoor Music Festival", "type": "entertainment", "date": "2025-01-25"}
        ]

class TrendsService:
    async def get_fashion_trends(self) -> List[str]:
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
    
    async def get_environmental_context(self, location: Optional[str] = None) -> Dict[str, Any]:
        weather = await self.weather_service.get_weather()
        events = await self.events_service.get_local_events(location or "New York")
        trends = await self.trends_service.get_fashion_trends()
        
        return {
            "weather": weather,
            "local_events": events,
            "trends": trends
        }
