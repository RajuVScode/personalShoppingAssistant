"""
Clarifier Agent Module - Dynamic Model-Driven Approach

This module implements the ClarifierAgent using a fully dynamic, LLM-driven approach
with NO hardcoded keywords or decision trees.

Key Principles:
- Dynamic, model-driven behavior only
- Semantic intent inference using LLM
- Minimal, relevant follow-up questions
- Context-aware routing (travel vs non-travel vs direct product)

The agent routes requests semantically:
A) Travel/Trip Context → ask travel-relevant questions only
B) Non-Travel Shopping → ask product-relevant questions only  
C) Direct Product Request → skip discovery, move to recommendations
"""

import json
from datetime import datetime, timedelta
from backend.agents.base import BaseAgent
from backend.utils.date_parser import parse_relative_date


def get_current_date():
    """Return today's date in ISO format (YYYY-MM-DD)."""
    return datetime.now().strftime("%Y-%m-%d")


def get_weekend_dates(current_date: datetime, next_week: bool = False):
    """
    Calculate the dates for the upcoming weekend (Saturday and Sunday).
    
    Args:
        current_date: The reference date to calculate from
        next_week: If True, get next week's weekend instead of this week's
        
    Returns:
        Tuple of (saturday_date, sunday_date) in YYYY-MM-DD format
    """
    days_until_saturday = (5 - current_date.weekday()) % 7
    if days_until_saturday == 0 and current_date.weekday() != 5:
        days_until_saturday = 7
    if next_week:
        days_until_saturday += 7
    saturday = current_date + timedelta(days=days_until_saturday)
    sunday = saturday + timedelta(days=1)
    return saturday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


CLARIFIER_PROMPT = """You are a Dynamic Personal Shopping Assistant. Your role is to understand user intent semantically and ask only minimal, relevant follow-up questions.

NON-NEGOTIABLE PRINCIPLES:
- Dynamic, model-driven behavior only. No hardcoded rules.
- Infer intent and entities semantically from natural language.
- Ask only minimal, relevant questions needed to proceed.
- Provide recommendations when requirements are sufficiently clear.

INTENT ROUTING (Infer semantically - no keywords):

A) TRAVEL/TRIP CONTEXT
If user indicates a travel scenario, ask ONLY travel-relevant questions:
- Destination (city/region/country)
- Dates or timeframe (start/end or approximate like "in January")
- Activities/goals (sightseeing, relaxation, business, adventure)
- Budget range (optional)
Do NOT ask product detail questions unless user explicitly requests products for the trip.

B) NON-TRAVEL SHOPPING (birthday, wedding, gifting, home, tech, etc.)
If shopping is unrelated to travel, do NOT ask for destination, travel dates, or travel activities.
Ask product-relevant questions:
- Product category/type (if unspecified)
- Intended use or recipient
- Key attributes (size, color, style, theme)
- Quantity and budget range

C) DIRECT PRODUCT REQUEST
If user clearly specifies a product (e.g., "shoes for Paris trip in January, Size M"):
- SKIP discovery questions
- Extract ALL details from the message (product, destination, dates, size)
- If only 1-2 critical details missing, ask at most 1-2 clarifying questions
- Move quickly to recommendations

SIZE/COLOR PREFERENCE:
- Capture any size mentioned (UK 9, M, L, EU 42, 32, etc.) in preferred_size
- Size and color are OPTIONAL - if user says "no preference", "any size", "doesn't matter", or similar, proceed WITHOUT filtering
- When user declines preference questions with "no", "skip", "no preference", set is_skip_response: true and proceed to recommendations

DATE HANDLING:
- Recognize ALL date formats semantically: "19th Jan", "Jan 19", "January 19th", "19 January", "the 19th", "tomorrow", "next week", etc.
- When user provides a specific day (like "19th Jan" or "tomorrow"), this IS a complete date - do NOT ask for dates again
- Combine partial dates with prior context: if month was mentioned before and user now provides day, merge them
- All dates must be FUTURE relative to {CURRENT_DATE}
- Set has_date_info: true when ANY recognizable date/time information is provided
- IMPORTANT: Do NOT ask for travel TIME (hours/minutes). Only travel DATE is required. Once a date is captured, proceed with other questions or recommendations.

VAGUE/PARTIAL DATE DETECTION (CRITICAL FOR TRAVEL):
- When user provides ONLY a month (e.g., "January", "in February", "next March") WITHOUT specific days, this is a PARTIAL DATE
- When user provides ONLY a duration (e.g., "one week", "two weeks", "a few days") WITHOUT specific start/end dates, this is a PARTIAL DATE
- When user provides vague timeframes (e.g., "sometime next month", "early January", "late February"), this is a PARTIAL DATE
- For PARTIAL DATES: Set is_partial_date: true and partial_date_value to the detected timeframe (e.g., "January", "one week")
- For PARTIAL DATES in travel context: You MUST ask for specific dates in your assistant_message
  Example: "What specific dates in January are you planning to travel to Paris?"
  Example: "When exactly would you like to visit? Could you provide the start and end dates for your one week trip?"
- Do NOT proceed to recommendations with only partial dates for travel - you need exact dates to provide weather-appropriate recommendations
- COMPLETE DATES include: specific day + month (e.g., "Jan 19-25", "19th to 25th January", "January 19")

PAST DATE VALIDATION (CRITICAL):
- Today's date is {CURRENT_DATE}. All travel dates MUST be in the FUTURE.
- If user provides dates that are clearly in the PAST relative to today, set is_past_date: true
- For PAST DATES: Ask user to provide valid FUTURE dates in your assistant_message
  Example: "Those dates have already passed. Could you please provide future travel dates?"
  Example: "January 15th has already passed. When would you like to travel instead?"
- Do NOT proceed to recommendations with past dates

QUESTIONING POLICY:
- Ask ONLY for missing, high-impact information
- Do NOT repeat already provided details
- Keep questions concise (one sentence)
- If intent is ambiguous, ask ONE targeted question

Today's date: {CURRENT_DATE}

OUTPUT AS JSON:
{{
  "assistant_message": "string - your response to the user",
  "updated_intent": {{
      "destination": "string|null - 'City, Country' format",
      "destination_city": "string|null",
      "destination_country": "string|null",
      "country_only": true|false,
      "travel_date": "string|null",
      "trip_segments": [...]|null,
      "activities": ["string", ...]|null,
      "preferred_brand": "string|null",
      "preferred_size": "string|null",
      "clothes": "string|null",
      "budget_amount": number|null,
      "budget_currency": "string|null",
      "notes": "string|null",
      "mentions_product": true|false
  }},
  "is_skip_response": true|false,
  "mentions_activity": true|false,
  "is_confirmation": true|false,
  "has_date_info": true|false,
  "is_partial_date": true|false,
  "partial_date_value": "string|null",
  "is_past_date": true|false,
  "is_new_trip": true|false,
  "next_question": "string|null",
  "ready_for_recommendations": true|false
}}

CRITICAL: 
- For TRAVEL intents with PARTIAL DATES (month only, duration only, vague timeframes): set is_partial_date: true, partial_date_value to the timeframe, and ready_for_recommendations: false. Ask for specific dates in assistant_message.
- For TRAVEL intents with COMPLETE DATES (specific start/end days, "tomorrow", "next Monday"): set is_partial_date: false and ready_for_recommendations: true
- NEVER ask for travel TIME (departure time, arrival time, hours). Only DATE matters.
- For NON-TRAVEL shopping: partial dates are acceptable, proceed to recommendations
- Size/color are OPTIONAL - do NOT require them to proceed
- If user says "no", "no preference", "skip", "any", "doesn't matter" to preference questions, set is_skip_response: true and ready_for_recommendations: true"""

# NOTE: Hardcoded activity lists removed - now handled by LLM semantic detection

def detect_intent_with_llm(query: str, llm) -> dict:
    """
    Use LLM to detect shopping intent, product mentions, and activities from user query.
    
    This replaces hardcoded keyword matching with intelligent LLM-based detection,
    allowing the system to understand natural language variations and context.
    
    Args:
        query: The user's message text
        llm: The LangChain LLM instance to use for detection
        
    Returns:
        Dictionary containing:
        - has_shopping_intent: bool - whether user wants to buy something
        - product_mentioned: str|None - the product type mentioned (e.g., "shoes", "jacket")
        - activity_mentioned: str|None - any activity mentioned (e.g., "hiking", "swimming")
        - is_affirmative: bool - whether this is a yes/confirmation response
        - is_negative: bool - whether this is a no/decline response
    """
    from langchain_core.messages import HumanMessage, SystemMessage
    
    detection_prompt = """You are an intent detection system for a shopping assistant.
Analyze the user's message semantically and extract:

1. **Shopping Intent**: Does the user express desire to buy, purchase, or acquire any product?
   Use semantic understanding - detect shopping intent from context, not just specific words.

2. **Product Mentioned**: What type of product is the user interested in?
   Return the general product category mentioned (clothing, footwear, accessories, etc.)
   Return null if no specific product is mentioned.

3. **Activity Mentioned**: What activity, event, or purpose is mentioned?
   Detect any activity, hobby, event, or occasion mentioned in context.
   Return null if no activity is mentioned.

4. **Response Type**: Is this an affirmative or negative response to a previous question?
   Detect confirmation or declination semantically from context.

5. **No Preference Response**: Is the user declining to specify a preference?
   Detect "no preference", "any", "doesn't matter", "skip", "no" as declining preference questions.

Respond ONLY with a JSON object (no markdown, no explanation):
{
  "has_shopping_intent": true/false,
  "product_mentioned": "product_type" or null,
  "activity_mentioned": "activity" or null,
  "is_affirmative": true/false,
  "is_negative": true/false,
  "is_no_preference": true/false
}"""

    try:
        messages = [
            SystemMessage(content=detection_prompt),
            HumanMessage(content=f"User message: {query}")
        ]
        response = llm.invoke(messages)
        result_text = response.content.strip()
        
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        
        raw_result = json.loads(result_text.strip())
        # Validate and normalize the result to ensure consistent structure
        result = validate_llm_intent_result(raw_result)
        print(f"[DEBUG] LLM intent detection result: {result}")
        return result
    except Exception as e:
        print(f"[DEBUG] LLM intent detection error: {e}, using default values")
        return {
            "has_shopping_intent": False,
            "product_mentioned": None,
            "activity_mentioned": None,
            "is_affirmative": False,
            "is_negative": False,
            "is_no_preference": False
        }


# NOTE: Hardcoded keyword sets removed - LLM handles all detection semantically


def validate_llm_intent_result(result: dict) -> dict:
    """
    Validate and normalize LLM intent detection result.
    
    Ensures all expected keys exist with correct types, providing safe defaults
    for missing or malformed values.
    
    Args:
        result: Raw result from LLM detection
        
    Returns:
        Normalized result dict with all required keys
    """
    if not isinstance(result, dict):
        return {
            "has_shopping_intent": False,
            "product_mentioned": None,
            "activity_mentioned": None,
            "is_affirmative": False,
            "is_negative": False,
            "is_no_preference": False
        }
    
    return {
        "has_shopping_intent": bool(result.get("has_shopping_intent", False)),
        "product_mentioned": result.get("product_mentioned") if isinstance(result.get("product_mentioned"), str) else None,
        "activity_mentioned": result.get("activity_mentioned") if isinstance(result.get("activity_mentioned"), str) else None,
        "is_affirmative": bool(result.get("is_affirmative", False)),
        "is_negative": bool(result.get("is_negative", False)),
        "is_no_preference": bool(result.get("is_no_preference", False))
    }


# NOTE: Hardcoded date phrases removed - LLM handles date ambiguity detection


# NOTE: All date detection functions removed - LLM detects dates semantically
# Only extract_month_from_text remains as a pure PARSING utility for combining date fragments

def extract_month_from_text(text: str) -> str:
    """Extract month name from text if present."""
    import re
    months = {
        "january": "January", "february": "February", "march": "March",
        "april": "April", "may": "May", "june": "June",
        "july": "July", "august": "August", "september": "September",
        "october": "October", "november": "November", "december": "December",
        "jan": "January", "feb": "February", "mar": "March", "apr": "April",
        "jun": "June", "jul": "July", "aug": "August", "sep": "September",
        "oct": "October", "nov": "November", "dec": "December"
    }
    text_lower = text.lower()
    for abbrev, full in months.items():
        if re.search(rf'\b{abbrev}\b', text_lower):
            return full
    return None


# NOTE: All keyword-based detection functions removed - LLM handles all intent detection semantically


class ClarifierAgent(BaseAgent):

    def __init__(self):
        super().__init__("Clarifier", CLARIFIER_PROMPT)

    def _generate_dynamic_question(self, question_type: str, query: str, intent: dict, extra_context: dict = None) -> str:
        """
        Generate contextual questions dynamically using LLM based on question type and context.
        
        Args:
            question_type: Type of question to generate (city, product, date, activity, etc.)
            query: The user's original message
            intent: Current merged intent with destination, dates, activities etc.
            extra_context: Additional context like country, month, activity name etc.
            
        Returns:
            A contextual, natural-sounding question
        """
        try:
            from langchain_core.messages import SystemMessage as SysMsg
            
            destination = intent.get("destination") or intent.get("destination_city") or ""
            activities = intent.get("activities") or []
            travel_date = intent.get("travel_date") or ""
            extra = extra_context or {}
            
            context_parts = []
            if destination:
                context_parts.append(f"destination: {destination}")
            if travel_date:
                context_parts.append(f"travel date: {travel_date}")
            if activities:
                context_parts.append(f"activities: {', '.join(activities)}")
            for key, val in extra.items():
                if val:
                    context_parts.append(f"{key}: {val}")
            
            context_str = "; ".join(context_parts) if context_parts else "no specific context yet"
            
            prompts = {
                "city": f"""Generate a SHORT, friendly question (max 12 words) asking which city the user is traveling to.
The user mentioned a country but not a specific city.
Context: {context_str}
User said: "{query}"
Return ONLY the question.""",

                "destination": f"""Generate a SHORT, friendly question (max 12 words) asking where the user would like to travel.
The user hasn't mentioned a destination yet.
Context: {context_str}
User said: "{query}"
Return ONLY the question.""",

                "product": f"""Generate a SHORT, friendly question (max 15 words) asking what specific products the user is looking for.
The user wants to shop but didn't specify what products.
Context: {context_str}
User said: "{query}"
Do NOT suggest products. Just ask what they need.
Return ONLY the question.""",

                "date": f"""Generate a SHORT, friendly question (max 15 words) asking when the user is planning to travel.
The user has a destination but hasn't mentioned travel dates.
Context: {context_str}
User said: "{query}"
Return ONLY the question.""",

                "specific_date": f"""Generate a SHORT, friendly question (max 15 words) asking for specific travel dates.
The user mentioned a month but not specific days.
Context: {context_str}
User said: "{query}"
Return ONLY the question.""",

                "activity": f"""Generate a SHORT, friendly question (max 15 words) asking what activities the user is planning.
Context: {context_str}
User said: "{query}"
Return ONLY the question.""",

                "shopping_offer": f"""Generate a SHORT, friendly question (max 15 words) asking if the user would like product recommendations for their activity.
Context: {context_str}
User said: "{query}"
Return ONLY the question.""",

                "ambiguous_intent": f"""Generate a SHORT, friendly question (max 15 words) clarifying if the user wants to buy something or is asking about an activity.
Context: {context_str}
User said: "{query}"
Return ONLY the question.""",

                "proceed_message": f"""Generate a SHORT, friendly confirmation (max 12 words) that you'll find product recommendations.
Context: {context_str}
User said: "{query}"
Return ONLY the confirmation, no question mark.""",

                "decline_shopping": f"""Generate a SHORT, friendly response (max 20 words) acknowledging the user doesn't want to shop and wishing them well.
Context: {context_str}
User said: "{query}"
Return ONLY the response.""",

                "invalid_date": f"""Generate a SHORT, friendly response (max 25 words) explaining that the date provided doesn't exist on the calendar and asking for a valid date.
Context: {context_str}
Reason the date is invalid: {extra.get('reason', 'The date does not exist on the calendar')}
User said: "{query}"
Be helpful and explain why the date is invalid (e.g., February only has 28 or 29 days).
Return ONLY the response asking for a valid date."""
            }
            
            prompt = prompts.get(question_type)
            if not prompt:
                print(f"[DEBUG] Unknown question type: {question_type}")
                return None
            
            messages = [SysMsg(content=prompt)]
            response = self.llm.invoke(messages)
            result = response.content.strip().strip('"\'')
            
            # Validate response is reasonable
            if result and len(result) > 5 and len(result) < 250:
                return result
            else:
                print(f"[DEBUG] Dynamic question generation returned invalid response for {question_type}")
                return None
                
        except Exception as e:
            print(f"[DEBUG] Error generating dynamic question ({question_type}): {e}")
            return None

    def _generate_dynamic_product_question(self, query: str, intent: dict) -> str:
        """Generate contextual product question - wrapper for backwards compatibility."""
        result = self._generate_dynamic_question("product", query, intent)
        if result:
            return result
        destination = intent.get("destination") or ""
        return self._generate_dynamic_question("product", query, intent) or ""

    def _parse_date_from_query(self, query: str, existing_context: dict, conversation_history: list = None) -> dict:
        """
        Use LLM to dynamically parse date information from query and context.
        Handles partial dates, date ranges, and combining fragments from conversation.
        
        Returns dict with:
            - has_complete_date: bool - whether a complete date was found
            - parsed_date: str - the parsed/combined date string
            - needs_more_info: bool - whether more date info is needed
        """
        try:
            from langchain_core.messages import SystemMessage as SysMsg
            
            # Gather context
            existing_travel_date = existing_context.get("travel_date") or ""
            existing_month = existing_context.get("_pending_month") or ""
            destination = existing_context.get("destination") or ""
            
            # Get recent conversation for context
            conv_context = ""
            if conversation_history:
                recent = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
                for msg in recent:
                    if isinstance(msg, dict):
                        conv_context += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"
                    else:
                        conv_context += f"{msg}\n"
            
            # Get current year for leap year validation
            from datetime import datetime
            current_year = datetime.now().year
            next_year = current_year + 1
            
            prompt = f"""Parse date information from the user's message and validate it against the calendar.

User message: "{query}"
Existing travel date: "{existing_travel_date}"
Previously mentioned month: "{existing_month}"
Destination: "{destination}"
Current year: {current_year}

Recent conversation:
{conv_context}

IMPORTANT: Validate that dates are real calendar dates!
- February has 28 days (29 in leap years: {current_year} is {"a leap year" if current_year % 4 == 0 and (current_year % 100 != 0 or current_year % 400 == 0) else "not a leap year"}, {next_year} is {"a leap year" if next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0) else "not a leap year"})
- April, June, September, November have 30 days
- January, March, May, July, August, October, December have 31 days
- There is NO February 29 in non-leap years, NO February 30, NO February 31, etc.

Analyze and return a JSON object:
{{
    "has_complete_date": true/false,  // true if we have a valid complete date
    "parsed_date": "string",  // The complete or partial date (e.g., "January 19-20", "March 5", "next week")
    "month_only": "string or null",  // If only a month was mentioned without days
    "needs_more_info": true/false,  // true if we need specific days for a month
    "is_invalid_date": true/false,  // true if the date doesn't exist on the calendar (e.g., Feb 30, Feb 31, April 31)
    "invalid_date_reason": "string or null"  // Explanation if date is invalid (e.g., "February only has 28 days in 2026")
}}

Examples:
- Query "Feb 30" -> {{"has_complete_date": false, "parsed_date": "", "month_only": null, "needs_more_info": false, "is_invalid_date": true, "invalid_date_reason": "February only has 28 days"}}
- Query "Feb 29" in non-leap year -> {{"has_complete_date": false, "parsed_date": "", "month_only": null, "needs_more_info": false, "is_invalid_date": true, "invalid_date_reason": "February 29 only exists in leap years, and {next_year} is not a leap year"}}
- Query "April 31" -> {{"has_complete_date": false, "parsed_date": "", "month_only": null, "needs_more_info": false, "is_invalid_date": true, "invalid_date_reason": "April only has 30 days"}}
- Query "Jan 19th" -> {{"has_complete_date": true, "parsed_date": "January 19", "month_only": null, "needs_more_info": false, "is_invalid_date": false, "invalid_date_reason": null}}

Return ONLY the JSON object."""

            messages = [SysMsg(content=prompt)]
            response = self.llm.invoke(messages)
            result = response.content.strip()
            
            import json
            try:
                parsed = json.loads(result)
                return parsed
            except json.JSONDecodeError:
                import re
                match = re.search(r'\{.*?\}', result, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group())
                        return parsed
                    except:
                        pass
            
            return {"has_complete_date": False, "parsed_date": "", "needs_more_info": True}
        except Exception as e:
            print(f"[DEBUG] Error parsing date: {e}")
            return {"has_complete_date": False, "parsed_date": "", "needs_more_info": True}

    def _filter_specific_activities(self, activities: list) -> list:
        """
        Use LLM to dynamically filter out generic travel words and keep only specific activities.
        Returns only activities that represent actual things to do (like hiking, skiing, sightseeing).
        """
        if not activities:
            return []
        
        try:
            from langchain_core.messages import SystemMessage as SysMsg
            
            prompt = f"""Analyze this list of activities and return ONLY the specific, actionable activities.

Activities: {activities}

REMOVE generic travel words like: travel, travelling, traveling, trip, vacation, holiday, visit, visiting, going, journey, tour, etc.
KEEP specific activities like: hiking, skiing, sightseeing, beach, swimming, shopping, dining, photography, etc.

Return a JSON array of ONLY the specific activities. If none are specific, return [].
Example input: ["traveling", "hiking", "vacation", "skiing"]
Example output: ["hiking", "skiing"]

Return ONLY the JSON array, nothing else."""

            messages = [SysMsg(content=prompt)]
            response = self.llm.invoke(messages)
            result = response.content.strip()
            
            # Parse the JSON array
            import json
            try:
                specific = json.loads(result)
                if isinstance(specific, list):
                    return specific
            except json.JSONDecodeError:
                # Try to extract array from response
                import re
                match = re.search(r'\[.*?\]', result, re.DOTALL)
                if match:
                    try:
                        specific = json.loads(match.group())
                        if isinstance(specific, list):
                            return specific
                    except:
                        pass
            
            return []
        except Exception as e:
            print(f"[DEBUG] Error filtering activities: {e}")
            return []

    def _detect_changes(self, existing_intent: dict, new_intent: dict,
                        merged_intent: dict) -> dict:
        """Detect modifications to destination, dates, and activities."""
        changes = {
            "has_changes": False,
            "destination_changed": False,
            "dates_changed": False,
            "activities_changed": False,
            "changes": []
        }

        old_destination = existing_intent.get("destination")
        new_destination = new_intent.get("destination") or merged_intent.get(
            "destination")
        if old_destination and new_destination and old_destination.lower(
        ) != new_destination.lower():
            changes["has_changes"] = True
            changes["destination_changed"] = True
            changes["changes"].append({
                "field": "destination",
                "old_value": old_destination,
                "new_value": new_destination
            })

        old_dates = existing_intent.get("travel_date")
        new_dates = new_intent.get("travel_date") or merged_intent.get(
            "travel_date")
        if old_dates and new_dates and old_dates != new_dates:
            changes["has_changes"] = True
            changes["dates_changed"] = True
            changes["changes"].append({
                "field": "travel_date",
                "old_value": old_dates,
                "new_value": new_dates
            })

        old_activities = set(existing_intent.get("activities") or [])
        new_activities_raw = new_intent.get("activities") or merged_intent.get(
            "activities") or []
        new_activities = set(new_activities_raw)

        if old_activities or new_activities:
            removed = old_activities - new_activities if old_activities else set(
            )
            added = new_activities - old_activities if new_activities else set(
            )

            if removed or added:
                changes["has_changes"] = True
                changes["activities_changed"] = True
                changes["changes"].append({
                    "field": "activities",
                    "type": "modified",
                    "old_value": list(old_activities),
                    "new_value": list(new_activities),
                    "removed": list(removed),
                    "added": list(added)
                })

        return changes

    def _generate_change_acknowledgment(self, changes: dict) -> str:
        """Generate a user-friendly acknowledgment message for detected changes."""
        if not changes["has_changes"]:
            return ""

        messages = []
        for change in changes["changes"]:
            field = change["field"]
            if field == "destination":
                messages.append(
                    f"I've updated your destination from {change['old_value']} to {change['new_value']}"
                )
            elif field == "travel_date":
                messages.append(
                    f"I've updated your travel dates from {change['old_value']} to {change['new_value']}"
                )
            elif field == "activities":
                if change.get("removed"):
                    messages.append(
                        f"I've updated your activities (removed: {', '.join(change['removed'])}; added: {', '.join(change.get('added', []))})"
                    )
                else:
                    messages.append(
                        f"I've updated your activities to include: {', '.join(change.get('added', []))}"
                    )

        return ". ".join(messages) + ". " if messages else ""

    def _extract_brand_fallback(self, query: str) -> str:
        """Extract brand name from user query - now handled by LLM."""
        # Brand extraction now handled by LLM semantic detection
        return None

    def _extract_activities_fallback(self, query: str) -> list:
        """Extract activities from user query - now handled by LLM."""
        # Activity extraction now handled by LLM semantic detection
        return []

    def analyze(self,
                query: str,
                conversation_history: list = None,
                existing_intent: dict = None) -> dict:
        current_date = get_current_date()
        existing_intent = existing_intent or {}
        conversation_history = conversation_history or []

        existing_destination = existing_intent.get("destination")

        context = ""
        if conversation_history:
            context = f"\nConversation history: {json.dumps(conversation_history[-5:])}"

        existing_intent_str = ""
        if existing_intent:
            filled_fields = {
                k: v
                for k, v in existing_intent.items() if v is not None
            }
            if filled_fields:
                existing_intent_str = f"\n\nALREADY COLLECTED INFORMATION (DO NOT ask for these again):\n{json.dumps(filled_fields, indent=2)}"

        prompt = f"""Today's date: {current_date}

User query: {query}{context}{existing_intent_str}

IMPORTANT: If information was already collected (shown above), preserve it in updated_intent and DO NOT ask for it again.
Only ask for MISSING information that hasn't been collected yet.

Extract travel intent and respond with the JSON structure. If key details are missing (destination, travel_date), ask ONE clarifying question."""

        system_prompt = CLARIFIER_PROMPT.replace("{CURRENT_DATE}",
                                                 current_date)

        response = self.invoke(prompt, system_override=system_prompt)
        print(f"[DEBUG] Raw clarifier response: {response}")
        try:
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]

            clean_response = clean_response.replace("{{",
                                                    "{").replace("}}", "}")

            result = json.loads(clean_response.strip())
            print(f"[DEBUG] Clarifier response: {result}")
            new_intent = result.get("updated_intent", {})
            merged_intent = self._merge_intent(existing_intent or {},
                                               new_intent)

            detected_changes = self._detect_changes(existing_intent or {},
                                                    new_intent, merged_intent)
            change_acknowledgment = self._generate_change_acknowledgment(
                detected_changes)

            if detected_changes["has_changes"]:
                merged_intent["_context_refresh_needed"] = True
                if detected_changes["destination_changed"]:
                    merged_intent["_asked_optional"] = False
                    merged_intent["_asked_activities"] = False
                print(
                    f"[DEBUG] Detected changes: {detected_changes['changes']}")

            # Use LLM-detected date info signal for date parsing
            llm_detected_date = result.get("has_date_info", False)

            # Only auto-parse dates if LLM detected date info
            if not merged_intent.get("travel_date") and llm_detected_date:
                parsed_date = parse_relative_date(query, datetime.now())
                if parsed_date:
                    merged_intent["travel_date"] = parsed_date
                    print(
                        f"[DEBUG] Parsed date from query: {parsed_date}"
                    )

            country_only = new_intent.get("country_only", False)
            destination_country = new_intent.get("destination_country")
            destination_city = new_intent.get("destination_city")

            if country_only and destination_country and not destination_city and not existing_destination:
                city_question = self._generate_dynamic_question("city", query, merged_intent, {"country": destination_country})
                if not city_question:
                    city_question = f"Which city are you travelling to in {destination_country}?"
                merged_intent["_pending_country"] = destination_country
                return {
                    "needs_clarification":
                    True,
                    "clarification_question":
                    city_question,
                    "assistant_message":
                    change_acknowledgment +
                    city_question if change_acknowledgment else city_question,
                    "updated_intent":
                    merged_intent,
                    "clarified_query":
                    query,
                    "ready_for_recommendations":
                    False,
                    "detected_changes":
                    detected_changes
                }

            if destination_city and destination_city != existing_destination:
                existing_intent["_asked_optional"] = False

            ready_for_recs = result.get("ready_for_recommendations", False)
            has_destination = merged_intent.get("destination")
            trip_segments = merged_intent.get("trip_segments") or []
            has_date = merged_intent.get("travel_date") or (len(trip_segments)
                                                            > 0)
            has_required = has_destination and has_date
            
            # DYNAMIC MODE: Trust LLM's ready_for_recommendations decision
            # This enables the dynamic, model-driven approach - no hardcoded rules
            mentions_product = new_intent.get("mentions_product", False) or result.get("updated_intent", {}).get("mentions_product", False)
            is_skip = result.get("is_skip_response", False)
            
            # Track already_asked flags
            already_asked_optional = existing_intent.get("_asked_optional", False)
            already_asked_activities = existing_intent.get("_asked_activities", False)
            
            # Check last question type to determine if skip applies to optional preferences
            last_question_type = existing_intent.get("_last_question_type", "")
            was_optional_question = last_question_type in ("optional", "preference", "budget_brand", "size_color")
            
            # UNIFIED SKIP HANDLING - applies when user is declining OPTIONAL preferences
            if is_skip:
                # Always clear size preferences when user says no preference
                merged_intent["preferred_size"] = None
                print(f"[DEBUG] is_skip=True: Cleared preferred_size")
                
                # PRIMARY GATE: Trust LLM's explicit decision
                # If clarifier LLM says BOTH is_skip_response=true AND ready_for_recommendations=true,
                # it determined user is declining preferences AND we have enough info - proceed
                if ready_for_recs:
                    base_message = result.get("assistant_message", "Perfect! Let me find products for you.")
                    print(f"[DEBUG] is_skip + ready_for_recs: LLM explicit proceed")
                    return {
                        "needs_clarification": False,
                        "clarification_question": "",
                        "assistant_message": change_acknowledgment + base_message if change_acknowledgment else base_message,
                        "updated_intent": merged_intent,
                        "clarified_query": query,
                        "ready_for_recommendations": True,
                        "detected_changes": detected_changes
                    }
                
                # SECONDARY GATE: Check for established context
                has_shopping_context = (
                    existing_intent.get("_shopping_flow_complete") or
                    existing_intent.get("notes") or
                    merged_intent.get("notes") or
                    existing_intent.get("_product_category_received") or
                    existing_intent.get("_confirmed_shopping")
                )
                
                if was_optional_question or already_asked_optional or already_asked_activities or has_shopping_context:
                    base_message = result.get("assistant_message", "Perfect! Let me find products for you.")
                    print(f"[DEBUG] is_skip + context: Proceeding to recommendations")
                    return {
                        "needs_clarification": False,
                        "clarification_question": "",
                        "assistant_message": change_acknowledgment + base_message if change_acknowledgment else base_message,
                        "updated_intent": merged_intent,
                        "clarified_query": query,
                        "ready_for_recommendations": True,
                        "detected_changes": detected_changes
                    }
                # Otherwise, "no" may be answering a critical question - continue flow
            
            # Trust LLM when it says ready_for_recommendations AND has product mention
            if ready_for_recs and mentions_product:
                # LLM determined we have enough info - trust it and proceed
                print(f"[DEBUG] Dynamic mode: LLM ready_for_recommendations=True with product mention, proceeding")
                base_message = result.get("assistant_message", "Let me find the best products for you!")
                return {
                    "needs_clarification": False,
                    "clarification_question": "",
                    "assistant_message": change_acknowledgment + base_message if change_acknowledgment else base_message,
                    "updated_intent": merged_intent,
                    "clarified_query": query,
                    "ready_for_recommendations": True,
                    "detected_changes": detected_changes
                }

            # Update already_asked flags from merged_intent as well
            already_asked_optional = already_asked_optional or merged_intent.get("_asked_optional", False)
            already_asked_activities = already_asked_activities or merged_intent.get("_asked_activities", False)
            
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

            if new_activities and isinstance(new_activities,
                                             list) and len(new_activities) > 0:
                mentions_activity = True

            # Fallback brand extraction - check if user mentioned a brand
            fallback_brand = self._extract_brand_fallback(query)
            if fallback_brand and not merged_intent.get("preferred_brand"):
                merged_intent["preferred_brand"] = fallback_brand
                print(f"[DEBUG] Extracted brand from query: {fallback_brand}")

            # Check for budget or brand AFTER fallback extraction
            has_budget_or_brand = (merged_intent.get("budget_amount")
                                   or merged_intent.get("preferred_brand"))

            is_new_trip = result.get("is_new_trip", False)
            if is_new_trip:
                existing_intent["_asked_optional"] = False
                existing_intent["_asked_activities"] = False

            # Use LLM signal for date detection - pure LLM-driven
            llm_has_date_info = result.get("has_date_info", False)
            
            # Date PARSING using LLM: dynamically parse and combine date fragments from context
            # E.g., user said "January" in previous message, now says "19-20" - combine them
            if llm_has_date_info:
                # Use LLM-based date parsing instead of hardcoded regex patterns
                date_context = {
                    "travel_date": existing_intent.get("travel_date") or merged_intent.get("travel_date") or "",
                    "_pending_month": existing_intent.get("_pending_month") or merged_intent.get("_pending_month") or "",
                    "destination": merged_intent.get("destination") or "",
                    "notes": existing_intent.get("notes") or merged_intent.get("notes") or ""
                }
                
                date_result = self._parse_date_from_query(query, date_context, conversation_history)
                
                # Handle invalid calendar dates (e.g., Feb 30, Feb 29 in non-leap year)
                if date_result.get("is_invalid_date"):
                    invalid_reason = date_result.get("invalid_date_reason") or "That date doesn't exist on the calendar."
                    dest = merged_intent.get("destination", "your destination")
                    
                    # Generate dynamic message for invalid date
                    invalid_date_message = self._generate_dynamic_question("invalid_date", query, merged_intent, {"reason": invalid_reason})
                    if not invalid_date_message:
                        invalid_date_message = f"{invalid_reason} Please provide a valid date for your trip to {dest}."
                    
                    print(f"[DEBUG] Invalid calendar date detected: {invalid_reason}")
                    
                    return {
                        "needs_clarification": True,
                        "clarification_question": invalid_date_message,
                        "assistant_message": invalid_date_message,
                        "updated_intent": merged_intent,
                        "clarified_query": query,
                        "ready_for_recommendations": False,
                        "detected_changes": detected_changes
                    }
                elif date_result.get("has_complete_date") and date_result.get("parsed_date"):
                    merged_intent["travel_date"] = date_result["parsed_date"]
                    print(f"[DEBUG] LLM parsed date: {date_result['parsed_date']}")
                    has_date = True
                elif date_result.get("month_only"):
                    # Store month for later combination with days
                    merged_intent["_pending_month"] = date_result["month_only"]
                    merged_intent["_has_partial_date"] = True
                    print(f"[DEBUG] LLM detected partial date (month only): {date_result['month_only']}")
            
            # Recalculate has_date and has_required after date parsing
            # This ensures parsed dates from patterns are properly recognized
            has_date = merged_intent.get("travel_date") or (len(trip_segments) > 0)
            has_required = has_destination and has_date
            
            # Decision uses LLM signal only
            has_dates_info = has_date or llm_has_date_info
            
            # Handle PAST DATE detection - block and ask for future dates
            is_past_date = result.get("is_past_date", False)
            if is_past_date and has_destination:
                dest = merged_intent.get("destination", "your destination")
                
                # Use LLM's message if it mentions past dates, otherwise generate
                llm_message = result.get("assistant_message", "")
                if "past" in llm_message.lower() or "passed" in llm_message.lower() or "already" in llm_message.lower():
                    past_date_message = llm_message
                else:
                    past_date_message = f"Those dates have already passed. Could you please provide future travel dates for your trip to {dest}?"
                
                # Clear the invalid date
                merged_intent["travel_date"] = None
                merged_intent["_has_partial_date"] = False
                
                return {
                    "needs_clarification": True,
                    "clarification_question": past_date_message,
                    "assistant_message": past_date_message,
                    "updated_intent": merged_intent,
                    "clarified_query": query,
                    "ready_for_recommendations": False,
                    "detected_changes": detected_changes
                }
            
            # Handle PARTIAL DATE detection for travel intents
            is_partial_date = result.get("is_partial_date", False)
            partial_date_value = result.get("partial_date_value")
            
            # Store partial date info for later use
            if is_partial_date and partial_date_value:
                merged_intent["_pending_month"] = partial_date_value
                merged_intent["_has_partial_date"] = True
                print(f"[DEBUG] Partial date detected: {partial_date_value}")
            
            # If destination + partial date (travel context), ask for specific dates
            if has_destination and is_partial_date and not existing_intent.get("_asked_specific_dates"):
                partial_info = partial_date_value or "your timeframe"
                
                # Use LLM's assistant_message if it's asking for dates, otherwise generate dynamically
                llm_message = result.get("assistant_message", "")
                if "date" in llm_message.lower() or "when" in llm_message.lower():
                    date_question = llm_message
                else:
                    date_question = self._generate_dynamic_question("specific_date", query, merged_intent, {"month": partial_info}) or result.get("next_question") or llm_message
                
                merged_intent["_asked_specific_dates"] = True
                return {
                    "needs_clarification": True,
                    "clarification_question": date_question,
                    "assistant_message": change_acknowledgment + date_question if change_acknowledgment else date_question,
                    "updated_intent": merged_intent,
                    "clarified_query": query,
                    "ready_for_recommendations": False,
                    "detected_changes": detected_changes
                }

            # EARLY SHOPPING/ACTIVITY DETECTION using LLM (runs BEFORE destination/date checks)
            # Skip detection if we're waiting for a product category answer
            already_asked_product_category = existing_intent.get(
                "_asked_product_category", False)

            if already_asked_product_category and not existing_intent.get(
                    "_product_category_received", False):
                # User is answering what products they want - capture and proceed
                merged_intent["_product_category_received"] = True
                merged_intent["_shopping_flow_complete"] = True
                merged_intent["notes"] = query if not merged_intent.get(
                    "notes") else f"{merged_intent.get('notes')}; {query}"
                # Skip shopping/activity detection for this response
                direct_shopping_intent = False
                direct_non_shopping_activity = None
                llm_intent_result = None
            else:
                # Use LLM-based intent detection (fully dynamic, no keyword fallback)
                llm_intent_result = detect_intent_with_llm(query, self.llm)
                
                # Extract LLM results - pure LLM-driven detection
                direct_shopping_intent = llm_intent_result.get("has_shopping_intent", False)
                
                # Check for "no preference" responses from intent detection LLM
                llm_no_preference = llm_intent_result.get("is_no_preference", False)
                if llm_no_preference:
                    print(f"[DEBUG] LLM detected 'no preference' response")
                    # Clear size preferences
                    merged_intent["preferred_size"] = None
                    
                    # Check for shopping context
                    has_shop_ctx = (
                        existing_intent.get("_shopping_flow_complete") or
                        existing_intent.get("notes") or
                        merged_intent.get("notes") or
                        existing_intent.get("_product_category_received") or
                        existing_intent.get("_confirmed_shopping")
                    )
                    prior_pref = already_asked_optional or already_asked_activities
                    
                    # Proceed if we have established context (shopping or travel preference questions asked)
                    if was_optional_question or prior_pref or has_shop_ctx:
                        base_message = "Perfect! Let me find the best products for you."
                        print(f"[DEBUG] llm_no_preference + context: Proceeding to recommendations")
                        return {
                            "needs_clarification": False,
                            "clarification_question": "",
                            "assistant_message": change_acknowledgment + base_message if change_acknowledgment else base_message,
                            "updated_intent": merged_intent,
                            "clarified_query": query,
                            "ready_for_recommendations": True,
                            "detected_changes": detected_changes
                        }
                    # If no context, continue to gather critical info
                
                # Activity detection from LLM only
                llm_activity = llm_intent_result.get("activity_mentioned")
                
                # Map activity to non-shopping based on LLM signals
                # If has_shopping_intent is true, the activity is shopping-related
                # Otherwise, it's a non-shopping activity
                if llm_activity and not direct_shopping_intent:
                    direct_non_shopping_activity = llm_activity.lower()
                else:
                    direct_non_shopping_activity = None

            # Handle shopping confirmation response (yes/no to "Would you like to shop for activity?")
            awaiting_shopping_confirm = existing_intent.get(
                "_awaiting_shopping_confirm", False)
            if awaiting_shopping_confirm:
                # Use LLM result only - pure LLM-driven detection
                product_in_confirmation = llm_intent_result.get("product_mentioned") if llm_intent_result else None
                
                # LLM-based affirmative/negative detection
                is_user_affirmative = llm_intent_result.get("is_affirmative", False) if llm_intent_result else False
                is_user_negative = llm_intent_result.get("is_negative", False) if llm_intent_result else False
                
                if is_user_affirmative or product_in_confirmation:
                    merged_intent["_awaiting_shopping_confirm"] = False
                    merged_intent["_confirmed_shopping"] = True
                    
                    # If user mentioned a product (e.g., "yes, like to buy shoes"), capture it and proceed
                    if product_in_confirmation:
                        merged_intent["_asked_product_category"] = True
                        merged_intent["_product_category_received"] = True
                        merged_intent["_shopping_flow_complete"] = True
                        merged_intent["notes"] = product_in_confirmation if not merged_intent.get(
                            "notes") else f"{merged_intent.get('notes')}; {product_in_confirmation}"
                        # Proceed to recommendations with the product
                        activity_name = existing_intent.get("_pending_activity", "your trip")
                        proceed_message = self._generate_dynamic_question("proceed_message", query, merged_intent, {"product": product_in_confirmation, "activity": activity_name})
                        if not proceed_message:
                            proceed_message = f"Great! I'll find {product_in_confirmation} recommendations for {activity_name}."
                        return {
                            "needs_clarification": False,
                            "clarification_question": None,
                            "assistant_message": change_acknowledgment + proceed_message if change_acknowledgment else proceed_message,
                            "updated_intent": merged_intent,
                            "clarified_query": query,
                            "ready_for_recommendations": True,
                            "detected_changes": detected_changes
                        }
                    else:
                        # Just "yes" without a product - ask what they want to buy
                        merged_intent["_asked_product_category"] = True
                        product_question = self._generate_dynamic_question("product", query, merged_intent) or result.get("assistant_message") or result.get("next_question")
                        return {
                            "needs_clarification": True,
                            "clarification_question": product_question,
                            "assistant_message": change_acknowledgment + product_question if change_acknowledgment else product_question,
                            "updated_intent": merged_intent,
                            "clarified_query": query,
                            "ready_for_recommendations": False,
                            "detected_changes": detected_changes
                        }
                elif is_user_negative:
                    merged_intent["_awaiting_shopping_confirm"] = False
                    merged_intent["_declined_shopping"] = True
                    activity_name = existing_intent.get(
                        "_pending_activity", "your activity")
                    tip_message = self._generate_dynamic_question("decline_shopping", query, merged_intent, {"activity": activity_name})
                    if not tip_message:
                        tip_message = f"No problem! Enjoy your {activity_name}!"
                    return {
                        "needs_clarification":
                        False,
                        "clarification_question":
                        "",
                        "assistant_message":
                        change_acknowledgment +
                        tip_message if change_acknowledgment else tip_message,
                        "updated_intent":
                        merged_intent,
                        "clarified_query":
                        query,
                        "ready_for_recommendations":
                        False,
                        "detected_changes":
                        detected_changes
                    }

            # Handle direct shopping intent from query (e.g., "I want to buy shoes")
            # Check if user mentioned a specific product using LLM only
            product_mention = llm_intent_result.get("product_mentioned") if llm_intent_result else None
            
            if direct_shopping_intent and not existing_intent.get(
                    "_asked_product_category", False):
                # Add shopping to activities if not present
                current_activities = merged_intent.get("activities", []) or []
                if "shopping" not in current_activities:
                    current_activities.append("shopping")
                    merged_intent["activities"] = current_activities

                merged_intent["_asked_product_category"] = True
                merged_intent["_asked_activities"] = True
                
                # If user already mentioned a product, don't ask - mark complete and continue
                if product_mention:
                    merged_intent["_shopping_flow_complete"] = True
                    merged_intent["notes"] = f"Looking for {product_mention}" if not merged_intent.get("notes") else f"{merged_intent.get('notes')}; Looking for {product_mention}"
                    print(f"[DEBUG] Product already mentioned: {product_mention} - skipping product question")
                    # Don't return - let the flow continue to ask destination/date if needed
                else:
                    # No product mentioned, ask what they want (use LLM to generate dynamic question)
                    product_question = self._generate_dynamic_product_question(query, merged_intent)
                    return {
                        "needs_clarification":
                        True,
                        "clarification_question":
                        product_question,
                        "assistant_message":
                        change_acknowledgment + product_question
                        if change_acknowledgment else product_question,
                        "updated_intent":
                        merged_intent,
                        "clarified_query":
                        query,
                        "ready_for_recommendations":
                        False,
                        "detected_changes":
                        detected_changes
                    }

            # Handle direct non-shopping activity from query (e.g., "planning a hiking trip")
            # This runs regardless of destination/date status
            if direct_non_shopping_activity and not direct_shopping_intent:
                if not existing_intent.get("_asked_shopping_for_activity",
                                           False):
                    # Add the activity to activities list
                    current_activities = merged_intent.get("activities",
                                                           []) or []
                    if direct_non_shopping_activity not in current_activities:
                        current_activities.append(direct_non_shopping_activity)
                        merged_intent["activities"] = current_activities

                    merged_intent["_asked_shopping_for_activity"] = True
                    merged_intent["_awaiting_shopping_confirm"] = True
                    merged_intent["_pending_activity"] = direct_non_shopping_activity
                    merged_intent["_asked_activities"] = True
                    shopping_question = self._generate_dynamic_question("shopping_offer", query, merged_intent, {"activity": direct_non_shopping_activity}) or result.get("assistant_message") or result.get("next_question")
                    return {
                        "needs_clarification": True,
                        "clarification_question": shopping_question,
                        "assistant_message": change_acknowledgment + shopping_question if change_acknowledgment else shopping_question,
                        "updated_intent": merged_intent,
                        "clarified_query": query,
                        "ready_for_recommendations": False,
                        "detected_changes": detected_changes
                    }

            # Handle ambiguous intent - neither shopping nor activity detected
            # Only ask if we haven't already asked and user hasn't provided clear context
            # NOTE: product_mention already detected earlier (before shopping intent handling)
            # If product was mentioned but we didn't go through shopping flow, set it up now
            if product_mention and not merged_intent.get("_shopping_flow_complete"):
                # User mentioned a specific product - treat as shopping intent
                direct_shopping_intent = True
                merged_intent["_shopping_flow_complete"] = True
                if not merged_intent.get("notes") or product_mention not in str(merged_intent.get("notes", "")):
                    merged_intent["notes"] = f"Looking for {product_mention}" if not merged_intent.get("notes") else f"{merged_intent.get('notes')}; Looking for {product_mention}"
                print(f"[DEBUG] Late product mention detection: {product_mention} - treating as shopping intent")
            
            if not direct_shopping_intent and not direct_non_shopping_activity:
                if not existing_intent.get("_asked_ambiguous_intent", False):
                    # Check if we have enough context already (destination, activities, etc.)
                    has_any_context = (
                        has_destination or merged_intent.get("activities")
                        or existing_intent.get("_asked_activities", False) or
                        existing_intent.get("_shopping_flow_complete", False)
                        or existing_intent.get("_declined_shopping", False)
                        or is_skip or result.get("is_confirmation", False)
                        or product_mention)  # Product mention counts as context

                    if not has_any_context and len(query.strip()) > 3:
                        merged_intent["_asked_ambiguous_intent"] = True
                        ambiguous_question = self._generate_dynamic_question("ambiguous_intent", query, merged_intent) or result.get("assistant_message") or result.get("next_question")
                        return {
                            "needs_clarification":
                            True,
                            "clarification_question":
                            ambiguous_question,
                            "assistant_message":
                            change_acknowledgment + ambiguous_question
                            if change_acknowledgment else ambiguous_question,
                            "updated_intent":
                            merged_intent,
                            "clarified_query":
                            query,
                            "ready_for_recommendations":
                            False,
                            "detected_changes":
                            detected_changes
                        }

            if has_destination and not has_dates_info:
                date_question = self._generate_dynamic_question("date", query, merged_intent) or result.get("assistant_message") or result.get("next_question")
                return {
                    "needs_clarification":
                    True,
                    "clarification_question":
                    date_question,
                    "assistant_message":
                    change_acknowledgment +
                    date_question if change_acknowledgment else date_question,
                    "updated_intent":
                    merged_intent,
                    "clarified_query":
                    query,
                    "ready_for_recommendations":
                    False,
                    "detected_changes":
                    detected_changes
                }
            
            # Check for partial date (month only) - ask for specific days
            pending_month = merged_intent.get("_pending_month") or existing_intent.get("_pending_month")
            # has_complete_date is true if we have an actual date (not just partial)
            has_partial_flag = merged_intent.get("_has_partial_date", False) or existing_intent.get("_has_partial_date", False)
            has_complete_date = has_date or (merged_intent.get("travel_date") and not has_partial_flag)
            
            if has_destination and pending_month and not has_complete_date and not existing_intent.get("_asked_specific_dates"):
                # Ask for specific dates while acknowledging the month - use dynamic generation
                date_question = self._generate_dynamic_question("specific_date", query, merged_intent, {"month": pending_month}) or result.get("assistant_message") or result.get("next_question")
                merged_intent["_asked_specific_dates"] = True
                return {
                    "needs_clarification":
                    True,
                    "clarification_question":
                    date_question,
                    "assistant_message":
                    change_acknowledgment +
                    date_question if change_acknowledgment else date_question,
                    "updated_intent":
                    merged_intent,
                    "clarified_query":
                    query,
                    "ready_for_recommendations":
                    False,
                    "detected_changes":
                    detected_changes
                }

            # 1. Ask Activities if missing (only if shopping flow wasn't triggered earlier)
            shopping_flow_complete = merged_intent.get(
                "_shopping_flow_complete", False) or existing_intent.get(
                    "_shopping_flow_complete", False)
            declined_shopping = merged_intent.get(
                "_declined_shopping", False) or existing_intent.get(
                    "_declined_shopping", False)

            if has_destination and has_dates_info and not already_asked_activities and not shopping_flow_complete and not declined_shopping:
                # Check if specific activities were captured (not just mentions_activity flag)
                # Use LLM to dynamically filter out generic travel words
                captured_activities = merged_intent.get(
                    "activities") or existing_intent.get("activities") or []
                specific_activities = self._filter_specific_activities(captured_activities)
                has_specific_activities = len(specific_activities) > 0

                if has_specific_activities:
                    merged_intent["_asked_activities"] = True
                    # Activities already captured by early detection, continue to optional
                else:
                    merged_intent["_asked_activities"] = True
                    merged_intent["_last_question_type"] = "optional"
                    activity_question = self._generate_dynamic_question("activity", query, merged_intent) or result.get("assistant_message") or result.get("next_question")
                    return {
                        "needs_clarification":
                        True,
                        "clarification_question":
                        activity_question,
                        "assistant_message":
                        change_acknowledgment + activity_question
                        if change_acknowledgment else activity_question,
                        "updated_intent":
                        merged_intent,
                        "clarified_query":
                        query,
                        "ready_for_recommendations":
                        False,
                        "detected_changes":
                        detected_changes
                    }

            # 2. Budget/Brand preferences are optional - skip asking and proceed to recommendations
            # The LLM handles all questions dynamically based on user input
            if has_destination and has_dates_info and (
                    already_asked_activities
                    or merged_intent.get("_asked_activities")
            ) and not already_asked_optional:
                merged_intent["_asked_optional"] = True
                # Proceed directly - budget/brand are optional, no need to ask

            if already_asked_optional and already_asked_activities:
                if is_skip or has_budget_or_brand or mentions_activity or has_dates_info:
                    base_message = "Perfect! Let me prepare your personalized recommendations."
                    if change_acknowledgment:
                        base_message = change_acknowledgment + "Let me update your recommendations."
                    return {
                        "needs_clarification": False,
                        "clarification_question": "",
                        "assistant_message": base_message,
                        "updated_intent": merged_intent,
                        "clarified_query": query,
                        "ready_for_recommendations": True,
                        "detected_changes": detected_changes
                    }

            if not has_destination:
                next_question = result.get("next_question") or result.get("assistant_message") or self._generate_dynamic_question("destination", query, merged_intent)
                return {
                    "needs_clarification":
                    True,
                    "clarification_question":
                    next_question,
                    "assistant_message":
                    change_acknowledgment +
                    next_question if change_acknowledgment else next_question,
                    "updated_intent":
                    merged_intent,
                    "clarified_query":
                    query,
                    "ready_for_recommendations":
                    False,
                    "detected_changes":
                    detected_changes
                }

            base_message = "Perfect! Let me prepare your personalized recommendations."
            if change_acknowledgment:
                base_message = change_acknowledgment + "Let me update your recommendations."
            return {
                "needs_clarification": False,
                "clarification_question": "",
                "assistant_message": base_message,
                "updated_intent": merged_intent,
                "clarified_query": query,
                "ready_for_recommendations": True,
                "detected_changes": detected_changes
            }
        except json.JSONDecodeError:
            return {
                "needs_clarification": False,
                "clarified_query": query,
                "assistant_message": "",
                "updated_intent": existing_intent or {},
                "detected_changes": {
                    "has_changes": False,
                    "destination_changed": False,
                    "dates_changed": False,
                    "activities_changed": False,
                    "changes": []
                }
            }

    def _merge_intent(self, existing: dict, new: dict) -> dict:
        merged = existing.copy()
        for key, value in new.items():
            if value is not None:
                merged[key] = value
        return merged
