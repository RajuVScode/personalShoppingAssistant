from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database.models import Customer, PurchaseHistory, Product
from backend.models.schemas import CustomerContext

class Customer360Agent:
    def __init__(self, db: Session):
        self.db = db
    
    def get_customer_context(self, customer_id: int) -> CustomerContext:
        customer_data = self._get_customer_from_new_table(customer_id)
        if customer_data:
            return customer_data
        
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            return CustomerContext(
                customer_id=customer_id,
                name="Guest",
                preferences={},
                style_profile={},
                size_info={},
                location=None,
                recent_purchases=[]
            )
        
        recent_purchases = (
            self.db.query(PurchaseHistory)
            .filter(PurchaseHistory.customer_id == customer_id)
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
            customer_id=customer.id,
            name=customer.name,
            preferences=customer.preferences or {},
            style_profile=customer.style_profile or {},
            size_info=customer.size_info or {},
            location=customer.location,
            recent_purchases=purchase_data
        )
    
    def _get_customer_from_new_table(self, customer_id: int) -> CustomerContext | None:
        cust_id_str = f"CUST-{str(customer_id).zfill(7)}"
        
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
                LIMIT 1
            """),
            {"cid": cust_id_str}
        ).fetchone()
        
        if not result:
            return None
        
        categories = result.categories_interested.split(",") if result.categories_interested else []
        brands = result.preferred_brands.split(",") if result.preferred_brands else []
        styles = result.preferred_styles.split(",") if result.preferred_styles else []
        
        location = None
        if result.city:
            location = f"{result.city}, {result.state}" if result.state else result.city
        
        return CustomerContext(
            customer_id=customer_id,
            name=f"{result.first_name} {result.last_name}",
            preferences={
                "categories_interested": categories,
                "price_sensitivity": result.price_sensitivity,
                "preferred_shopping_days": result.preferred_shopping_days
            },
            style_profile={
                "preferred_brands": brands,
                "preferred_styles": styles,
                "gender": result.gender
            },
            size_info={},
            location=location,
            recent_purchases=[],
            vip_flag=result.vip_flag,
            lifetime_value_cents=result.lifetime_value_cents,
            total_orders=result.total_orders
        )
