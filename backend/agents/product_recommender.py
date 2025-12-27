import json
from backend.agents.base import BaseAgent
from backend.rag.vector_store import ProductVectorStore
from backend.models.schemas import EnrichedContext, ProductResponse
from backend.database.connection import SessionLocal
from backend.database.models import Product
from typing import List, Dict, Any
from sqlalchemy import or_, and_

RECOMMENDER_PROMPT = """You are a formal travel and lifestyle recommender.

Given the user's travel prompt, destination, dates, weather context, and top 5 product recommendations, produce a structured, formal response that MUST include:

1) **Weather Overview** – temperatures (high/low), precipitation likelihood, wind, daylight, and seasonal notes
2) **Recommended Activities** – indoor/outdoor options justified by the weather and destination
3) **Clothing/Shoes/Accessories Preferences** – weather-aware and practical recommendations grounded in the forecast
4) **Itinerary** (Weekly or Daily) – when travel-related, a day-by-day or week-by-week plan with suggested activities and attire
5) **Local Events Summary** – Provide a concise summary of relevant local events (title, dates, venue, URL), indicate whether each event is likely outdoor or indoor, and mark events as `weather-sensitive` when appropriate. For each event, comment on how the event's conditions (outdoor/indoor and likely weather) should influence activities, itinerary choices, and product recommendations from the RAG results. If no events are available, state 'No events found for the requested dates.'
6) **Outfit/Product Recommendations** – specific items from the product catalog that align with the weather and activities
7) **Recommended Products from Catalog** – Include specific product information like long_description, family_name, material, available_colors, available_sizes, names, brands, prices, and availability. Generate a formal response that answers the user query using only the product catalog data from RAG results above. Do not add any generic product details or assumptions. If a field is missing, explicitly mention "Information not available." Maintain a professional and formal tone.

Incorporate the 5 recommended products from the RAG to support the plan.

If data is missing, state your assumptions clearly and proceed with best-practice recommendations.

Ensure the tone is formal, professional, and complete. All sections must be present."""

class ProductRecommenderAgent(BaseAgent):
    def __init__(self):
        super().__init__("ProductRecommender", RECOMMENDER_PROMPT)
        try:
            self.vector_store = ProductVectorStore()
            if self.vector_store.load_index():
                self.use_vector_store = True
                print(f"Loaded vector index with {len(self.vector_store.documents)} products")
            else:
                self.use_vector_store = False
                print("No vector index found, will use database fallback")
        except Exception as e:
            print(f"Vector store init error: {e}")
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
            query = db.query(Product).filter(Product.in_stock == True)
            
            conditions = []
            
            if context.intent.subcategory:
                conditions.append(Product.subcategory.ilike(f"%{context.intent.subcategory}%"))
            elif context.intent.category:
                conditions.append(Product.category.ilike(f"%{context.intent.category}%"))
            
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
            
            products = query.order_by(Product.rating.desc()).limit(num_results).all()
            
            if not products and context.intent.keywords:
                keyword_conditions = []
                for kw in context.intent.keywords[:3]:
                    keyword_conditions.append(or_(
                        Product.name.ilike(f"%{kw}%"),
                        Product.description.ilike(f"%{kw}%"),
                        Product.subcategory.ilike(f"%{kw}%"),
                        Product.material.ilike(f"%{kw}%")
                    ))
                if keyword_conditions:
                    query = db.query(Product).filter(Product.in_stock == True)
                    query = query.filter(or_(*keyword_conditions))
                    if context.intent.budget_max:
                        query = query.filter(Product.price <= context.intent.budget_max)
                    products = query.order_by(Product.rating.desc()).limit(num_results).all()
            
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
        
        weather_info = context.environmental.weather or {}
        events_info = context.environmental.local_events or []
        
        prompt = f"""
**User Query:** {context.intent.raw_query}

**Customer Profile:**
- Name: {context.customer.name}
- Location/Destination: {context.customer.location or 'Not specified'}
- Style Preferences: {context.customer.style_profile}
- Recent Purchases: {context.customer.recent_purchases[:3] if context.customer.recent_purchases else 'None'}

**Parsed Intent:**
- Category: {context.intent.category or 'Not specified'}
- Subcategory: {context.intent.subcategory or 'Not specified'}
- Occasion: {context.intent.occasion or 'Not specified'}
- Style: {context.intent.style or 'Not specified'}
- Budget: ${context.intent.budget_min or 0} - ${context.intent.budget_max or 'No limit'}

**Weather Context:**
- Temperature: {weather_info.get('temperature', 'N/A')}°C
- Conditions: {weather_info.get('description', 'N/A')}
- Season: {weather_info.get('season', 'Not specified')}

**Local Events:**
{json.dumps(events_info[:5], indent=2) if events_info else 'No events found for the requested dates.'}

**Trends:**
{context.environmental.trends[:5] if context.environmental.trends else 'N/A'}

**Top 5 Recommended Products from RAG:**
{json.dumps([{
    "name": p.get("name"),
    "family_name": p.get("name", "").split(" — ")[0] if " — " in p.get("name", "") else p.get("name"),
    "category": p.get("category"),
    "subcategory": p.get("subcategory"),
    "price": p.get("price"),
    "brand": p.get("brand"),
    "material": p.get("material", "Information not available"),
    "available_colors": p.get("colors", []),
    "description": p.get("description", "Information not available"),
    "in_stock": p.get("in_stock", True),
    "rating": p.get("rating")
} for p in products[:5]], indent=2)}

Based on the above context, generate a formal, structured response following all 7 required sections:
1) Weather Overview
2) Recommended Activities
3) Clothing/Shoes/Accessories Preferences
4) Itinerary (if travel-related)
5) Local Events Summary
6) Outfit/Product Recommendations
7) Recommended Products from Catalog

Use only the product data provided above. Maintain a professional and formal tone throughout.
"""
        
        response = self.invoke(prompt)
        return response
