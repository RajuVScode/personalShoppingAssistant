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
- Ask ONLY ONE targeted clarifying question per turn if information is missing or ambiguous.
- If everything is collected and clear, provide a friendly, concise confirmation.
- Use US English tone, be helpful and polite.
- Infer budget currency from context; default to USD.
- If budget is provided without currency, set currency to USD by default.
- Activities should be either an array or strings. If the user gives a single activity (e.g., "hiking"), accept it as a valid array with one item and do not ask for more unless the user seems unsure.
- Clothes can be a simple descriptive string (e.g., "casual summer wear").
- Do NOT ask multiple questions at once; keep it single-question per turn.
- Respond concisely and avoid over-prompting.

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
- Support relative: "today", "tomorrow", "this weekend", "next weekend".
- "today" => {CURRENT_DATE}
- "tomorrow" => {CURRENT_DATE} + 1 day
- "this weekend" => Saturday-Sunday of the current week (based on {CURRENT_DATE})
- "next weekend" => Saturday-Sunday of the following week (based on {CURRENT_DATE})
- If month/day is given without year, infer the year with a future bias relative to {CURRENT_DATE}.
- If multiple destinations are mentioned, choose the primary after prepositions (to/in/at/for) or the final city in "heading to …".
- Date format: "YYYY-MM-DD" (single date) or "YYYY-MM-DD to YYYY-MM-DD" (range).

OUTPUT STRICTLY AS A JSON OBJECT with this shape:
{{
  "assistant_message": "string - what the assistant says to the user in this turn",
  "updated_intent": {{
      "destination": "string|null",
      "travel_date": "string|null",
      "activities": ["string", ...]|null,
      "preferred_brand": "string|null",
      "clothes": "string|null",
      "budget_amount": number|null,
      "budget_currency": "string|null",
      "notes": "string|null"
  }},
  "next_question": "string|null"
}}"""


class ClarifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("Clarifier", CLARIFIER_PROMPT)
    
    def analyze(self, query: str, conversation_history: list = None) -> dict:
        current_date = get_current_date()
        
        context = ""
        if conversation_history:
            context = f"\nConversation history: {json.dumps(conversation_history[-5:])}"
        
        prompt = f"""Today's date: {current_date}

User query: {query}{context}

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
            
            needs_clarification = result.get("next_question") is not None
            
            return {
                "needs_clarification": needs_clarification,
                "clarification_question": result.get("next_question") or result.get("assistant_message", ""),
                "assistant_message": result.get("assistant_message", ""),
                "updated_intent": result.get("updated_intent", {}),
                "clarified_query": query
            }
        except json.JSONDecodeError:
            return {
                "needs_clarification": False,
                "clarified_query": query,
                "assistant_message": "",
                "updated_intent": {}
            }
