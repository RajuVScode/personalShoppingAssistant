import json
from backend.agents.base import BaseAgent
from backend.models.schemas import NormalizedIntent

INTENT_PROMPT = """You are an Intent Processor for a personalized shopping experience.
Your role is to extract structured shopping intent from natural language queries.

Extract the following information when available:
- category: Main product category (e.g., "Footwear", "Apparel", "Accessories")
- subcategory: More specific (e.g., "Running Shoes", "Winter Jacket", "Handbag")
- budget_min: Minimum price if mentioned
- budget_max: Maximum price if mentioned
- occasion: What the item is for (e.g., "wedding", "casual", "work", "gym")
- style: Style preference (e.g., "modern", "classic", "sporty", "elegant")
- gender: Target gender (e.g., "men", "women", "unisex")
- color_preferences: Any mentioned colors as a list
- size: If mentioned
- keywords: Important keywords from the query

Respond ONLY with a valid JSON object containing these fields.
Use null for fields that cannot be determined from the query.
Always include "raw_query" with the original query."""

class IntentProcessor(BaseAgent):
    def __init__(self):
        super().__init__("IntentProcessor", INTENT_PROMPT)
    
    def process(self, query: str) -> NormalizedIntent:
        prompt = f"Extract shopping intent from this query: \"{query}\""
        
        response = self.invoke(prompt)
        
        try:
            data = json.loads(response.strip().replace("```json", "").replace("```", ""))
            data["raw_query"] = query
            return NormalizedIntent(**data)
        except (json.JSONDecodeError, Exception):
            return NormalizedIntent(raw_query=query, keywords=query.split())
