import json
from backend.agents.base import BaseAgent
from backend.models.schemas import NormalizedIntent

INTENT_PROMPT = """You are an Intent Processor for a personalized shopping experience.
Your role is to extract structured shopping intent from natural language queries.

IMPORTANT: Use these exact category names from the product catalog:
- Clothing (for apparel, dresses, shirts, pants, etc.)
- Footwear (shoes, boots, sneakers)
- Shoes (alternative for footwear)
- Accessories (belts, scarves, hats, etc.)
- Handbags (purses, bags)
- Designer Bags
- Outerwear (jackets, coats)
- Fine Jewelry (rings, necklaces, bracelets)
- Beauty (cosmetics)
- Makeup
- Skincare
- Fragrance (perfume, cologne)
- Bedding
- Decor

For subcategory, use: Dresses, Tops, Pants, Skirts, Blazers, Sneakers, Heels, Boots, etc.

Extract:
- category: Use exact category from list above
- subcategory: Specific type (e.g., "Dresses", "Tops", "Sneakers")
- budget_min/budget_max: Price range if mentioned
- occasion: What the item is for
- style: Style preference
- gender: "men", "women", or "unisex"
- color_preferences: Any colors mentioned
- size: If mentioned
- keywords: Important words

Respond ONLY with valid JSON. Use null for unknown fields."""

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
