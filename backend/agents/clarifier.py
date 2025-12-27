import json
from backend.agents.base import BaseAgent

CLARIFIER_PROMPT = """You are a Clarifier Agent for a personalized shopping experience.
Your role is to analyze user shopping queries and determine if they need clarification.

When analyzing a query, check for:
1. Ambiguous product categories (e.g., "something nice" - nice for what occasion?)
2. Missing budget information when relevant
3. Unclear size or fit preferences
4. Vague occasion or purpose
5. Missing gender/target person information

If the query is clear enough to proceed, respond with:
{"needs_clarification": false, "clarified_query": "<original query>"}

If clarification is needed, respond with:
{"needs_clarification": true, "clarification_question": "<your follow-up question>", "reason": "<why you need this>"}

Always be helpful and conversational in your clarification questions.
Only ask ONE clarification question at a time - the most important one.
Be concise and friendly."""

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
