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
1. ONLY ask for destination and travel_date if they are truly missing.
2. Once you have destination AND travel_date, ask ONE COMBINED question for any remaining optional details:
   "What activities are you planning, any budget constraints, and clothing preferences? (Feel free to share any or skip!)"
3. If user provides some optional details, ACCEPT them and proceed - do NOT ask for more.
4. If user says "that's it" or provides destination+dates without extras, PROCEED without asking more questions.
5. Activities, budget, and clothes are OPTIONAL - do not require them to proceed.

- Use US English tone, be helpful and polite.
- Infer budget currency from context; default to USD.
- If budget is provided without currency, set currency to USD by default.
- Activities should be either an array or strings. Accept single activities.
- Clothes can be a simple descriptive string.
- Be concise and avoid over-prompting.

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

class ClarifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("Clarifier", CLARIFIER_PROMPT)
    
    def _is_skip_response(self, query: str) -> bool:
        query_lower = query.lower().strip()
        return any(phrase in query_lower for phrase in SKIP_PHRASES)
    
    def _mentions_activity(self, query: str) -> bool:
        query_lower = query.lower().strip()
        return any(keyword in query_lower for keyword in ACTIVITY_KEYWORDS)
    
    def analyze(self, query: str, conversation_history: list = None, existing_intent: dict = None) -> dict:
        current_date = get_current_date()
        
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
            has_date = merged_intent.get("travel_date") or merged_intent.get("trip_segments")
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
            
            query_mentions_date = any(word in query.lower() for word in [
                "january", "february", "march", "april", "may", "june", 
                "july", "august", "september", "october", "november", "december",
                "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                "next week", "this week", "tomorrow", "today", "weekend",
                " to ", "-", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th",
                "10th", "11th", "12th", "13th", "14th", "15th"
            ])
            
            if has_required and already_asked_optional:
                return {
                    "needs_clarification": False,
                    "clarification_question": "",
                    "assistant_message": "Perfect! Let me prepare your personalized recommendations.",
                    "updated_intent": merged_intent,
                    "clarified_query": query,
                    "ready_for_recommendations": True
                }
            
            if has_required and not already_asked_optional:
                destinations = []
                if merged_intent.get("trip_segments"):
                    for seg in merged_intent["trip_segments"]:
                        if isinstance(seg, dict):
                            destinations.append(seg.get("destination", ""))
                        else:
                            destinations.append(seg.destination)
                else:
                    destinations = [merged_intent.get("destination", "")]
                
                dest_str = " and ".join(destinations)
                
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
            
            if has_destination and query_mentions_date and not already_asked_optional:
                destinations = []
                if merged_intent.get("trip_segments"):
                    for seg in merged_intent["trip_segments"]:
                        if isinstance(seg, dict):
                            destinations.append(seg.get("destination", ""))
                        else:
                            destinations.append(seg.destination)
                else:
                    destinations = [merged_intent.get("destination", "")]
                
                dest_str = " and ".join(destinations)
                
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
            
            if is_skip or mentions_activity or has_optional:
                if has_destination:
                    return {
                        "needs_clarification": False,
                        "clarification_question": "",
                        "assistant_message": "Perfect! Let me prepare your personalized recommendations.",
                        "updated_intent": merged_intent,
                        "clarified_query": query,
                        "ready_for_recommendations": True
                    }
            
            needs_clarification = not has_destination or (not has_date and not query_mentions_date)
            
            return {
                "needs_clarification": needs_clarification,
                "clarification_question": result.get("next_question") or result.get("assistant_message", ""),
                "assistant_message": result.get("assistant_message", ""),
                "updated_intent": merged_intent,
                "clarified_query": query,
                "ready_for_recommendations": not needs_clarification
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
