import httpx
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

class WeatherService:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.location_coords = {
            "paris": (48.8566, 2.3522),
            "london": (51.5074, -0.1278),
            "new york": (40.7128, -74.0060),
            "los angeles": (34.0522, -118.2437),
            "tokyo": (35.6762, 139.6503),
            "sydney": (-33.8688, 151.2093),
            "dubai": (25.2048, 55.2708),
            "miami": (25.7617, -80.1918),
            "seattle": (47.6062, -122.3321),
            "chicago": (41.8781, -87.6298),
            "san francisco": (37.7749, -122.4194),
            "boston": (42.3601, -71.0589),
            "rome": (41.9028, 12.4964),
            "barcelona": (41.3851, 2.1734),
            "berlin": (52.5200, 13.4050),
            "amsterdam": (52.3676, 4.9041),
            "singapore": (1.3521, 103.8198),
            "hong kong": (22.3193, 114.1694),
            "bangkok": (13.7563, 100.5018),
            "mumbai": (19.0760, 72.8777),
        }
    
    def _get_coordinates(self, location: str) -> tuple:
        if not location:
            return (40.7128, -74.0060)
        
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(self.geocode_url, params={"name": location, "count": 1})
                data = response.json()
                if data.get("results"):
                    result = data["results"][0]
                    return (result["latitude"], result["longitude"])
        except:
            pass
        
        location_lower = location.lower().strip()
        if location_lower in self.location_coords:
            return self.location_coords[location_lower]
        
        return (40.7128, -74.0060)
    
    def get_weather(self, location: str = None, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        latitude, longitude = self._get_coordinates(location)
        
        days_until_travel = self._calculate_days_until_travel(start_date)
        
        if days_until_travel > 16:
            return self._get_historical_weather(latitude, longitude, location, start_date, end_date)
        
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
                    "description": self._get_weather_description(current.get("weather_code", 0)),
                    "location": location or "Default"
                }
        except Exception as e:
            return {"error": str(e), "description": "Unable to fetch weather data"}
    
    def _calculate_days_until_travel(self, start_date: str) -> int:
        if not start_date:
            return 0
        try:
            travel_date = datetime.strptime(start_date, "%Y-%m-%d")
            today = datetime.now()
            delta = (travel_date - today).days
            return max(0, delta)
        except:
            return 0
    
    def _get_historical_weather(self, latitude: float, longitude: float, location: str, start_date: str, end_date: str) -> Dict[str, Any]:
        try:
            from meteostat import Point, Normals
            
            point = Point(latitude, longitude)
            
            normals = Normals(point)
            df = normals.fetch()
            
            if df.empty:
                return self._get_climate_estimate(latitude, location)
            
            target_month = 1
            if start_date:
                try:
                    travel_date = datetime.strptime(start_date, "%Y-%m-%d")
                    target_month = travel_date.month
                except:
                    pass
            
            if target_month in df.index:
                month_data = df.loc[target_month]
                avg_temp = month_data.get('tavg')
                if avg_temp is None:
                    tmin = month_data.get('tmin', 15)
                    tmax = month_data.get('tmax', 25)
                    avg_temp = (tmin + tmax) / 2 if tmin and tmax else 20
                
                prcp = month_data.get('prcp', 0)
                
                description = self._get_climate_description(avg_temp, prcp)
                
                return {
                    "temperature": round(avg_temp, 1) if avg_temp else 20,
                    "precipitation": prcp,
                    "description": f"{description} (historical average)",
                    "location": location or "Default",
                    "data_source": "meteostat_normals"
                }
            else:
                return self._get_climate_estimate(latitude, location)
                
        except Exception as e:
            return self._get_climate_estimate(latitude, location)
    
    def _get_climate_estimate(self, latitude: float, location: str) -> Dict[str, Any]:
        if abs(latitude) < 23.5:
            temp, desc = 28, "Tropical climate"
        elif abs(latitude) < 35:
            temp, desc = 22, "Subtropical climate"
        elif abs(latitude) < 50:
            temp, desc = 15, "Temperate climate"
        else:
            temp, desc = 8, "Cool climate"
        
        return {
            "temperature": temp,
            "description": f"{desc} (estimated)",
            "location": location or "Default",
            "data_source": "estimate"
        }
    
    def _get_climate_description(self, temp: float, prcp: float) -> str:
        if temp > 30:
            temp_desc = "Hot"
        elif temp > 25:
            temp_desc = "Warm"
        elif temp > 15:
            temp_desc = "Mild"
        elif temp > 5:
            temp_desc = "Cool"
        else:
            temp_desc = "Cold"
        
        if prcp > 100:
            prcp_desc = ", rainy"
        elif prcp > 50:
            prcp_desc = ", some rain expected"
        else:
            prcp_desc = ""
        
        return f"{temp_desc}{prcp_desc}"
    
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
                            "title": event.get("name", "Unknown Event"),
                            "type": self._get_event_type(event),
                            "start": self._get_event_start(event),
                            "end": self._get_event_end(event),
                            "venue": self._get_venue(event),
                            "url": event.get("url", ""),
                            "description": self._get_description(event),
                            "weather_sensitive": self._is_weather_sensitive(event)
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
    
    def _get_event_start(self, event: Dict) -> str:
        dates = event.get("dates", {})
        start = dates.get("start", {})
        local_date = start.get("localDate", "TBD")
        local_time = start.get("localTime", "")
        if local_time:
            return f"{local_date} {local_time}"
        return local_date
    
    def _get_event_end(self, event: Dict) -> str:
        dates = event.get("dates", {})
        end = dates.get("end", {})
        local_date = end.get("localDate", "")
        local_time = end.get("localTime", "")
        if local_date and local_time:
            return f"{local_date} {local_time}"
        elif local_date:
            return local_date
        return ""
    
    def _get_venue(self, event: Dict) -> str:
        embedded = event.get("_embedded", {})
        venues = embedded.get("venues", [])
        if venues:
            venue = venues[0]
            name = venue.get("name", "")
            city = venue.get("city", {}).get("name", "")
            state = venue.get("state", {}).get("stateCode", "")
            if city and state:
                return f"{name}, {city}, {state}"
            elif city:
                return f"{name}, {city}"
            return name
        return ""
    
    def _get_description(self, event: Dict) -> str:
        info = event.get("info", "") or event.get("pleaseNote", "")
        if info:
            return info[:200] + "..." if len(info) > 200 else info
        classifications = event.get("classifications", [])
        if classifications:
            genre = classifications[0].get("genre", {}).get("name", "")
            segment = classifications[0].get("segment", {}).get("name", "")
            if genre and segment:
                return f"{segment} - {genre} event"
            elif segment:
                return f"{segment} event"
        return "Live event"
    
    def _is_weather_sensitive(self, event: Dict) -> bool:
        embedded = event.get("_embedded", {})
        venues = embedded.get("venues", [])
        if venues:
            venue = venues[0]
            if venue.get("upcomingEvents", {}).get("outdoor"):
                return True
            venue_type = venue.get("type", "").lower()
            if "outdoor" in venue_type or "park" in venue_type or "stadium" in venue_type:
                return True
        event_type = self._get_event_type(event).lower()
        outdoor_types = ["sports", "music", "festival", "outdoor"]
        return any(t in event_type for t in outdoor_types)
    
    def _get_fallback_events(self) -> List[Dict[str, Any]]:
        return [
            {"title": "Local Fashion Week", "type": "fashion", "start": "Upcoming", "end": "", "venue": "Convention Center", "url": "", "description": "Fashion and style showcase", "weather_sensitive": False},
            {"title": "Tech Conference", "type": "business", "start": "Upcoming", "end": "", "venue": "Expo Hall", "url": "", "description": "Technology and innovation event", "weather_sensitive": False},
            {"title": "Music Festival", "type": "entertainment", "start": "Upcoming", "end": "", "venue": "City Park", "url": "", "description": "Outdoor music and arts festival", "weather_sensitive": True}
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
        weather = self.weather_service.get_weather(location, start_date, end_date)
        events = self.events_service.get_local_events(location or "New York", start_date, end_date)
        trends = self.trends_service.get_fashion_trends()
        
        return {
            "weather": weather,
            "local_events": events,
            "trends": trends
        }
