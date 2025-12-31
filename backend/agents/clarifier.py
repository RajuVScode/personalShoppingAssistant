import json
from datetime import datetime, timedelta
from backend.agents.base import BaseAgent

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_weekend_dates(current_date: datetime, next_week: bool = False):
    days_until_saturday = (5 - current_date.weekday()) % 7
    if days_until_saturday == 0 and current_date.weekday() != 5:
        days_until_saturday = 7
    if next_week:
        days_until_saturday += 7
    saturday = current_date + timedelta(days=days_until_saturday)
    sunday = saturday + timedelta(days=1)
    return saturday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

CLARIFIER_PROMPT = """You are a Clarifier Agent for travel planning. Your task:
- Extract or confirm the user's intent across these fields:
  destination, travel_date, activities, preferred_brand, clothes, budget_amount, budget_currency, notes.
- SUPPORT MULTI-DESTINATION TRIPS: If user mentions multiple destinations with dates (e.g., "Paris Jan 5-8, then Rome Jan 9-12"), extract ALL of them into trip_segments.

CRITICAL RULES:
1. ONLY ask for destination and travel_date if they are truly MISSING (not mentioned at all).
2. NEVER ask for confirmation of an obvious destination. Accept city names as-is:
   - "Paris" → destination: "Paris, France" (DO NOT ask "did you mean Paris, France?")
   - "Rome" → destination: "Rome, Italy"
   - "Tokyo" → destination: "Tokyo, Japan"
   - "Parris" or "Prais" → Assume Paris, France (handle typos gracefully)
3. Once you have destination AND travel_date, proceed - do NOT over-clarify.
4. If user provides some optional details, ACCEPT them and proceed - do NOT ask for more.
5. If user says "that's it" or provides destination+dates without extras, PROCEED without asking more questions.
6. Activities, budget, and clothes are OPTIONAL - do not require them to proceed.
7. NEVER get stuck in a loop asking the same question. If user confirms a destination, ACCEPT it immediately.

- Use US English tone, be helpful and polite.
- Infer budget currency from context; default to USD.
- If budget is provided without currency, set currency to USD by default.
- Activities should be either an array or strings. Accept single activities.
- Clothes can be a simple descriptive string.
- Be concise and avoid over-prompting.
- DO NOT ask "did you mean X?" for obvious destinations - just accept them.

Context:
- Today's date (ISO): {CURRENT_DATE}

Rules:
- Keep assistant_message friendly and purposeful.
- Use next_question only if more info is needed AND ask exactly one question.
- Never include extra keys or text outside the JSON.
- Please don't consider model date as current date. Always use the provided CURRENT_DATE.
- If only one date is mentioned, set start_date = end_date.
- Parse various date formats:
- Parse ranges like "from 5 March to 8 March", "10-12 Jan 2025", "2025-01-10 to 2025-01-12".
- Support relative dates and ACCEPT THEM as valid travel dates:
- "today" => {CURRENT_DATE}
- "tomorrow" => {CURRENT_DATE} + 1 day
- "this week" => current week dates
- "next week" => the following week dates (Monday-Sunday)
- "this weekend" => Saturday-Sunday of the current week
- "next weekend" => Saturday-Sunday of the following week
- "next month" => dates in the following calendar month
- IMPORTANT: "next week", "this weekend", etc. are VALID date inputs - do NOT ask for more specific dates!
- CRITICAL: All dates MUST be in the FUTURE relative to {CURRENT_DATE}. If today is late December 2025, "next week" means early January 2026, NOT January 2025.
- If month/day is given without year, always use the NEXT occurrence of that date in the future. If "January 5" is mentioned and today is December 27, 2025, it means January 5, 2026.
- Date format: "YYYY-MM-DD" (single date) or "YYYY-MM-DD to YYYY-MM-DD" (range).

MULTI-DESTINATION HANDLING:
- If user mentions multiple destinations with different dates, extract each as a trip_segment.
- Example: "Paris Jan 5-8, then Rome Jan 9-12" → two segments
- Each segment has: destination, start_date, end_date, activities (optional)
- Set "destination" to first destination, "travel_date" to full range (first start to last end)
- Preserve trip_segments array for detailed per-leg context

DECISION LOGIC:
- If destination is missing → next_question asks for destination
- If travel_date is missing (and no relative date like "next week" given) → next_question asks for travel dates  
- If destination AND travel_date are present → Set next_question to null AND ready_for_recommendations to true
- Once you have destination + any date reference → PROCEED to recommendations (set next_question: null, ready_for_recommendations: true)
- DO NOT ask for activities/budget/clothes individually - these are optional extras

OUTPUT STRICTLY AS A JSON OBJECT with this shape:
{{
  "assistant_message": "string - what the assistant says to the user in this turn",
  "updated_intent": {{
      "destination": "string|null - primary destination (first if multiple)",
      "travel_date": "string|null - full date range",
      "trip_segments": [
          {{
              "destination": "string",
              "start_date": "YYYY-MM-DD",
              "end_date": "YYYY-MM-DD",
              "activities": ["string", ...]|null
          }}
      ]|null,
      "activities": ["string", ...]|null,
      "preferred_brand": "string|null",
      "clothes": "string|null",
      "budget_amount": number|null,
      "budget_currency": "string|null",
      "notes": "string|null"
  }},
  "next_question": "string|null",
  "ready_for_recommendations": true|false
}}

Set "ready_for_recommendations": true when destination and travel_date are collected."""


SKIP_PHRASES = [
    "no preference", "no preferences", "no specific preference", "no specific preferences",
    "none", "nothing", "skip", "proceed", "that's it", "thats it", "that is it",
    "no budget", "no clothing", "no activities", "no constraints", "no specific",
    "just proceed", "go ahead", "continue", "no thanks", "no thank you",
    "i'm good", "im good", "all good", "nothing specific", "nothing else",
    "no particular", "don't have any", "dont have any", "no additional",
]

ACTIVITY_KEYWORDS = [
    "attending", "attend", "event", "events", "local events", "concert", "concerts",
    "dinner", "dining", "restaurant", "beach", "hiking", "sightseeing", "tour",
    "museum", "shopping", "nightlife", "party", "festival", "sports", "game",
    "meeting", "conference", "business", "wedding", "ceremony", "show", "theater",
    "theatre", "opera", "ballet", "club", "bar", "swimming", "skiing", "surfing",
    "exploring", "adventure", "outdoor", "indoor", "relaxing", "spa", "wellness",
]

CONFIRMATION_PATTERNS = [
    "yes", "yeah", "yep", "yup", "correct", "right", "exactly", "that's right",
    "it is", "that is", "yes it is", "yes, it is", "confirmed", "affirmative",
]

CITY_ALIASES = {
    "paris": "Paris, France",
    "parris": "Paris, France",
    "prais": "Paris, France",
    "pari": "Paris, France",
    "rome": "Rome, Italy",
    "tokyo": "Tokyo, Japan",
    "london": "London, UK",
    "manchester": "Manchester, UK",
    "birmingham": "Birmingham, UK",
    "liverpool": "Liverpool, UK",
    "edinburgh": "Edinburgh, UK",
    "glasgow": "Glasgow, UK",
    "bristol": "Bristol, UK",
    "leeds": "Leeds, UK",
    "sheffield": "Sheffield, UK",
    "newcastle": "Newcastle, UK",
    "cardiff": "Cardiff, UK",
    "belfast": "Belfast, UK",
    "oxford": "Oxford, UK",
    "cambridge": "Cambridge, UK",
    "new york": "New York, USA",
    "ny": "New York, USA",
    "nyc": "New York, USA",
    "miami": "Miami, USA",
    "los angeles": "Los Angeles, USA",
    "la": "Los Angeles, USA",
    "chicago": "Chicago, USA",
    "san francisco": "San Francisco, USA",
    "seattle": "Seattle, USA",
    "boston": "Boston, USA",
    "washington": "Washington D.C., USA",
    "las vegas": "Las Vegas, USA",
    "orlando": "Orlando, USA",
    "barcelona": "Barcelona, Spain",
    "madrid": "Madrid, Spain",
    "berlin": "Berlin, Germany",
    "munich": "Munich, Germany",
    "frankfurt": "Frankfurt, Germany",
    "amsterdam": "Amsterdam, Netherlands",
    "sydney": "Sydney, Australia",
    "melbourne": "Melbourne, Australia",
    "dubai": "Dubai, UAE",
    "singapore": "Singapore",
    "hong kong": "Hong Kong",
    "toronto": "Toronto, Canada",
    "vancouver": "Vancouver, Canada",
    "montreal": "Montreal, Canada",
    "mexico city": "Mexico City, Mexico",
    "cancun": "Cancun, Mexico",
    "mumbai": "Mumbai, India",
    "delhi": "Delhi, India",
    "bangalore": "Bangalore, India",
    "bangkok": "Bangkok, Thailand",
    "phuket": "Phuket, Thailand",
    "bali": "Bali, Indonesia",
    "jakarta": "Jakarta, Indonesia",
    "kuala lumpur": "Kuala Lumpur, Malaysia",
    "seoul": "Seoul, South Korea",
    "beijing": "Beijing, China",
    "shanghai": "Shanghai, China",
    "lisbon": "Lisbon, Portugal",
    "porto": "Porto, Portugal",
    "athens": "Athens, Greece",
    "santorini": "Santorini, Greece",
    "istanbul": "Istanbul, Turkey",
    "vienna": "Vienna, Austria",
    "prague": "Prague, Czech Republic",
    "budapest": "Budapest, Hungary",
    "warsaw": "Warsaw, Poland",
    "zurich": "Zurich, Switzerland",
    "geneva": "Geneva, Switzerland",
    "brussels": "Brussels, Belgium",
    "copenhagen": "Copenhagen, Denmark",
    "stockholm": "Stockholm, Sweden",
    "oslo": "Oslo, Norway",
    "helsinki": "Helsinki, Finland",
    "dublin": "Dublin, Ireland",
    "auckland": "Auckland, New Zealand",
    "cape town": "Cape Town, South Africa",
    "johannesburg": "Johannesburg, South Africa",
    "cairo": "Cairo, Egypt",
    "marrakech": "Marrakech, Morocco",
}

COUNTRY_NAMES = {
    "uk": "the UK",
    "united kingdom": "the UK",
    "britain": "the UK",
    "england": "England",
    "usa": "the USA",
    "united states": "the USA",
    "america": "the USA",
    "us": "the USA",
    "france": "France",
    "germany": "Germany",
    "italy": "Italy",
    "spain": "Spain",
    "japan": "Japan",
    "china": "China",
    "australia": "Australia",
    "canada": "Canada",
    "mexico": "Mexico",
    "brazil": "Brazil",
    "india": "India",
    "netherlands": "the Netherlands",
    "holland": "the Netherlands",
    "switzerland": "Switzerland",
    "austria": "Austria",
    "portugal": "Portugal",
    "greece": "Greece",
    "turkey": "Turkey",
    "thailand": "Thailand",
    "vietnam": "Vietnam",
    "indonesia": "Indonesia",
    "malaysia": "Malaysia",
    "south korea": "South Korea",
    "korea": "South Korea",
    "uae": "the UAE",
    "united arab emirates": "the UAE",
    "saudi arabia": "Saudi Arabia",
    "egypt": "Egypt",
    "morocco": "Morocco",
    "south africa": "South Africa",
    "new zealand": "New Zealand",
    "ireland": "Ireland",
    "scotland": "Scotland",
    "wales": "Wales",
    "belgium": "Belgium",
    "sweden": "Sweden",
    "norway": "Norway",
    "denmark": "Denmark",
    "finland": "Finland",
    "poland": "Poland",
    "czech republic": "the Czech Republic",
    "hungary": "Hungary",
    "russia": "Russia",
    "argentina": "Argentina",
    "chile": "Chile",
    "colombia": "Colombia",
    "peru": "Peru",
}

class ClarifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("Clarifier", CLARIFIER_PROMPT)
    
    def _is_skip_response(self, query: str) -> bool:
        query_lower = query.lower().strip()
        return any(phrase in query_lower for phrase in SKIP_PHRASES)
    
    def _mentions_activity(self, query: str) -> bool:
        query_lower = query.lower().strip()
        return any(keyword in query_lower for keyword in ACTIVITY_KEYWORDS)
    
    def _is_confirmation(self, query: str) -> bool:
        query_lower = query.lower().strip()
        return any(pattern in query_lower for pattern in CONFIRMATION_PATTERNS)
    
    def _extract_city_from_query(self, query: str) -> str:
        query_lower = query.lower().strip()
        for alias, city in CITY_ALIASES.items():
            if alias in query_lower:
                return city
        return None
    
    def _is_new_trip_request(self, query: str) -> bool:
        query_lower = query.lower().strip()
        trip_indicators = [
            "travelling to", "traveling to", "going to", "flying to",
            "trip to", "visit", "planning to go", "want to go",
            "heading to", "travel to"
        ]
        return any(indicator in query_lower for indicator in trip_indicators)
    
    def _extract_country_only(self, query: str) -> str:
        query_lower = query.lower().strip()
        city_found = self._extract_city_from_query(query)
        if city_found:
            return None
        
        for country_key, country_name in COUNTRY_NAMES.items():
            if country_key in query_lower:
                return country_name
        return None
    
    def analyze(self, query: str, conversation_history: list = None, existing_intent: dict = None) -> dict:
        current_date = get_current_date()
        existing_intent = existing_intent or {}
        
        city_in_query = self._extract_city_from_query(query)
        is_confirmation = self._is_confirmation(query)
        existing_destination = existing_intent.get("destination")
        
        is_new_trip = self._is_new_trip_request(query)
        if is_new_trip:
            existing_intent["_asked_optional"] = False
        
        if city_in_query:
            if city_in_query != existing_destination:
                existing_intent["_asked_optional"] = False
            existing_intent["destination"] = city_in_query
            if is_confirmation or (len(query.strip().split()) <= 4):
                pass
        
        country_only = self._extract_country_only(query)
        if country_only and not city_in_query and not existing_destination:
            existing_intent["_pending_country"] = country_only
            city_question = f"Which city are you travelling to in {country_only}?"
            return {
                "needs_clarification": True,
                "clarification_question": city_question,
                "assistant_message": city_question,
                "updated_intent": existing_intent,
                "clarified_query": query,
                "ready_for_recommendations": False
            }
        
        context = ""
        if conversation_history:
            context = f"\nConversation history: {json.dumps(conversation_history[-5:])}"
        
        existing_intent_str = ""
        if existing_intent:
            filled_fields = {k: v for k, v in existing_intent.items() if v is not None}
            if filled_fields:
                existing_intent_str = f"\n\nALREADY COLLECTED INFORMATION (DO NOT ask for these again):\n{json.dumps(filled_fields, indent=2)}"
        
        prompt = f"""Today's date: {current_date}

User query: {query}{context}{existing_intent_str}

IMPORTANT: If information was already collected (shown above), preserve it in updated_intent and DO NOT ask for it again.
Only ask for MISSING information that hasn't been collected yet.

Extract travel intent and respond with the JSON structure. If key details are missing (destination, travel_date), ask ONE clarifying question."""
        
        system_prompt = CLARIFIER_PROMPT.replace("{CURRENT_DATE}", current_date)
        
        response = self.invoke(prompt, system_override=system_prompt)
        
        try:
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            clean_response = clean_response.replace("{{", "{").replace("}}", "}")
            
            result = json.loads(clean_response.strip())
            
            new_intent = result.get("updated_intent", {})
            merged_intent = self._merge_intent(existing_intent or {}, new_intent)
            
            ready_for_recs = result.get("ready_for_recommendations", False)
            has_destination = merged_intent.get("destination")
            trip_segments = merged_intent.get("trip_segments") or []
            has_date = merged_intent.get("travel_date") or (len(trip_segments) > 0)
            has_required = has_destination and has_date
            
            has_optional = (
                merged_intent.get("activities") or 
                merged_intent.get("budget_amount") or 
                merged_intent.get("clothes") or
                merged_intent.get("preferred_brand")
            )
            
            already_asked_optional = existing_intent.get("_asked_optional", False)
            
            is_skip = self._is_skip_response(query)
            mentions_activity = self._mentions_activity(query)
            
            query_lower = query.lower()
            date_keywords = [
                "january", "february", "march", "april", "may", "june", 
                "july", "august", "september", "october", "november", "december",
                "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                "next week", "this week", "tomorrow", "today", "weekend", "next month",
                "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th",
                "10th", "11th", "12th", "13th", "14th", "15th",
                "16th", "17th", "18th", "19th", "20th", "21st", "22nd", "23rd",
                "24th", "25th", "26th", "27th", "28th", "29th", "30th", "31st"
            ]
            
            import re
            has_date_range = bool(re.search(r'\d+\s*(to|-)\s*\d+', query_lower))
            has_month_day = bool(re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d+', query_lower))
            
            query_mentions_date = any(word in query_lower for word in date_keywords) or has_date_range or has_month_day
            
            has_dates_info = has_date or query_mentions_date
            
            if has_destination and not has_dates_info:
                dest = merged_intent.get("destination", "your destination")
                date_question = f"When are you planning to travel to {dest}? (e.g., 'next weekend', 'January 15-20', or specific dates)"
                return {
                    "needs_clarification": True,
                    "clarification_question": date_question,
                    "assistant_message": date_question,
                    "updated_intent": merged_intent,
                    "clarified_query": query,
                    "ready_for_recommendations": False
                }
            
            if already_asked_optional:
                if is_skip or has_optional or mentions_activity or has_dates_info:
                    return {
                        "needs_clarification": False,
                        "clarification_question": "",
                        "assistant_message": "Perfect! Let me prepare your personalized recommendations.",
                        "updated_intent": merged_intent,
                        "clarified_query": query,
                        "ready_for_recommendations": True
                    }
            
            if has_destination and has_dates_info and not already_asked_optional:
                destinations = []
                if merged_intent.get("trip_segments"):
                    for seg in merged_intent["trip_segments"]:
                        if isinstance(seg, dict):
                            destinations.append(seg.get("destination", ""))
                        else:
                            destinations.append(seg.destination)
                if not destinations:
                    destinations = [merged_intent.get("destination", "")]
                
                dest_str = " and ".join([d for d in destinations if d])
                if not dest_str:
                    dest_str = "your destinations"
                
                merged_intent["_asked_optional"] = True
                
                optional_question = f"Great! Your trip to {dest_str} is confirmed. Do you have any preferences for activities, budget, or favorite brands? (This is optional - feel free to skip!)"
                
                return {
                    "needs_clarification": True,
                    "clarification_question": optional_question,
                    "assistant_message": optional_question,
                    "updated_intent": merged_intent,
                    "clarified_query": query,
                    "ready_for_recommendations": False
                }
            
            if not has_destination:
                return {
                    "needs_clarification": True,
                    "clarification_question": result.get("next_question") or "Where would you like to travel?",
                    "assistant_message": result.get("assistant_message", ""),
                    "updated_intent": merged_intent,
                    "clarified_query": query,
                    "ready_for_recommendations": False
                }
            
            return {
                "needs_clarification": False,
                "clarification_question": "",
                "assistant_message": "Perfect! Let me prepare your personalized recommendations.",
                "updated_intent": merged_intent,
                "clarified_query": query,
                "ready_for_recommendations": True
            }
        except json.JSONDecodeError:
            return {
                "needs_clarification": False,
                "clarified_query": query,
                "assistant_message": "",
                "updated_intent": existing_intent or {}
            }
    
    def _merge_intent(self, existing: dict, new: dict) -> dict:
        merged = existing.copy()
        for key, value in new.items():
            if value is not None:
                merged[key] = value
        return merged
