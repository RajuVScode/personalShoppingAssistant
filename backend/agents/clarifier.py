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

SIZE PREFERENCE:
- Capture any size mentioned (UK 9, M, L, EU 42, 32, etc.) in preferred_size
- Size is a MANDATORY filter - show only products in that size

DATE HANDLING:
- Accept month names (January, February) as valid date info
- If user says "19-20" after mentioning a month, combine them
- For ambiguous dates like "next week", ask for specific dates
- All dates must be FUTURE relative to {CURRENT_DATE}

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
  "is_new_trip": true|false,
  "next_question": "string|null",
  "ready_for_recommendations": true|false
}}

CRITICAL: When user provides product + destination + date info (even partial like month name) + size, set ready_for_recommendations: true."""

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
        print(f"[DEBUG] LLM intent detection error: {e}, using default values")
        return {
            "has_shopping_intent": False,
            "product_mentioned": None,
            "activity_mentioned": None,
            "is_affirmative": False,
            "is_negative": False
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
            "is_negative": False
        }
    
    return {
        "has_shopping_intent": bool(result.get("has_shopping_intent", False)),
        "product_mentioned": result.get("product_mentioned") if isinstance(result.get("product_mentioned"), str) else None,
        "activity_mentioned": result.get("activity_mentioned") if isinstance(result.get("activity_mentioned"), str) else None,
        "is_affirmative": bool(result.get("is_affirmative", False)),
        "is_negative": bool(result.get("is_negative", False))
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

            # Use LLM signal for date detection - pure LLM-driven
            llm_has_date_info = result.get("has_date_info", False)
            
            # Date PARSING only (not decision-making): combine date fragments from context
            # E.g., user said "January" in previous message, now says "19-20" - combine them
            if llm_has_date_info and not has_date:
                import re
                # Check for day range pattern (e.g., "19-20") that needs month context
                day_match = re.search(r'^\s*(\d{1,2})\s*-\s*(\d{1,2})\s*$', query)
                if day_match:
                    # Look for month context in existing intent
                    existing_travel_date = existing_intent.get("travel_date") or ""
                    existing_month = extract_month_from_text(existing_travel_date)
                    
                    # Also check conversation history for month context
                    if not existing_month and conversation_history:
                        for prev_msg in reversed(conversation_history[-5:]):
                            if isinstance(prev_msg, dict):
                                prev_content = prev_msg.get("content", "")
                            else:
                                prev_content = str(prev_msg)
                            existing_month = extract_month_from_text(prev_content)
                            if existing_month:
                                break
                    
                    if existing_month:
                        start_day = int(day_match.group(1))
                        end_day = int(day_match.group(2))
                        combined_date = f"{existing_month} {start_day}-{end_day}"
                        merged_intent["travel_date"] = combined_date
                        print(f"[DEBUG] Combined date from context: {combined_date}")
                        has_date = True
            
            # Decision uses LLM signal only
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
                # Use LLM-based intent detection (fully dynamic, no keyword fallback)
                llm_intent_result = detect_intent_with_llm(query, self.llm)
                
                # Extract LLM results - pure LLM-driven detection
                direct_shopping_intent = llm_intent_result.get("has_shopping_intent", False)
                
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
            
            # Check for partial date (month only) - ask for specific days
            pending_month = merged_intent.get("_pending_month") or existing_intent.get("_pending_month")
            # has_complete_date is true if we have an actual date (not just partial)
            has_partial_flag = merged_intent.get("_has_partial_date", False) or existing_intent.get("_has_partial_date", False)
            has_complete_date = has_date or (merged_intent.get("travel_date") and not has_partial_flag)
            
            if has_destination and pending_month and not has_complete_date and not existing_intent.get("_asked_specific_dates"):
                dest = merged_intent.get("destination", "your destination")
                # Ask for specific dates while acknowledging the month
                date_question = f"What specific dates in {pending_month} are you traveling to {dest}? (e.g., '{pending_month} 15-20' or '19-20')"
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
