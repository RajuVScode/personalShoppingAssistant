import re
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from backend.agents.clarifier import ClarifierAgent

OFF_TOPIC_MESSAGE = """Thank you for your message. I am a travel shopping assistant designed to help you find the perfect items for your travel needs.

I would be happy to assist you with:
- Travel destination planning and outfit recommendations
- Weather-appropriate clothing suggestions for your trips
- Shopping recommendations based on your travel activities
- Budget-friendly travel wardrobe options

Please feel free to share your travel plans or shopping needs, and I will be glad to help you find suitable recommendations."""

TRAVEL_SHOPPING_KEYWORDS = {
    'travel', 'trip', 'vacation', 'holiday', 'destination', 'flying', 'flight',
    'beach', 'mountain', 'city', 'country', 'abroad', 'overseas', 'weekend',
    'shopping', 'clothes', 'clothing', 'outfit', 'wear', 'dress', 'shirt', 'pants',
    'jacket', 'coat', 'shoes', 'accessories', 'bag', 'luggage', 'suitcase',
    'pack', 'packing', 'wardrobe', 'fashion', 'style', 'brand', 'buy', 'purchase',
    'recommend', 'suggestion', 'hiking', 'swimming', 'skiing', 'camping',
    'business', 'meeting', 'conference', 'wedding', 'formal', 'casual',
    'summer', 'winter', 'spring', 'fall', 'autumn', 'weather', 'hot', 'cold',
    'warm', 'rainy', 'sunny', 'budget', 'price', 'cost', 'affordable',
    'paris', 'london', 'tokyo', 'new york', 'miami', 'rome', 'dubai',
    'hotel', 'resort', 'cruise', 'tour', 'adventure', 'explore',
    'next week', 'next weekend', 'tomorrow', 'january', 'february', 'march',
    'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'
}

def is_travel_shopping_related(query: str) -> bool:
    """Check if the query is related to travel or shopping topics."""
    query_lower = query.lower()
    
    for keyword in TRAVEL_SHOPPING_KEYWORDS:
        if keyword in query_lower:
            return True
    
    travel_patterns = [
        r'\bgoing\s+to\b', r'\btravel(?:l)?ing\s+to\b', r'\bvisit(?:ing)?\b',
        r'\bflying\s+to\b', r'\bheading\s+to\b', r'\boff\s+to\b',
        r'\bneed\s+(?:some|a|an)?\s*(?:new)?\s*(?:clothes|outfit|dress|shirt)',
        r'\bwhat\s+(?:should|can|to)\s+(?:i\s+)?(?:wear|pack|bring)\b',
        r'\brecommend(?:ation)?s?\b', r'\bsuggestion?s?\b',
        r'\bweek(?:s)?\s+from\b', r'\bdays?\s+from\b'
    ]
    
    for pattern in travel_patterns:
        if re.search(pattern, query_lower):
            return True
    
    return False

from backend.agents.intent_processor import IntentProcessor
from backend.agents.customer360 import Customer360Agent
from backend.agents.context_aggregator import ContextAggregator
from backend.agents.product_recommender import ProductRecommenderAgent
from backend.models.schemas import (
    ChatMessage, NormalizedIntent, CustomerContext, 
    EnvironmentalContext, EnrichedContext
)

class GraphState(TypedDict):
    messages: list
    user_id: int
    raw_query: str
    is_ambiguous: bool
    clarification_question: str
    assistant_message: str
    clarifier_intent: dict
    normalized_intent: dict
    customer_context: dict
    environmental_context: dict
    enriched_context: dict
    products: list
    final_response: str
    conversation_history: list
    detected_changes: dict
    context_refresh_needed: bool
    agent_thinking: list

from datetime import datetime

class ShoppingOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.clarifier = ClarifierAgent()
        self.intent_processor = IntentProcessor()
        self.customer360 = Customer360Agent(db)
        self.context_aggregator = ContextAggregator()
        self.recommender = ProductRecommenderAgent()
        self.graph = self._build_graph()
    
    def _add_thinking_step(self, state: GraphState, agent: str, action: str, details: dict = None) -> None:
        if "agent_thinking" not in state or state["agent_thinking"] is None:
            state["agent_thinking"] = []
        state["agent_thinking"].append({
            "agent": agent,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(GraphState)
        
        workflow.add_node("clarify", self._clarify_node)
        workflow.add_node("process_intent", self._intent_node)
        workflow.add_node("get_customer_context", self._customer_context_node)
        workflow.add_node("aggregate_context", self._aggregate_context_node)
        workflow.add_node("recommend", self._recommend_node)
        
        workflow.set_entry_point("clarify")
        
        workflow.add_conditional_edges(
            "clarify",
            self._should_clarify,
            {
                "clarify": END,
                "proceed": "process_intent"
            }
        )
        
        workflow.add_edge("process_intent", "get_customer_context")
        workflow.add_edge("get_customer_context", "aggregate_context")
        workflow.add_edge("aggregate_context", "recommend")
        workflow.add_edge("recommend", END)
        
        return workflow.compile()
    
    def _clarify_node(self, state: GraphState) -> GraphState:
        existing_intent = state.get("clarifier_intent", {})
        
        result = self.clarifier.analyze(
            state["raw_query"],
            state.get("conversation_history", []),
            existing_intent=existing_intent
        )
        
        state["is_ambiguous"] = result.get("needs_clarification", False)
        state["clarification_question"] = result.get("clarification_question", "")
        state["assistant_message"] = result.get("assistant_message", "")
        state["clarifier_intent"] = result.get("updated_intent", {})
        
        detected_changes = result.get("detected_changes", {})
        state["detected_changes"] = detected_changes
        state["context_refresh_needed"] = detected_changes.get("has_changes", False)
        
        destination = state["clarifier_intent"].get("destination", "")
        activities = state["clarifier_intent"].get("activities", "")
        travel_date = state["clarifier_intent"].get("travel_date", "")
        
        if state["is_ambiguous"]:
            if not destination:
                self._add_thinking_step(state, "Discovery", "I need to find out where they're headed so I can pull the right weather, event context, and travel style cues. Starting with a friendly tone to encourage natural sharing.")
            elif not travel_date:
                self._add_thinking_step(state, "Discovery", f"Now that I know the destination is {destination}, I need to find out the trip duration. This will help me calculate what they'll need and factor in the weather conditions.")
            elif not activities:
                self._add_thinking_step(state, "Discovery", f"With {destination} and dates set, I need to uncover the planned activities. Events like dinners or outdoor outings will influence what categories I recommend.")
        elif destination:
            self._add_thinking_step(state, "Discovery", f"I have all the details I need: {destination}" + (f" for {activities}" if activities else "") + ". Now I can organize recommendations by use case and help them visualize solving each segment.")
        
        if state["is_ambiguous"]:
            state["final_response"] = result.get("assistant_message", "") or state["clarification_question"]
        
        return state
    
    def _should_clarify(self, state: GraphState) -> Literal["clarify", "proceed"]:
        if state.get("is_ambiguous", False):
            return "clarify"
        return "proceed"
    
    def _intent_node(self, state: GraphState) -> GraphState:
        category = state.get("clarifier_intent", {}).get("notes", "items")
        self._add_thinking_step(state, "Planning", f"Time to structure the shopping approach. I'll identify the key product categories needed and build a framework to organize recommendations clearly.")
        
        intent = self.intent_processor.process(state["raw_query"])
        intent_dict = intent.model_dump()
        
        clarifier_intent = state.get("clarifier_intent", {})
        if clarifier_intent:
            if clarifier_intent.get("destination") and not intent_dict.get("location"):
                intent_dict["location"] = clarifier_intent["destination"]
            if clarifier_intent.get("travel_date"):
                intent_dict["occasion"] = f"travel on {clarifier_intent['travel_date']}"
            if clarifier_intent.get("activities"):
                activities = clarifier_intent["activities"]
                if isinstance(activities, str):
                    activities = [a.strip() for a in activities.split(",")]
                existing_keywords = intent_dict.get("keywords") or []
                intent_dict["keywords"] = existing_keywords + activities
            if clarifier_intent.get("budget_amount"):
                intent_dict["budget_max"] = clarifier_intent["budget_amount"]
            if clarifier_intent.get("clothes"):
                intent_dict["style"] = clarifier_intent["clothes"]
            if clarifier_intent.get("preferred_brand"):
                intent_dict["brand"] = clarifier_intent["preferred_brand"]
            if clarifier_intent.get("preferred_size"):
                intent_dict["size"] = clarifier_intent["preferred_size"]
                print(f"[DEBUG] Size preference captured: {clarifier_intent['preferred_size']}")
            if clarifier_intent.get("trip_segments"):
                intent_dict["trip_segments"] = clarifier_intent["trip_segments"]
            
            # Pass through requested_content for dynamic response generation
            if clarifier_intent.get("requested_content"):
                intent_dict["requested_content"] = clarifier_intent["requested_content"]
                # Also set travel_date for context
                if clarifier_intent.get("travel_date"):
                    intent_dict["travel_date"] = clarifier_intent["travel_date"]
                # Pass trip_duration_days for multi-day itineraries
                if clarifier_intent.get("trip_duration_days"):
                    intent_dict["trip_duration_days"] = clarifier_intent["trip_duration_days"]
                    print(f"[DEBUG] Intent: trip_duration_days = {clarifier_intent['trip_duration_days']}")
            
            # Extract product category from notes field (user's answer to "What products?")
            if clarifier_intent.get("notes") and not intent_dict.get("category"):
                notes = clarifier_intent["notes"].lower()
                # Map common product terms to catalog categories
                category_mapping = {
                    "shoes": "Footwear",
                    "shoe": "Footwear",
                    "sneakers": "Footwear",
                    "boots": "Footwear",
                    "heels": "Footwear",
                    "sandals": "Footwear",
                    "footwear": "Footwear",
                    "loafers": "Footwear",
                    "flats": "Footwear",
                    "clothing": "Clothing",
                    "clothes": "Clothing",
                    "dress": "Clothing",
                    "dresses": "Clothing",
                    "shirt": "Clothing",
                    "shirts": "Clothing",
                    "pants": "Clothing",
                    "jeans": "Clothing",
                    "jacket": "Outerwear",
                    "jackets": "Outerwear",
                    "coat": "Outerwear",
                    "coats": "Outerwear",
                    "outerwear": "Outerwear",
                    "bag": "Handbags",
                    "bags": "Handbags",
                    "handbag": "Handbags",
                    "handbags": "Handbags",
                    "purse": "Handbags",
                    "accessories": "Accessories",
                    "jewelry": "Fine Jewelry",
                    "jewellery": "Fine Jewelry",
                    "makeup": "Makeup",
                    "cosmetics": "Beauty",
                    "skincare": "Skincare",
                    "perfume": "Fragrance",
                    "fragrance": "Fragrance",
                }
                
                for keyword, category in category_mapping.items():
                    if keyword in notes:
                        intent_dict["category"] = category
                        # Also set subcategory for more specific terms
                        if keyword in ["sneakers", "boots", "heels", "sandals", "loafers", "flats"]:
                            intent_dict["subcategory"] = keyword.capitalize()
                        elif keyword in ["dress", "dresses"]:
                            intent_dict["subcategory"] = "Dresses"
                        elif keyword in ["shirt", "shirts"]:
                            intent_dict["subcategory"] = "Tops"
                        break
                
                # Add notes to keywords for better search
                existing_keywords = intent_dict.get("keywords") or []
                intent_dict["keywords"] = existing_keywords + [clarifier_intent["notes"]]
        
        state["normalized_intent"] = intent_dict
        
        category = intent_dict.get("category", "items")
        style = intent_dict.get("style", "")
        location = intent_dict.get("location", "their destination")
        self._add_thinking_step(state, "Planning", f"For {location}, I'll focus on {category.lower() if category else 'versatile pieces'}{' with ' + style + ' style' if style else ''}. This will help ensure everything works together.")
        
        return state
    
    def _customer_context_node(self, state: GraphState) -> GraphState:
        self._add_thinking_step(state, "Profile", "Let me review their style preferences and purchase history. Understanding their go-to colors, fabrics, and brands will help me suggest items they'll actually love.")
        
        context = self.customer360.get_customer_context(state["user_id"])
        state["customer_context"] = context.model_dump()
        
        prefs = list(context.preferences)[:3] if context.preferences else []
        style_profile = context.style_profile or "modern"
        if prefs:
            self._add_thinking_step(state, "Profile", f"Their style leans {style_profile} with preferences for {', '.join(prefs)}. I'll prioritize items that match this aesthetic and feel.")
        else:
            self._add_thinking_step(state, "Profile", f"Based on their history, they prefer a {style_profile} aesthetic. I'll keep this in mind when curating options.")
        
        return state
    
    def _aggregate_context_node(self, state: GraphState) -> GraphState:
        location = state["normalized_intent"].get("location", "the destination")
        self._add_thinking_step(state, "Context", f"Pulling weather data for {location}. This tells me whether to recommend layers, rain protection, or lighter pieces.")
        
        intent = NormalizedIntent(**state["normalized_intent"])
        customer = CustomerContext(**state["customer_context"])
        
        enriched = self.context_aggregator.aggregate(intent, customer)
        state["enriched_context"] = enriched.model_dump()
        state["environmental_context"] = enriched.environmental.model_dump()
        
        weather = state["environmental_context"].get("weather") or {}
        temp = weather.get("temperature", "")
        desc = weather.get("description", "")
        try:
            temp_val = float(temp) if temp else None
        except (ValueError, TypeError):
            temp_val = None
        
        if temp_val is not None and desc:
            if "rain" in desc.lower():
                self._add_thinking_step(state, "Context", f"Weather shows {temp_val:.0f}°C with {desc}. I'll need to factor in rain protection—perhaps a water-resistant layer or umbrella-friendly outerwear.")
            elif temp_val < 15:
                self._add_thinking_step(state, "Context", f"Temperature is {temp_val:.0f}°C with {desc}. They'll want warm layers and possibly a coat. I'll prioritize cozy fabrics.")
            else:
                self._add_thinking_step(state, "Context", f"Weather looks comfortable at {temp_val:.0f}°C, {desc}. Light layers should work well for their activities.")
        else:
            self._add_thinking_step(state, "Context", "Gathered environmental context including local events and trends. This will help inform timely recommendations.")
        
        return state
    
    def _recommend_node(self, state: GraphState) -> GraphState:
        category = state["normalized_intent"].get("category", "versatile pieces")
        self._add_thinking_step(state, "Styling", f"Now searching for {category} that match their style profile and trip needs. Looking for items that can mix and match across different occasions.")
        
        enriched = EnrichedContext(**state["enriched_context"])
        
        products, explanation = self.recommender.get_recommendations(enriched)
        
        state["products"] = products
        state["final_response"] = explanation
        
        count = len(products)
        if count > 0:
            top_product = products[0].get("name", "items") if products else "items"
            self._add_thinking_step(state, "Styling", f"Found {count} excellent matches. Top pick: {top_product}. These selections balance style, practicality, and their personal preferences.")
        else:
            self._add_thinking_step(state, "Styling", "Expanding search criteria to find more suitable options that match their needs.")
        
        return state
    
    def process_message(self, user_id: int, message: str, conversation_history: list = None, existing_intent: dict = None) -> dict:
        has_conversation_history = conversation_history and len(conversation_history) > 0
        
        has_existing_context = existing_intent and (
            existing_intent.get("destination") or 
            existing_intent.get("destination_city") or
            existing_intent.get("destination_country") or
            existing_intent.get("travel_date") or
            existing_intent.get("activities") or
            existing_intent.get("trip_segments") or
            existing_intent.get("location") or
            existing_intent.get("_asked_optional") or
            existing_intent.get("_asked_activities")
        )
        
        is_new_conversation = not has_conversation_history and not has_existing_context
        
        if is_new_conversation and not is_travel_shopping_related(message):
            return {
                "response": OFF_TOPIC_MESSAGE,
                "products": [],
                "clarification_needed": False,
                "clarification_question": None,
                "updated_intent": existing_intent or {},
                "context": {}
            }
        
        initial_state: GraphState = {
            "messages": [],
            "user_id": user_id,
            "raw_query": message,
            "is_ambiguous": False,
            "clarification_question": "",
            "assistant_message": "",
            "clarifier_intent": existing_intent or {},
            "normalized_intent": {},
            "customer_context": {},
            "environmental_context": {},
            "enriched_context": {},
            "products": [],
            "final_response": "",
            "conversation_history": conversation_history or [],
            "detected_changes": {},
            "context_refresh_needed": False,
            "agent_thinking": []
        }
        
        final_state = self.graph.invoke(initial_state)
        
        normalized_intent = final_state.get("normalized_intent", {})
        clarifier_intent = final_state.get("clarifier_intent", {})
        
        if clarifier_intent.get("trip_segments") and not normalized_intent.get("trip_segments"):
            normalized_intent["trip_segments"] = clarifier_intent["trip_segments"]
        
        # Pass trip_duration_days from clarifier to normalized intent
        if clarifier_intent.get("trip_duration_days") and not normalized_intent.get("trip_duration_days"):
            normalized_intent["trip_duration_days"] = clarifier_intent["trip_duration_days"]
        
        detected_changes = final_state.get("detected_changes", {})
        
        return {
            "response": final_state["final_response"],
            "products": final_state["products"],
            "clarification_needed": final_state["is_ambiguous"],
            "clarification_question": final_state["clarification_question"],
            "updated_intent": clarifier_intent,
            "context": {
                "intent": normalized_intent,
                "environmental": final_state.get("environmental_context", {})
            },
            "detected_changes": detected_changes,
            "context_refresh_needed": final_state.get("context_refresh_needed", False),
            "agent_thinking": final_state.get("agent_thinking", [])
        }
