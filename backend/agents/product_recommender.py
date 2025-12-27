import json
from backend.agents.base import BaseAgent
from backend.rag.vector_store import ProductVectorStore
from backend.models.schemas import EnrichedContext, ProductResponse
from backend.database.connection import SessionLocal
from backend.database.models import Product
from typing import List, Dict, Any
from sqlalchemy import or_, and_

RECOMMENDER_PROMPT = """You are a warm, knowledgeable personal shopping assistant who acts like a trusted stylist.

Your communication style:
- Warm and confident, like a personal stylist who knows the customer well
- Reference customer's known preferences naturally ("I know you love [brand]", "Given your preference for [style]")
- Structure trips into clear phases/missions with weather context
- Create complete OUTFIT BUNDLES with reasoning for each item
- Explain WHY each product suits this customer specifically

Response Structure for Travel Recommendations:

1) **Personal Greeting** - Welcome the customer by name, acknowledge their trip, mention you already know their style/preferences

2) **Trip Structure** - Break the trip into phases (Week 1, Week 2 OR by destination):
   - Destination name and dates
   - Expected weather (temperature range, conditions)
   - Key activities planned
   - Style direction (e.g., "elevated smart-casual", "functional outdoor")
   - Required outfit sets

3) **Outfit Bundles** - For each phase, create named outfit bundles like:
   - "City Explorer" - smart-casual daywear
   - "Museum Day" - comfortable but polished
   - "Dinner Night" - elevated evening wear
   - "Adventure Ready" - functional outdoor gear
   
   For each bundle, list items with WHY reasoning:
   - Item name, brand, price
   - Why it suits THIS customer ("matches your preferred [style]", "aligns with your love of [brand]")
   - Why it works for the weather/activity

4) **Consolidated Pack Summary** - Total items, outfit combinations possible, estimated pack weight

Always use the customer's known preferences (brands, styles, categories) to personalize recommendations.
If customer asks for alternatives or has budget concerns, offer options warmly."""

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
        
        prefs = context.customer.preferences or {}
        style = context.customer.style_profile or {}
        preferred_brands = style.get("preferred_brands", [])
        preferred_styles = style.get("preferred_styles", [])
        categories = prefs.get("categories_interested", [])
        price_sensitivity = prefs.get("price_sensitivity", "medium")
        
        products_json = json.dumps([{
            "name": p.get("name"),
            "category": p.get("category"),
            "subcategory": p.get("subcategory"),
            "price": p.get("price"),
            "brand": p.get("brand"),
            "colors": p.get("colors", []),
            "description": p.get("description", "")
        } for p in products[:5]], indent=2)
        
        prompt = f"""
**Customer Profile (YOU KNOW THIS CUSTOMER):**
- Name: {context.customer.name}
- VIP Status: {"Yes" if context.customer.vip_flag else "No"}
- Total Orders: {context.customer.total_orders or 0}
- Home Location: {context.customer.location or 'Not specified'}
- Preferred Brands: {', '.join(preferred_brands) if preferred_brands else 'Not specified'}
- Preferred Styles: {', '.join(preferred_styles) if preferred_styles else 'Not specified'}
- Categories Interested: {', '.join(categories) if categories else 'Not specified'}
- Price Sensitivity: {price_sensitivity}
- Gender: {style.get('gender', 'Not specified')}

**Travel Query:** {context.intent.raw_query}

**Trip Details:**
- Destination: {context.customer.location or context.intent.occasion or 'Not specified'}
- Budget Range: ${context.intent.budget_min or 0} - ${context.intent.budget_max or 'flexible'}

**Weather at Destination:**
- Temperature: {weather_info.get('temperature', 'N/A')}°C (High: {weather_info.get('temp_max', 'N/A')}°C / Low: {weather_info.get('temp_min', 'N/A')}°C)
- Conditions: {weather_info.get('description', 'Variable')}
- Season: {weather_info.get('season', 'transitional')}

**Local Events:**
{json.dumps(events_info[:3], indent=2) if events_info else 'No specific events found.'}

**Available Products from Catalog (use these for outfit bundles):**
{products_json}

Generate a warm, personalized response following this structure:

1) **Personal Greeting** - Welcome {context.customer.name} by name, acknowledge you know their style preferences and favorite brands

2) **Trip Structure** - Break the trip into phases with:
   - Destination and dates
   - Weather forecast (temperature range, conditions, what to expect)
   - Key activities planned
   - Style direction based on customer's known preferences
   - Required outfit types for each phase

3) **Outfit Bundles** - Create 2-3 named outfit bundles using the products above:
   - Give each bundle a descriptive name (e.g., "City Explorer", "Museum Day", "Dinner Night")
   - For each item include: product name, brand, price
   - Explain WHY it suits {context.customer.name} specifically (reference their preferred brands/styles)
   - Note how it works for the weather/activity

4) **Daily Itinerary** (optional) - If relevant, suggest activities for each day with recommended attire

5) **Consolidated Pack Summary** - Total items, possible outfit combinations, travel-ready notes

Be warm and confident like a trusted personal stylist. Reference their preferences naturally. Use ONLY the products listed above.
"""
        
        response = self.invoke(prompt)
        return response
