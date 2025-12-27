import json
from backend.agents.base import BaseAgent
from backend.rag.vector_store import ProductVectorStore
from backend.models.schemas import EnrichedContext, ProductResponse
from backend.database.connection import SessionLocal
from backend.database.models import Product
from typing import List, Dict, Any
from sqlalchemy import or_, and_

RECOMMENDER_PROMPT = """You are a Product Recommendation Agent for a personalized shopping experience.
Your role is to explain product recommendations based on the customer's context and preferences.

Given:
1. Customer profile (preferences, purchase history, style)
2. Current intent (what they're looking for)
3. Environmental context (weather, events, trends)
4. Retrieved products from the catalog

Generate a personalized, conversational response that:
- Acknowledges their specific request
- Explains WHY each product matches their needs
- References relevant context (weather, upcoming events, their style)
- Is warm, helpful, and not pushy
- Highlights 3-5 top recommendations

Be concise but informative. Make connections between their preferences and the products."""

class ProductRecommenderAgent(BaseAgent):
    def __init__(self):
        super().__init__("ProductRecommender", RECOMMENDER_PROMPT)
        try:
            self.vector_store = ProductVectorStore()
            self.use_vector_store = True
        except Exception:
            self.vector_store = None
            self.use_vector_store = False
    
    def get_recommendations(
        self, 
        context: EnrichedContext,
        num_results: int = 5
    ) -> tuple[List[Dict[str, Any]], str]:
        products = []
        
        if self.use_vector_store and self.vector_store:
            try:
                search_query = self._build_search_query(context)
                filters = self._build_filters(context)
                products = self.vector_store.search(search_query, k=num_results, filters=filters)
            except Exception:
                pass
        
        if not products:
            products = self._db_fallback_search(context, num_results)
        
        explanation = self._generate_explanation(context, products)
        
        return products, explanation
    
    def _build_filters(self, context: EnrichedContext) -> dict:
        filters = {}
        if context.intent.budget_max:
            filters["budget_max"] = context.intent.budget_max
        if context.intent.budget_min:
            filters["budget_min"] = context.intent.budget_min
        if context.intent.category:
            filters["category"] = context.intent.category
        if context.intent.gender:
            filters["gender"] = context.intent.gender
        return filters
    
    def _db_fallback_search(self, context: EnrichedContext, num_results: int = 5) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(Product)
            
            conditions = []
            
            if context.intent.category:
                conditions.append(Product.category.ilike(f"%{context.intent.category}%"))
            
            if context.intent.subcategory:
                conditions.append(Product.subcategory.ilike(f"%{context.intent.subcategory}%"))
            
            if context.intent.budget_max:
                conditions.append(Product.price <= context.intent.budget_max)
            
            if context.intent.budget_min:
                conditions.append(Product.price >= context.intent.budget_min)
            
            if context.intent.gender:
                conditions.append(or_(
                    Product.gender.ilike(f"%{context.intent.gender}%"),
                    Product.gender.ilike("%unisex%")
                ))
            
            if conditions:
                query = query.filter(and_(*conditions))
            
            products = query.limit(num_results).all()
            
            return [{
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "subcategory": p.subcategory,
                "price": p.price,
                "brand": p.brand,
                "gender": p.gender,
                "image_url": p.image_url,
                "in_stock": p.in_stock,
                "rating": p.rating,
                "colors": p.colors,
                "tags": p.tags
            } for p in products]
        finally:
            db.close()
    
    def _build_search_query(self, context: EnrichedContext) -> str:
        parts = []
        
        if context.intent.raw_query:
            parts.append(context.intent.raw_query)
        
        if context.intent.category:
            parts.append(context.intent.category)
        if context.intent.subcategory:
            parts.append(context.intent.subcategory)
        if context.intent.occasion:
            parts.append(f"for {context.intent.occasion}")
        if context.intent.style:
            parts.append(context.intent.style)
        if context.intent.color_preferences:
            parts.append(" ".join(context.intent.color_preferences))
        
        if context.environmental.weather:
            weather = context.environmental.weather
            if weather.get("temperature"):
                temp = weather["temperature"]
                if temp < 10:
                    parts.append("warm winter cold weather")
                elif temp > 25:
                    parts.append("light summer breathable")
        
        if context.customer.style_profile:
            profile = context.customer.style_profile
            if profile.get("preferred_styles"):
                parts.extend(profile["preferred_styles"])
        
        return " ".join(parts)
    
    def _generate_explanation(
        self, 
        context: EnrichedContext, 
        products: List[Dict[str, Any]]
    ) -> str:
        if not products:
            return "I couldn't find products matching your criteria. Could you try a different search?"
        
        prompt = f"""
Customer: {context.customer.name}
Location: {context.customer.location or 'Not specified'}
Style preferences: {context.customer.style_profile}
Recent purchases: {context.customer.recent_purchases[:3] if context.customer.recent_purchases else 'None'}

Current request: {context.intent.raw_query}
Parsed intent: Category: {context.intent.category}, Style: {context.intent.style}, Occasion: {context.intent.occasion}

Weather: {context.environmental.weather}
Trending: {context.environmental.trends[:3] if context.environmental.trends else 'N/A'}

Products found:
{json.dumps([{
    "name": p.get("name"),
    "category": p.get("category"),
    "price": p.get("price"),
    "brand": p.get("brand")
} for p in products[:5]], indent=2)}

Generate a personalized, friendly recommendation explanation (2-3 paragraphs max).
"""
        
        response = self.invoke(prompt)
        return response
