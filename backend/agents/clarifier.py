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

CRITICAL - EXTRACT EVERYTHING FROM USER MESSAGE:
- ACTIVITIES: If user says "travelling to Miami for hiking" or "going to Paris for shopping", IMMEDIATELY extract "hiking" or "shopping" into the activities array. Do NOT wait to ask - capture it NOW.
- DATES: If user mentions ANY date reference (next weekend, tomorrow, January 5, etc.), set has_date_info: true
- NEW TRIP: If user is starting a new trip (travelling to, going to, trip to, etc.), set is_new_trip: true

LOCATION EXTRACTION - CRITICAL:
- You MUST extract and normalize locations using your world knowledge.
- Set "destination_city" to the normalized city name (e.g., "Liverpool", "Birmingham", "Tokyo")
- Set "destination_country" to the normalized country name (e.g., "UK", "USA", "Japan")
- Set "country_only" to true if user mentions ONLY a country without a specific city (e.g., "travelling to the UK", "going to France")
- Handle typos gracefully using your knowledge (e.g., "Parris" → Paris, "Londun" → London)
- Combine city and country into "destination" field (e.g., "Liverpool, UK", "Tokyo, Japan")

COUNTRY-ONLY DETECTION:
- If user says "travelling to the UK" or "going to France" WITHOUT mentioning a city → set country_only: true
- If user says "travelling to Liverpool UK" or "going to Paris" → set country_only: false (city is present)
- When country_only is true, the system will ask which city they're visiting

CRITICAL RULES:
1. ONLY ask for destination and travel_date if they are truly MISSING (not mentioned at all).
2. NEVER ask for confirmation of an obvious destination. Accept city names as-is:
   - "Paris" → destination: "Paris, France", destination_city: "Paris", destination_country: "France"
   - "Liverpool UK" → destination: "Liverpool, UK", destination_city: "Liverpool", destination_country: "UK"
   - Handle any city worldwide using your knowledge - no hardcoded list needed
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

USER RESPONSE DETECTION - Use your language understanding to detect:
- "is_skip_response": true if user wants to skip/proceed without optional info (e.g., "that's it", "no preference", "just proceed", "I'm good", "nothing else", etc.)
- "mentions_activity": true if user mentions ANY activity, event, sport, or experience. Examples: "hiking", "cycling", "beach", "concert", "dining", "wedding", "sightseeing", "swimming", "shopping", "museum". Even a single word like "hiking" should set this to true.
- "is_confirmation": true if user is confirming something (e.g., "yes", "yeah", "correct", "that's right", etc.)

IMPORTANT - CAPTURING ACTIVITIES:
- When user mentions activities (even single words like "hiking" or "cycling"), ADD them to the "activities" array in updated_intent.
- Example: If user says "hiking", set activities: ["hiking"] AND mentions_activity: true
- Always preserve existing activities and ADD new ones to the array.

OUTPUT STRICTLY AS A JSON OBJECT with this shape:
{{
  "assistant_message": "string - what the assistant says to the user in this turn",
  "updated_intent": {{
      "destination": "string|null - normalized 'City, Country' format (e.g., 'Liverpool, UK')",
      "destination_city": "string|null - just the city name (e.g., 'Liverpool')",
      "destination_country": "string|null - just the country name (e.g., 'UK')",
      "country_only": true|false - true if user mentioned country without city,
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
  "is_skip_response": true|false,
  "mentions_activity": true|false,
  "is_confirmation": true|false,
  "has_date_info": true|false - true if user mentioned ANY date/time reference,
  "is_new_trip": true|false - true if user is starting a new trip request,
  "next_question": "string|null",
  "ready_for_recommendations": true|false
}}

Set "ready_for_recommendations": true when destination and travel_date are collected."""


COMMON_ACTIVITIES = {
    "hiking", "cycling", "swimming", "surfing", "skiing", "snowboarding",
    "shopping", "sightseeing", "dining", "beach", "museum", "concert",
    "wedding", "conference", "meeting", "business", "festival", "party",
    "spa", "wellness", "yoga", "golf", "tennis", "running", "jogging",
    "camping", "fishing", "climbing", "diving", "snorkeling", "kayaking",
    "sailing", "boating", "photography", "wine tasting", "cooking class",
    "tour", "adventure", "nightlife", "clubbing", "theater", "opera",
}

KNOWN_BRANDS = {
    "riviera atelier", "montclair house", "maison signature", "aurelle couture",
    "golden atelier", "veloce luxe", "luxe & co.", "evangeline", "opal essence",
    "bellezza studio", "seaside atelier", "sable & stone"
}


class ClarifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("Clarifier", CLARIFIER_PROMPT)
    
    def _extract_brand_fallback(self, query: str) -> str:
        """Extract brand name from user query by matching against known brands."""
        query_lower = query.lower().strip()
        for brand in KNOWN_BRANDS:
            if brand in query_lower:
                return brand.title()
        return None
    
    def _extract_activities_fallback(self, query: str) -> list:
        query_lower = query.lower()
        found = []
        for activity in COMMON_ACTIVITIES:
            if activity in query_lower:
                found.append(activity)
        return found
    
    def analyze(self, query: str, conversation_history: list = None, existing_intent: dict = None) -> dict:
        current_date = get_current_date()
        existing_intent = existing_intent or {}
        conversation_history = conversation_history or []
        
        existing_destination = existing_intent.get("destination")
        
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
            
            country_only = new_intent.get("country_only", False)
            destination_country = new_intent.get("destination_country")
            destination_city = new_intent.get("destination_city")
            
            if country_only and destination_country and not destination_city and not existing_destination:
                city_question = f"Which city are you travelling to in {destination_country}?"
                merged_intent["_pending_country"] = destination_country
                return {
                    "needs_clarification": True,
                    "clarification_question": city_question,
                    "assistant_message": city_question,
                    "updated_intent": merged_intent,
                    "clarified_query": query,
                    "ready_for_recommendations": False
                }
            
            if destination_city and destination_city != existing_destination:
                existing_intent["_asked_optional"] = False
            
            ready_for_recs = result.get("ready_for_recommendations", False)
            has_destination = merged_intent.get("destination")
            trip_segments = merged_intent.get("trip_segments") or []
            has_date = merged_intent.get("travel_date") or (len(trip_segments) > 0)
            has_required = has_destination and has_date
            
            already_asked_optional = existing_intent.get("_asked_optional", False) or merged_intent.get("_asked_optional", False)
            already_asked_activities = existing_intent.get("_asked_activities", False) or merged_intent.get("_asked_activities", False)
            
            is_skip = result.get("is_skip_response", False)
            mentions_activity = result.get("mentions_activity", False)
            
            new_activities = new_intent.get("activities") or []
            
            fallback_activities = self._extract_activities_fallback(query)
            if fallback_activities:
                if isinstance(new_activities, list):
                    for act in fallback_activities:
                        if act not in new_activities:
                            new_activities.append(act)
                else:
                    new_activities = fallback_activities
                merged_intent["activities"] = new_activities
                mentions_activity = True
            
            if new_activities and isinstance(new_activities, list) and len(new_activities) > 0:
                mentions_activity = True
            
            # Fallback brand extraction - check if user mentioned a brand
            fallback_brand = self._extract_brand_fallback(query)
            if fallback_brand and not merged_intent.get("preferred_brand"):
                merged_intent["preferred_brand"] = fallback_brand
                print(f"[DEBUG] Extracted brand from query: {fallback_brand}")
            
            # Check for budget or brand AFTER fallback extraction
            has_budget_or_brand = (
                merged_intent.get("budget_amount") or 
                merged_intent.get("preferred_brand")
            )
            
            is_new_trip = result.get("is_new_trip", False)
            if is_new_trip:
                existing_intent["_asked_optional"] = False
                existing_intent["_asked_activities"] = False
            
            llm_has_date_info = result.get("has_date_info", False)
            has_dates_info = has_date or llm_has_date_info
            
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
            
            # 1. Ask Activities if missing
            if has_destination and has_dates_info and not already_asked_activities:
                if mentions_activity or merged_intent.get("activities"):
                    merged_intent["_asked_activities"] = True
                else:
                    merged_intent["_asked_activities"] = True
                    activity_question = "What kind of activities are you planning for this trip? (e.g., hiking, shopping, dining)"
                    return {
                        "needs_clarification": True,
                        "clarification_question": activity_question,
                        "assistant_message": activity_question,
                        "updated_intent": merged_intent,
                        "clarified_query": query,
                        "ready_for_recommendations": False
                    }

            # 2. Ask Optional (Budget/Brand) if missing
            if has_destination and has_dates_info and (already_asked_activities or merged_intent.get("_asked_activities")) and not already_asked_optional:
                if has_budget_or_brand:
                    merged_intent["_asked_optional"] = True
                else:
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
                    
                    optional_question = f"Great! Your trip to {dest_str} is confirmed. Do you have any preferences for budget or favorite brands? (This is optional - feel free to skip!)"
                    
                    return {
                        "needs_clarification": True,
                        "clarification_question": optional_question,
                        "assistant_message": optional_question,
                        "updated_intent": merged_intent,
                        "clarified_query": query,
                        "ready_for_recommendations": False
                    }
            
            if already_asked_optional and already_asked_activities:
                if is_skip or has_budget_or_brand or mentions_activity or has_dates_info:
                    return {
                        "needs_clarification": False,
                        "clarification_question": "",
                        "assistant_message": "Perfect! Let me prepare your personalized recommendations.",
                        "updated_intent": merged_intent,
                        "clarified_query": query,
                        "ready_for_recommendations": True
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
