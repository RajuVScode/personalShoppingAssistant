"""
Product Recommender Agent Module

This module implements the ProductRecommenderAgent, responsible for generating
personalized product recommendations based on user context and preferences.

Key Responsibilities:
- Build semantic search queries from user context (destination, weather, activities)
- Search product catalog using vector similarity (RAG approach)
- Apply mandatory size filtering to match user preferences
- Diversify recommendations across product categories
- Generate natural language explanations for recommendations

The agent uses a combination of:
1. Vector store for semantic product search
2. Database fallback for basic filtering
3. LLM for generating recommendation explanations
"""

import json
from datetime import datetime
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
3) **Itinerary** – CRITICAL: Match the itinerary length EXACTLY to the trip duration provided. If the trip is 1 day, provide a single-day itinerary. If 3 days, provide 3 days. Do NOT default to 3 days or create days beyond the actual trip duration. Include suggested activities and attire for each day.
4) **Local Events Summary** – Concise summary of relevant local events (title, dates, venue), indicate outdoor/indoor, and note weather-sensitivity. If no events, state 'No events found.'
5) **Clothing, Shoes & Accessories Recommendations** – Provide outfit guidance and recommendations narrative. Explain WHY each product suits the trip based on weather, activities, and customer style. Reference product names with brief rationale. Do NOT repeat full catalog details here - just recommend with brief explanations.
6) **Product Catalog Details** – For each recommended product, provide COMPLETE catalog information: name, brand, price, material, available_colors, available_sizes, description, and availability.

IMPORTANT: The itinerary must match the exact trip duration. For a 1-day trip, only show 1 day.

If data is missing, state your assumptions clearly and proceed with best-practice recommendations.

Ensure the tone is formal, professional, and complete. All sections must be present."""

class ProductRecommenderAgent(BaseAgent):
    """
    AI agent for generating personalized product recommendations.
    
    Uses a RAG (Retrieval-Augmented Generation) approach combining:
    - Vector similarity search for semantic matching
    - Rule-based filters for size/brand preferences
    - LLM for natural language explanations
    
    Attributes:
        vector_store: ProductVectorStore instance for semantic search
        use_vector_store: Whether vector store is available and loaded
    """
    
    def __init__(self):
        """Initialize the recommender with vector store and LLM connection."""
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
        """
        Generate product recommendations based on enriched user context.
        
        Args:
            context: EnrichedContext containing intent, customer profile,
                    weather data, and other contextual information
            num_results: Maximum number of products to return
            
        Returns:
            Tuple of (products_list, explanation_string)
            
        Flow:
        1. Build semantic search query from context
        2. Search vector store (or fallback to database)
        3. Apply mandatory size filtering
        4. Generate natural language explanation
        """
        products = []
        
        if self.use_vector_store and self.vector_store:
            try:
                search_query = self._build_search_query(context)
                filters = self._build_filters(context)
                raw_products = self.vector_store.search(search_query, k=num_results * 3, filters=filters)
                products = self._diversify_by_category(raw_products, num_results)
            except Exception:
                pass
        
        if not products:
            products = self._db_fallback_search(context, num_results)
        
        # MANDATORY: Final size filter to guarantee no wrong-sized products
        if context.intent.size:
            user_size = context.intent.size.upper().strip()
            products = self._strict_size_filter(products, user_size)
            print(f"[DEBUG] Final strict size filter applied: {len(products)} products after filtering for size {user_size}")
        
        explanation = self._generate_explanation(context, products)
        
        return products, explanation
    
    def _strict_size_filter(self, products: List[Dict[str, Any]], user_size: str) -> List[Dict[str, Any]]:
        """
        MANDATORY filter to ensure only products in the user's exact size are returned.
        Product names contain the variant (e.g., "Montclair Dresses — Black / M").
        We filter to match ONLY the user's specified size in the variant.
        """
        if not user_size:
            return products
        
        filtered = []
        for product in products:
            name = product.get("name", "")
            
            # Check if product name contains size variant "/ SIZE"
            if " / " in name:
                parts = name.split(" / ")
                if len(parts) >= 2:
                    variant_size = parts[-1].strip().upper()
                    if variant_size == user_size:
                        filtered.append(product)
                        print(f"[DEBUG] Strict filter match: {name}")
                    else:
                        print(f"[DEBUG] Strict filter reject: {name} (has {variant_size}, want {user_size})")
            else:
                # Product without size variant in name - include it
                filtered.append(product)
        
        return filtered
    
    def _diversify_by_category(self, products: List[Dict[str, Any]], num_results: int) -> List[Dict[str, Any]]:
        if not products:
            return []
        
        seen_subcategories = set()
        seen_names = set()
        diversified = []
        
        for product in products:
            subcategory = product.get("subcategory", "").lower()
            base_name = product.get("name", "").split("—")[0].strip().lower()
            
            if base_name in seen_names:
                continue
            
            if subcategory and subcategory in seen_subcategories:
                continue
            
            diversified.append(product)
            if subcategory:
                seen_subcategories.add(subcategory)
            seen_names.add(base_name)
            
            if len(diversified) >= num_results:
                break
        
        if len(diversified) < num_results:
            for product in products:
                if product not in diversified:
                    base_name = product.get("name", "").split("—")[0].strip().lower()
                    if base_name not in seen_names:
                        diversified.append(product)
                        seen_names.add(base_name)
                        if len(diversified) >= num_results:
                            break
        
        return diversified[:num_results]
    
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
        
        # Size filter - mandatory when specified by user
        if context.intent.size:
            filters["size"] = context.intent.size
            print(f"[DEBUG] Size filter applied: {context.intent.size}")
        
        # User-specified brand takes priority
        if context.intent.brand:
            filters["brand"] = context.intent.brand
        elif context.customer.preferences:
            # Fall back to customer's preferred brands if no specific brand requested
            prefs = context.customer.preferences
            if prefs.get("preferred_brands"):
                filters["preferred_brands"] = prefs["preferred_brands"]
        
        if context.customer.preferences:
            prefs = context.customer.preferences
            if prefs.get("categories_interested"):
                filters["categories_interested"] = prefs["categories_interested"]
        
        return filters
    
    def _db_fallback_search(self, context: EnrichedContext, num_results: int = 5) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(Product).filter(Product.in_stock == True)
            
            conditions = []
            
            # If user specified a brand in the intent, prioritize that brand
            if context.intent.brand:
                conditions.append(Product.brand.ilike(f"%{context.intent.brand}%"))
            
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
            
            preferred_brands = []
            categories_interested = []
            if context.customer.preferences:
                prefs = context.customer.preferences
                preferred_brands = prefs.get("preferred_brands", []) or []
                categories_interested = prefs.get("categories_interested", []) or []
            
            # Only add preferred brands if no specific brand was requested
            if preferred_brands and not context.intent.brand:
                brand_conditions = [Product.brand.ilike(f"%{brand}%") for brand in preferred_brands[:5]]
                conditions.append(or_(*brand_conditions))
            
            if conditions:
                query = query.filter(and_(*conditions))
            
            products = query.order_by(Product.rating.desc()).limit(num_results * 3).all()
            
            # If user specified a brand but no products found, try brand-only search
            if not products and context.intent.brand:
                brand_query = db.query(Product).filter(Product.in_stock == True)
                brand_query = brand_query.filter(Product.brand.ilike(f"%{context.intent.brand}%"))
                products = brand_query.order_by(Product.rating.desc()).limit(num_results * 3).all()
            
            # Only try other fallbacks if NO explicit brand was requested
            if not products and not context.intent.brand:
                if categories_interested:
                    cat_conditions = []
                    for cat in categories_interested[:3]:
                        cat_conditions.append(or_(
                            Product.category.ilike(f"%{cat}%"),
                            Product.subcategory.ilike(f"%{cat}%")
                        ))
                    if cat_conditions:
                        query = db.query(Product).filter(Product.in_stock == True)
                        query = query.filter(or_(*cat_conditions))
                        if context.intent.budget_max:
                            query = query.filter(Product.price <= context.intent.budget_max)
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
            
            # Apply mandatory size filter if user specified a size
            # Filter by size in product NAME (e.g., "Sandals — Black / M")
            user_size = context.intent.size
            if user_size:
                user_size_upper = user_size.upper().strip()
                print(f"[DEBUG] Filtering DB products by size in name: {user_size_upper}")
                filtered_products = []
                for p in products:
                    name = p.name or ""
                    # Check if product name contains size variant "/ SIZE"
                    if " / " in name:
                        parts = name.split(" / ")
                        if len(parts) >= 2:
                            variant_size = parts[-1].strip().upper()
                            if variant_size == user_size_upper:
                                filtered_products.append(p)
                                print(f"[DEBUG] Size match: {name}")
                    else:
                        # Product without size variant in name - include it
                        filtered_products.append(p)
                products = filtered_products
                print(f"[DEBUG] After size filter: {len(products)} products remain")
            
            raw_products = [{
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
                "sizes_available": p.sizes_available,
                "tags": p.tags
            } for p in products]
            
            return self._diversify_by_category(raw_products, num_results)
        finally:
            db.close()
    
    def _build_search_query(self, context: EnrichedContext) -> str:
        parts = []
        
        if context.intent.brand:
            parts.append(f"brand {context.intent.brand}")
            
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
        
        if context.customer.preferences:
            prefs = context.customer.preferences
            if prefs.get("preferred_brands"):
                parts.extend(prefs["preferred_brands"][:3])
            if prefs.get("categories_interested"):
                parts.extend(prefs["categories_interested"][:3])
        
        return " ".join(parts)
    
    def _parse_trip_duration(self, occasion: str) -> tuple:
        if not occasion:
            return None, None, 1
        try:
            if " to " in occasion:
                parts = occasion.replace("travel on ", "").split(" to ")
                if len(parts) == 2:
                    start = datetime.strptime(parts[0].strip(), "%Y-%m-%d")
                    end = datetime.strptime(parts[1].strip(), "%Y-%m-%d")
                    duration = (end - start).days + 1
                    return parts[0].strip(), parts[1].strip(), max(1, duration)
            else:
                date_str = occasion.replace("travel on ", "").strip()
                if "-" in date_str and len(date_str) == 10:
                    return date_str, date_str, 1
        except:
            pass
        return None, None, 1
    
    def _format_segments_context(self, segments) -> str:
        if not segments:
            return ""
        
        result = []
        cumulative_day = 1
        
        for i, seg in enumerate(segments):
            if hasattr(seg, 'destination'):
                dest = seg.destination
                start = seg.start_date
                end = seg.end_date
                weather = seg.weather or {}
                events = seg.local_events or []
            else:
                dest = seg.get('destination', 'Unknown')
                start = seg.get('start_date', '')
                end = seg.get('end_date', '')
                weather = seg.get('weather', {})
                events = seg.get('local_events', [])
            
            try:
                start_dt = datetime.strptime(start, "%Y-%m-%d")
                end_dt = datetime.strptime(end, "%Y-%m-%d")
                segment_days = (end_dt - start_dt).days + 1
            except:
                segment_days = 1
            
            day_range = f"Day {cumulative_day}" if segment_days == 1 else f"Day {cumulative_day}-{cumulative_day + segment_days - 1}"
            
            segment_info = f"""
**Segment {i+1}: {dest} ({start} to {end}) - {day_range} of trip**
- Duration: {segment_days} day(s)
- Weather: {weather.get('temperature', 'N/A')}°C, {weather.get('description', 'N/A')}
- Local Events: {json.dumps(events[:3], indent=2) if events else 'No events found'}
"""
            result.append(segment_info)
            cumulative_day += segment_days
        
        return "\n".join(result)
    
    def _calculate_actual_trip_days(self, segments) -> int:
        total_days = 0
        for seg in segments:
            if hasattr(seg, 'start_date'):
                start = seg.start_date
                end = seg.end_date
            else:
                start = seg.get('start_date', '')
                end = seg.get('end_date', '')
            
            try:
                start_dt = datetime.strptime(start, "%Y-%m-%d")
                end_dt = datetime.strptime(end, "%Y-%m-%d")
                total_days += (end_dt - start_dt).days + 1
            except:
                total_days += 1
        
        return max(1, total_days)
    
    def _generate_explanation(
        self, 
        context: EnrichedContext, 
        products: List[Dict[str, Any]]
    ) -> str:
        if not products:
            return "I couldn't find products matching your criteria. Could you try a different search?"
        
        weather_info = context.environmental.weather or {}
        events_info = context.environmental.local_events or []
        segments = getattr(context.environmental, 'segments', None) or []
        
        is_multi_destination = len(segments) > 1
        
        start_date, end_date, duration_days = self._parse_trip_duration(context.intent.occasion)
        
        if is_multi_destination:
            duration_days = self._calculate_actual_trip_days(segments)
            segments_section = self._format_segments_context(segments)
            destination_info = ", ".join([
                s.destination if hasattr(s, 'destination') else s.get('destination', '') 
                for s in segments
            ])
        else:
            segments_section = ""
            destination_info = getattr(context.intent, 'location', None) or 'Not specified'
        
        customer_prefs = context.customer.preferences or {}
        preferred_brands = customer_prefs.get("preferred_brands", [])
        categories_interested = customer_prefs.get("categories_interested", [])
        price_sensitivity = customer_prefs.get("price_sensitivity", "Not specified")
        
        prompt = f"""
**User Query:** {context.intent.raw_query}

**Customer Profile:**
- Name: {context.customer.name}
- Home Location: {context.customer.location or 'Not specified'}
- Travel Destination(s): {destination_info}
- Style Preferences: {context.customer.style_profile}
- Recent Purchases: {context.customer.recent_purchases[:3] if context.customer.recent_purchases else 'None'}

**CUSTOMER SHOPPING PREFERENCES (CRITICAL - Personalize recommendations based on these):**
- Preferred Brands: {', '.join(preferred_brands) if preferred_brands else 'No specific brand preference'}
- Categories of Interest: {', '.join(categories_interested) if categories_interested else 'All categories'}
- Price Sensitivity: {price_sensitivity}
- VIP Customer: {context.customer.style_profile.get('vip_customer', False)}

IMPORTANT: When recommending products, PRIORITIZE items from the customer's preferred brands and categories. Mention in the recommendations why each product aligns with the customer's preferences.

**Parsed Intent:**
- Category: {context.intent.category or 'Not specified'}
- Subcategory: {context.intent.subcategory or 'Not specified'}
- Occasion: {context.intent.occasion or 'Not specified'}
- Style: {context.intent.style or 'Not specified'}
- Budget: ${context.intent.budget_min or 0} - ${context.intent.budget_max or 'No limit'}

**TRIP DURATION (CRITICAL - MUST FOLLOW):**
- Start Date: {start_date or 'Not specified'}
- End Date: {end_date or 'Not specified'}
- Duration: {duration_days} day(s)
- IMPORTANT: The itinerary MUST be exactly {duration_days} day(s). Do NOT create more days.
- CRITICAL DAY NUMBERING: Always number days as "Day 1", "Day 2", "Day 3", etc. starting from Day 1. Do NOT use day-of-year numbers or any other numbering scheme. For a 7-day trip, use Day 1 through Day 7 only.
{"- MULTI-DESTINATION TRIP: Include weather and events for EACH destination separately." if is_multi_destination else ""}
{segments_section if is_multi_destination else f'''
**Weather Context:**
- Temperature: {weather_info.get('temperature', 'N/A')}°C
- Conditions: {weather_info.get('description', 'N/A')}
- Season: {weather_info.get('season', 'Not specified')}

**Local Events:**
{json.dumps(events_info[:5], indent=2) if events_info else 'No events found for the requested dates.'}
'''}

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

Generate a formal response with these sections:
{"1) Weather Overview - Include weather for EACH destination separately" if is_multi_destination else "1) Weather Overview"}
2) Recommended Activities{" for each destination" if is_multi_destination else ""}
3) Itinerary - EXACTLY {duration_days} day(s). Number days as Day 1, Day 2, Day 3... up to Day {duration_days}. Include the actual date in parentheses, e.g., "Day 1 ({start_date})".{" Show which days are in each city." if is_multi_destination else ""}
4) Local Events Summary{" by destination" if is_multi_destination else ""}
5) Clothing & Accessories Recommendations - Brief outfit guidance explaining WHY each product suits the trip. Reference product names with rationale.{" Consider varying weather conditions across destinations." if is_multi_destination else ""} Do NOT list detailed specs here.
6) Product Catalog Details - Full product info (name, brand, price, material, colors, sizes, description) for each recommendation.

Use only the product data provided. Maintain a professional tone.
"""
        
        try:
            response = self.invoke(prompt)
            return response
        except Exception as e:
            print(f"LLM explanation failed: {e}")
            return self._generate_fallback_explanation(context, products)
    
    def _generate_fallback_explanation(
        self,
        context: EnrichedContext,
        products: List[Dict[str, Any]]
    ) -> str:
        """Generate a simple explanation when LLM fails."""
        destination = getattr(context.intent, 'location', None) or 'your destination'
        weather_info = context.environmental.weather or {}
        temp = weather_info.get('temperature', 'N/A')
        conditions = weather_info.get('description', 'varied conditions')
        
        product_list = "\n".join([
            f"- **{p.get('name')}** by {p.get('brand')} - ${p.get('price', 'N/A')}"
            for p in products[:5]
        ])
        
        return f"""## Travel Recommendations for {destination}

### Weather Overview
Expected temperature: {temp}°C with {conditions}.

### Recommended Products
Based on your travel plans and preferences, here are my top recommendations:

{product_list}

These items have been selected to match your trip requirements. Each product is in stock and ready to ship."""
