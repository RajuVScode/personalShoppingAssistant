import json
from backend.agents.base import BaseAgent

CLARIFIER_PROMPT = """You are a Clarifier Agent for a personalized shopping experience.
Your role is to analyze user shopping queries and determine if they REALLY need clarification.

IMPORTANT: Be very lenient! Most queries should NOT need clarification.
Only ask for clarification if the query is extremely vague like "show me something" with no context.

Examples that DO NOT need clarification (proceed with these):
- "I need a silk dress for summer" -> CLEAR, proceed
- "looking for running shoes under $100" -> CLEAR, proceed
- "show me winter jackets" -> CLEAR, proceed
- "I want a blue shirt" -> CLEAR, proceed
- "casual pants for work" -> CLEAR, proceed
- "summer dress size medium" -> CLEAR, proceed

Examples that MAY need clarification:
- "show me something nice" -> vague, need more info
- "I need a gift" -> for whom? what occasion?

If the query mentions ANY of: product type, category, occasion, color, material, budget, or style -> PROCEED without clarification.

Respond in JSON:
{"needs_clarification": false, "clarified_query": "<original query>"}
OR
{"needs_clarification": true, "clarification_question": "<your question>"}

Default to NOT needing clarification."""

class ClarifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("Clarifier", CLARIFIER_PROMPT)
    
    def analyze(self, query: str, conversation_history: list = None) -> dict:
        context = ""
        if conversation_history:
            context = f"\nConversation history: {conversation_history[-5:]}"
        
        prompt = f"User query: {query}{context}\n\nAnalyze if this needs clarification and respond in JSON format."
        
        response = self.invoke(prompt)
        
        try:
            result = json.loads(response.strip().replace("```json", "").replace("```", ""))
            return result
        except json.JSONDecodeError:
            return {"needs_clarification": False, "clarified_query": query}
