from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database.models import Customer, PurchaseHistory, Product
from backend.models.schemas import CustomerContext
from typing import Union

class Customer360Agent:
    def __init__(self, db: Session):
        self.db = db
    
    def get_customer_context(self, customer_id: Union[int, str]) -> CustomerContext:
        cust_id_str = str(customer_id) if isinstance(customer_id, int) else customer_id
        
        if not cust_id_str.startswith("CUST-"):
            cust_id_str = f"CUST-{int(customer_id):07d}"
        
        result = self.db.execute(
            text("""
                SELECT c.customer_id, c.first_name, c.last_name, c.email, c.gender,
                       c.vip_flag, c.lifetime_value_cents, c.total_orders,
                       p.categories_interested, p.price_sensitivity, p.preferred_brands,
                       p.preferred_styles, p.preferred_shopping_days,
                       a.city, a.state, a.country
                FROM customers c
                LEFT JOIN customer_preferences p ON c.customer_id = p.customer_id
                LEFT JOIN customer_addresses a ON c.customer_id = a.customer_id AND a.is_default_shipping = true
                WHERE c.customer_id = :cid
            """),
            {"cid": cust_id_str}
        ).fetchone()
        
        if not result:
            return CustomerContext(
                customer_id=customer_id,
                name="Guest",
                preferences={},
                style_profile={},
                size_info={},
                location=None,
                recent_purchases=[]
            )
        
        location = None
        if result.city:
            location = f"{result.city}, {result.state or ''}, {result.country or 'USA'}".strip(", ")
        
        preferences = {
            "categories_interested": result.categories_interested or [],
            "price_sensitivity": result.price_sensitivity,
            "preferred_brands": result.preferred_brands or [],
            "preferred_shopping_days": result.preferred_shopping_days,
        }
        
        style_profile = {
            "preferred_styles": result.preferred_styles or [],
            "vip_customer": result.vip_flag,
            "lifetime_value": result.lifetime_value_cents / 100 if result.lifetime_value_cents else 0,
        }
        
        numeric_cust_id = int(customer_id) if isinstance(customer_id, int) else int(cust_id_str.replace("CUST-", ""))
        
        recent_purchases = (
            self.db.query(PurchaseHistory)
            .filter(PurchaseHistory.customer_id == numeric_cust_id)
            .order_by(PurchaseHistory.purchased_at.desc())
            .limit(10)
            .all()
        )
        
        purchase_data = []
        for purchase in recent_purchases:
            product = self.db.query(Product).filter(Product.id == purchase.product_id).first()
            if product:
                purchase_data.append({
                    "product_name": product.name,
                    "category": product.category,
                    "brand": product.brand,
                    "price": product.price,
                    "purchased_at": str(purchase.purchased_at)
                })
        
        return CustomerContext(
            customer_id=result.customer_id,
            name=f"{result.first_name} {result.last_name}",
            preferences=preferences,
            style_profile=style_profile,
            size_info={},
            location=location,
            recent_purchases=purchase_data
        )
