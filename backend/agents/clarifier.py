"""
Clarifier Agent Module

This module implements the ClarifierAgent, responsible for understanding and 
extracting user intent from natural language queries in the shopping assistant.

Key Responsibilities:
- Extract travel intent (destination, dates, activities)
- Detect shopping intent and product mentions
- Handle multi-destination trip planning
- Parse date ranges and handle ambiguous dates
- Capture user preferences (size, brand, budget)

The agent uses LLM-based intent extraction combined with rule-based fallbacks
for reliable detection of products, activities, and user responses.
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


CLARIFIER_PROMPT = """You are a Clarifier Agent for a travel guide and product suggestion application. Your task:
- Extract or confirm the user's intent across these fields:
  destination, travel_date, activities, preferred_brand, clothes, budget_amount, budget_currency, notes.
- SUPPORT MULTI-DESTINATION TRIPS: If user mentions multiple destinations with dates (e.g., "Paris Jan 5-8, then Rome Jan 9-12"), extract ALL of them into trip_segments.

CRITICAL - INTENT INFERENCE FROM CONTEXT:
- NEVER ask "Are you looking to buy something, or are you asking about an activity?" when the user mentions a SPECIFIC PRODUCT.
- If user mentions products (shoes, jacket, backpack, etc.), INFER they want product recommendations. Respond directly and helpfully.
- If user says "waterproof hiking shoes", they want PRODUCT RECOMMENDATIONS for hiking shoes. Don't ask if they're shopping.
- If user mentions an activity context (e.g., "shoes for trekking in Himachal"), infer the use case and provide immediate guidance.

PRODUCT MENTIONS - TREAT AS SHOPPING INTENT:
- shoes, sneakers, boots, sandals, jacket, coat, backpack, bag, luggage, shirt, pants, dress, etc.
- When products are mentioned, set mentions_product: true and skip generic intent questions.
- Provide immediate value: suggest features, ask targeted follow-ups (budget, climate, specific use case).

SIZE PREFERENCE HANDLING:
- If user specifies a size (e.g., "size UK 9", "size M", "32 inch waist", "size 10"), capture it in "preferred_size" field.
- Size formats to recognize: UK sizes (UK 9), US sizes (US 10), EU sizes (EU 42), letter sizes (S, M, L, XL, XXL), numeric sizes (32, 34, 36), waist/inseam (32x30).
- The system will filter recommendations to show ONLY products available in the specified size.
- Do NOT assume size flexibility - the user's size is a mandatory filter.

CRITICAL - EXTRACT EVERYTHING FROM USER MESSAGE:
- ACTIVITIES: If user says "travelling to Miami for hiking" or "going to Paris for shopping", IMMEDIATELY extract "hiking" or "shopping" into the activities array. Do NOT wait to ask - capture it NOW.
- DATES: If user mentions ANY date reference (next weekend, tomorrow, January 5, etc.), set has_date_info: true
- NEW TRIP: If user is starting a new trip (travelling to, going to, trip to, etc.), set is_new_trip: true
- PRODUCTS: If user mentions specific products, capture them in notes and proceed to recommendations.

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

AMBIGUOUS DATE HANDLING - ALWAYS ASK FOR CLARIFICATION:
- When user provides AMBIGUOUS or RELATIVE date expressions, DO NOT auto-interpret them.
- Instead, set "has_ambiguous_date": true and ask for specific calendar dates.
- AMBIGUOUS DATE PHRASES that REQUIRE clarification:
  - "next week", "this week", "a week", "one week", "two weeks", "in 2 weeks"
  - "next month", "this month", "a month"
  - "soon", "in a few days", "sometime next week"
  - Any phrase without specific calendar dates (day, month, or date range)
- Ask: "Could you please specify the exact start and end dates for your trip (for example, 22 Jan–28 Jan)?"

UNAMBIGUOUS DATES - Process without clarification:
- Specific dates: "January 15", "March 12-15", "2026-01-22 to 2026-01-28"
- Specific weekends with dates implied: "this weekend" (Saturday-Sunday only - 2 days is acceptable)
- Explicit date ranges: "from 5 March to 8 March", "10-12 Jan 2025"

- CRITICAL: All dates MUST be in the FUTURE relative to {CURRENT_DATE}.
- If month/day is given without year, always use the NEXT occurrence of that date in the future.
- Date format: "YYYY-MM-DD" (single date) or "YYYY-MM-DD to YYYY-MM-DD" (range).

MULTI-DESTINATION HANDLING:
- If user mentions multiple destinations with different dates, extract each as a trip_segment.
- Example: "Paris Jan 5-8, then Rome Jan 9-12" → two segments
- Each segment has: destination, start_date, end_date, activities (optional)
- Set "destination" to first destination, "travel_date" to full range (first start to last end)
- Preserve trip_segments array for detailed per-leg context

DECISION LOGIC:
- If destination is missing → next_question asks for destination
- If travel_date is missing → next_question asks for travel dates  
- If user provides AMBIGUOUS date (next week, one week, etc.) → ask for specific calendar dates
- If destination AND specific travel_date are present → Set next_question to null AND ready_for_recommendations to true
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
      "preferred_size": "string|null - user's size preference (e.g., 'UK 9', 'M', 'L', '32', 'EU 42')",
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
    "hiking",
    "cycling",
    "swimming",
    "surfing",
    "skiing",
    "snowboarding",
    "shopping",
    "sightseeing",
    "dining",
    "beach",
    "museum",
    "concert",
    "wedding",
    "conference",
    "meeting",
    "business",
    "festival",
    "party",
    "spa",
    "wellness",
    "yoga",
    "golf",
    "tennis",
    "running",
    "jogging",
    "camping",
    "fishing",
    "climbing",
    "diving",
    "snorkeling",
    "kayaking",
    "sailing",
    "boating",
    "photography",
    "wine tasting",
    "cooking class",
    "tour",
    "adventure",
    "nightlife",
    "clubbing",
    "theater",
    "opera",
    "trekking",
    "cooking",
    "gym",
    "gaming",
    "travel",
}

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
Analyze the user's message and extract:

1. **Shopping Intent**: Does the user want to buy, purchase, or acquire a product? 
   - "yes, like to buy shoes" → has_shopping_intent: true
   - "I need a jacket for my trip" → has_shopping_intent: true
   - "What's the weather like?" → has_shopping_intent: false

2. **Product Mentioned**: What specific product category is mentioned?
   - Look for: clothing (shoes, jacket, dress, pants, shirt, coat, sweater, etc.)
   - Accessories (bag, backpack, hat, sunglasses, watch, etc.)
   - Footwear (boots, sneakers, sandals, heels, etc.)
   - Return the general category, e.g., "shoes" not "hiking shoes"

3. **Activity Mentioned**: What activity or purpose is mentioned?
   - Examples: hiking, swimming, traveling, wedding, business meeting, beach, skiing
   - This helps contextualize product recommendations

4. **Response Type**: Is this an affirmative or negative response to a question?
   - Affirmative: yes, yeah, sure, okay, please, sounds good, let's do it
   - Negative: no, nope, not really, skip, I'm good

Respond ONLY with a JSON object (no markdown, no explanation):
{
  "has_shopping_intent": true/false,
  "product_mentioned": "product_type" or null,
  "activity_mentioned": "activity" or null,
  "is_affirmative": true/false,
  "is_negative": true/false
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
        print(f"[DEBUG] LLM intent detection error: {e}, falling back to keyword detection")
        return {
            "has_shopping_intent": False,
            "product_mentioned": None,
            "activity_mentioned": None,
            "is_affirmative": False,
            "is_negative": False
        }


# FALLBACK KEYWORD SETS: Used when LLM detection fails or returns invalid results.
# Primary intent detection uses detect_intent_with_llm() for intelligent detection,
# but these comprehensive lists ensure robust fallback behavior.
SHOPPING_KEYWORDS = {
    "shopping", "buy", "purchase", "order", "get a product",
    "looking to buy", "need to purchase", "want to buy",
    "buying", "purchasing", "shop", "need some",
    "looking for", "want some", "get some",
}

# FALLBACK: Comprehensive product keywords for robust detection when LLM fails
PRODUCT_KEYWORDS = {
    # Footwear
    "shoes", "shoe", "sneakers", "boots", "sandals", "loafers", "heels", "flats",
    # Outerwear
    "jacket", "jackets", "coat", "coats", "blazer", "blazers", "parka", "windbreaker",
    # Bags
    "backpack", "backpacks", "bag", "bags", "luggage", "suitcase", "duffel", "tote",
    # Tops
    "shirt", "shirts", "t-shirt", "t-shirts", "blouse", "top", "tops",
    # Bottoms
    "pants", "trousers", "jeans", "shorts", "leggings", "chinos",
    # Dresses
    "dress", "dresses", "skirt", "skirts", "gown",
    # Knitwear
    "sweater", "sweaters", "hoodie", "hoodies", "cardigan", "pullover",
    # Accessories
    "hat", "hats", "cap", "caps", "beanie", "sunglasses", "glasses",
    "watch", "watches", "jewelry", "accessories", "scarf", "scarves", "gloves",
    # Weather gear
    "umbrella", "raincoat", "poncho", "waterproof",
    # Swimwear
    "swimsuit", "swimwear", "bikini", "trunks",
    # Formal
    "suit", "suits", "tuxedo", "formal wear",
    # Activewear
    "activewear", "sportswear", "athleisure", "workout clothes",
    # Outdoor
    "hiking gear", "camping gear", "travel gear", "outdoor gear",
    # Cold weather
    "thermal", "thermals", "base layer", "fleece", "down jacket", "puffer", "insulated",
}


def detect_product_mention(query: str) -> str:
    """
    Keyword-based fallback for product detection.
    
    Used as a robust fallback when LLM detection fails or returns invalid results.
    The primary detection method is detect_intent_with_llm().
    
    Args:
        query: The user's message text
        
    Returns:
        The matched product keyword if found, None otherwise
    """
    query_lower = query.lower()
    for product in PRODUCT_KEYWORDS:
        if product in query_lower:
            return product
    return None


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
            "is_negative": False
        }
    
    return {
        "has_shopping_intent": bool(result.get("has_shopping_intent", False)),
        "product_mentioned": result.get("product_mentioned") if isinstance(result.get("product_mentioned"), str) else None,
        "activity_mentioned": result.get("activity_mentioned") if isinstance(result.get("activity_mentioned"), str) else None,
        "is_affirmative": bool(result.get("is_affirmative", False)),
        "is_negative": bool(result.get("is_negative", False))
    }


AMBIGUOUS_DATE_PHRASES = {
    "next week",
    "this week",
    "a week",
    "one week",
    "two weeks",
    "2 weeks",
    "in 2 weeks",
    "in two weeks",
    "few weeks",
    "couple weeks",
    "couple of weeks",
    "next month",
    "this month",
    "a month",
    "one month",
    "two months",
    "soon",
    "in a few days",
    "few days",
    "couple days",
    "couple of days",
    "sometime",
    "around",
    "roughly",
    "approximately",
    "end of month",
    "beginning of month",
    "mid month",
    "end of january",
    "end of february",
    "end of march",
    "end of april",
    "end of may",
    "end of june",
    "end of july",
    "end of august",
    "end of september",
    "end of october",
    "end of november",
    "end of december",
}


def detect_ambiguous_date(query: str) -> bool:
    """Check if the query contains an ambiguous date phrase that needs clarification."""
    query_lower = query.lower()

    # Check for ambiguous phrases
    for phrase in AMBIGUOUS_DATE_PHRASES:
        if phrase in query_lower:
            return True

    # Check for patterns like "1 week", "2 weeks", etc.
    import re
    ambiguous_patterns = [
        r'\b\d+\s*weeks?\b',  # "1 week", "2 weeks"
        r'\b\d+\s*months?\b',  # "1 month", "2 months"
        r'\bnext\s+week\b',
        r'\bthis\s+week\b',
        r'\bin\s+\d+\s+days?\b',  # "in 3 days"
    ]

    for pattern in ambiguous_patterns:
        if re.search(pattern, query_lower):
            return True

    return False


def has_specific_date(query: str) -> bool:
    """Check if the query contains specific calendar dates."""
    import re
    query_lower = query.lower()

    # Patterns for specific dates
    specific_patterns = [
        r'\b\d{1,2}\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',  # "15 Jan", "5 March"
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{1,2}',  # "Jan 15", "March 5"
        r'\b\d{4}-\d{2}-\d{2}\b',  # ISO format "2026-01-15"
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # "01/15/2026"
        r'\b\d{1,2}-\d{1,2}\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',  # "15-18 Jan"
        r'\bjanuary\s+\d{1,2}',
        r'\bfebruary\s+\d{1,2}',
        r'\bmarch\s+\d{1,2}',
        r'\bapril\s+\d{1,2}',
        r'\bmay\s+\d{1,2}',
        r'\bjune\s+\d{1,2}',
        r'\bjuly\s+\d{1,2}',
        r'\baugust\s+\d{1,2}',
        r'\bseptember\s+\d{1,2}',
        r'\boctober\s+\d{1,2}',
        r'\bnovember\s+\d{1,2}',
        r'\bdecember\s+\d{1,2}',
        r'\b\d{1,2}(st|nd|rd|th)\s+(of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',  # "15th of January"
    ]

    for pattern in specific_patterns:
        if re.search(pattern, query_lower):
            return True

    # Check for "this weekend" which is acceptable (specific 2-day period)
    if "this weekend" in query_lower or "upcoming weekend" in query_lower:
        return True

    return False


NON_SHOPPING_ACTIVITIES = {
    "hiking",
    "trekking",
    "running",
    "dining",
    "cooking",
    "camping",
    "gym",
    "gaming",
    "photography",
    "swimming",
    "cycling",
    "surfing",
    "skiing",
    "snowboarding",
    "yoga",
    "golf",
    "tennis",
    "jogging",
    "fishing",
    "climbing",
    "diving",
    "snorkeling",
    "kayaking",
    "sailing",
    "boating",
    "wine tasting",
    "cooking class",
    "tour",
    "adventure",
    "nightlife",
    "clubbing",
    "theater",
    "opera",
    "sightseeing",
    "beach",
    "museum",
    "concert",
    "wedding",
    "conference",
    "meeting",
    "business",
    "festival",
    "party",
    "spa",
    "wellness",
}


def detect_shopping_intent(query: str) -> bool:
    """Check if the query indicates shopping/purchasing intent."""
    query_lower = query.lower()
    for keyword in SHOPPING_KEYWORDS:
        if keyword in query_lower:
            return True
    return False


def detect_non_shopping_activity(query: str) -> str:
    """Check if the query mentions a non-shopping activity. Returns the activity name or None."""
    query_lower = query.lower()
    for activity in NON_SHOPPING_ACTIVITIES:
        if activity in query_lower:
            return activity
    return None


def is_affirmative_response(query: str) -> bool:
    """Check if the query is an affirmative response."""
    affirmatives = {
        "yes", "yeah", "sure", "okay", "ok", "go ahead", "proceed", "yep",
        "yup", "absolutely", "definitely", "please", "of course",
        "sounds good", "let's do it", "yes please", "sure thing"
    }
    query_lower = query.lower().strip()
    return query_lower in affirmatives or any(aff in query_lower
                                              for aff in affirmatives)


def is_negative_response(query: str) -> bool:
    """Check if the query is a negative response."""
    negatives = {
        "no", "nope", "nah", "not really", "no thanks", "no thank you",
        "i'm good", "skip", "not interested", "don't need"
    }
    query_lower = query.lower().strip()
    return query_lower in negatives or any(neg in query_lower
                                           for neg in negatives)


KNOWN_BRANDS = {
    "riviera atelier", "montclair house", "maison signature",
    "aurelle couture", "golden atelier", "veloce luxe", "luxe & co.",
    "evangeline", "opal essence", "bellezza studio", "seaside atelier",
    "sable & stone"
}


class ClarifierAgent(BaseAgent):

    def __init__(self):
        super().__init__("Clarifier", CLARIFIER_PROMPT)

    def _generate_dynamic_product_question(self, query: str, intent: dict) -> str:
        """
        Generate a contextual product question using LLM based on user context.
        
        Instead of asking generic "What kind of products would you like to buy?",
        this generates a question tailored to the user's destination, activities,
        and other context.
        
        Args:
            query: The user's original message
            intent: Current merged intent with destination, dates, activities etc.
            
        Returns:
            A contextual question about what products the user needs
        """
        try:
            from langchain_core.messages import SystemMessage as SysMsg
            
            destination = intent.get("destination") or intent.get("destination_city") or ""
            activities = intent.get("activities") or []
            travel_date = intent.get("travel_date") or ""
            
            context_parts = []
            if destination:
                context_parts.append(f"traveling to {destination}")
            if travel_date:
                context_parts.append(f"on {travel_date}")
            if activities:
                context_parts.append(f"for {', '.join(activities)}")
            
            context_str = " ".join(context_parts) if context_parts else "their trip"
            
            prompt = f"""You are a helpful shopping assistant. The user indicated they want to shop but didn't specify what products.

User's message: "{query}"
Context: {context_str}

Generate a SHORT, friendly question (1 sentence, max 15 words) asking what specific products they're looking for.
Do NOT suggest products. Just ask what they need.

Return ONLY the question, no quotes or explanation."""

            messages = [SysMsg(content=prompt)]
            response = self.llm.invoke(messages)
            question = response.content.strip().strip('"\'')
            
            # Validate response is reasonable
            if question and len(question) > 10 and len(question) < 200 and "?" in question:
                return question
            else:
                # Fallback if LLM response is malformed
                return f"What products are you looking for{' for ' + destination if destination else ''}?"
                
        except Exception as e:
            print(f"[DEBUG] Error generating dynamic product question: {e}")
            destination = intent.get("destination") or intent.get("destination_city") or ""
            return f"What products are you looking for{' for ' + destination if destination else ''}?"

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

            # Check for ambiguous dates BEFORE auto-parsing
            # If user provides ambiguous date and no specific date, ask for clarification
            has_ambiguous = detect_ambiguous_date(query)
            has_specific = has_specific_date(query)
            already_asked_date_clarification = existing_intent.get(
                "_asked_date_clarification", False)

            if has_ambiguous and not has_specific and not already_asked_date_clarification and not merged_intent.get(
                    "travel_date"):
                # User provided ambiguous date like "next week" - ask for specific dates
                merged_intent["_asked_date_clarification"] = True
                destination = merged_intent.get("destination",
                                                "your destination")
                date_clarification = f"Could you please specify the exact start and end dates for your trip to {destination}? (for example, 22 Jan - 28 Jan)"
                print(
                    f"[DEBUG] Detected ambiguous date in query, asking for clarification"
                )
                return {
                    "needs_clarification":
                    True,
                    "clarification_question":
                    date_clarification,
                    "assistant_message":
                    change_acknowledgment + date_clarification
                    if change_acknowledgment else date_clarification,
                    "updated_intent":
                    merged_intent,
                    "clarified_query":
                    query,
                    "ready_for_recommendations":
                    False,
                    "detected_changes":
                    detected_changes
                }

            # Only auto-parse dates if they are specific (not ambiguous)
            if not merged_intent.get("travel_date") and has_specific:
                parsed_date = parse_relative_date(query, datetime.now())
                if parsed_date:
                    merged_intent["travel_date"] = parsed_date
                    result["has_date_info"] = True
                    print(
                        f"[DEBUG] Parsed specific date from query: {parsed_date}"
                    )

            country_only = new_intent.get("country_only", False)
            destination_country = new_intent.get("destination_country")
            destination_city = new_intent.get("destination_city")

            if country_only and destination_country and not destination_city and not existing_destination:
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

            already_asked_optional = existing_intent.get(
                "_asked_optional", False) or merged_intent.get(
                    "_asked_optional", False)
            already_asked_activities = existing_intent.get(
                "_asked_activities", False) or merged_intent.get(
                    "_asked_activities", False)

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

            llm_has_date_info = result.get("has_date_info", False)
            has_dates_info = has_date or llm_has_date_info

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
                # Use LLM-based intent detection with fallback to keyword matching
                llm_intent_result = detect_intent_with_llm(query, self.llm)
                
                # Extract LLM results with fallback to keyword-based detection
                llm_shopping_intent = llm_intent_result.get("has_shopping_intent", False)
                keyword_shopping_intent = detect_shopping_intent(query)
                direct_shopping_intent = llm_shopping_intent or keyword_shopping_intent
                
                # Activity detection from LLM with fallback
                llm_activity = llm_intent_result.get("activity_mentioned")
                keyword_activity = detect_non_shopping_activity(query)
                
                # Map activity to non-shopping activity if it's not shopping-related
                if llm_activity and llm_activity.lower() not in ["shopping", "buying", "purchasing"]:
                    direct_non_shopping_activity = llm_activity.lower()
                elif keyword_activity:
                    direct_non_shopping_activity = keyword_activity
                else:
                    direct_non_shopping_activity = None

            # Handle shopping confirmation response (yes/no to "Would you like to shop for activity?")
            awaiting_shopping_confirm = existing_intent.get(
                "_awaiting_shopping_confirm", False)
            if awaiting_shopping_confirm:
                # Use LLM result combined with keyword fallback for robust detection
                llm_product = llm_intent_result.get("product_mentioned") if llm_intent_result else None
                keyword_product = detect_product_mention(query)
                product_in_confirmation = llm_product or keyword_product
                
                # Combine LLM and keyword-based affirmative/negative detection
                llm_is_affirmative = llm_intent_result.get("is_affirmative", False) if llm_intent_result else False
                llm_is_negative = llm_intent_result.get("is_negative", False) if llm_intent_result else False
                keyword_is_affirmative = is_affirmative_response(query)
                keyword_is_negative = is_negative_response(query)
                
                is_user_affirmative = llm_is_affirmative or keyword_is_affirmative
                is_user_negative = llm_is_negative or keyword_is_negative
                
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
                        product_question = "What kind of products or category of products would you like to buy?"
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
                    tip_message = f"No problem! Here are some tips for {activity_name}: Make sure to check weather conditions, bring appropriate gear, and stay hydrated. Enjoy your trip!"
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
            # FIRST check if user already mentioned a specific product (LLM + keyword fallback)
            llm_product_mention = llm_intent_result.get("product_mentioned") if llm_intent_result else None
            keyword_product_mention = detect_product_mention(query)
            product_mention = llm_product_mention or keyword_product_mention
            
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
                    shopping_question = f"Would you like to do shopping for {direct_non_shopping_activity}?"
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
                        ambiguous_question = "Are you looking to buy something, or are you asking about an activity?"
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
                dest = merged_intent.get("destination", "your destination")
                date_question = f"When are you planning to travel to {dest}? (e.g., 'next weekend', 'January 15-20', or specific dates)"
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
                # Filter out generic travel words that aren't real activities
                generic_travel_words = {
                    "travel", "travelling", "traveling", "trip", "vacation",
                    "holiday", "visit", "visiting", "going"
                }
                captured_activities = merged_intent.get(
                    "activities") or existing_intent.get("activities") or []
                specific_activities = [
                    a for a in captured_activities
                    if a.lower() not in generic_travel_words
                ]
                has_specific_activities = len(specific_activities) > 0

                if has_specific_activities:
                    merged_intent["_asked_activities"] = True
                    # Activities already captured by early detection, continue to optional
                else:
                    merged_intent["_asked_activities"] = True
                    activity_question = "What kind of activities are you planning for this trip? (e.g., hiking, shopping, dining)"
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

            # 2. Ask Optional (Budget/Brand) if missing
            if has_destination and has_dates_info and (
                    already_asked_activities
                    or merged_intent.get("_asked_activities")
            ) and not already_asked_optional:
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
                        "needs_clarification":
                        True,
                        "clarification_question":
                        optional_question,
                        "assistant_message":
                        change_acknowledgment + optional_question
                        if change_acknowledgment else optional_question,
                        "updated_intent":
                        merged_intent,
                        "clarified_query":
                        query,
                        "ready_for_recommendations":
                        False,
                        "detected_changes":
                        detected_changes
                    }

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
                next_question = result.get(
                    "next_question") or "Where would you like to travel?"
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
