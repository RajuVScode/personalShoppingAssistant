from sqlalchemy.orm import Session
from backend.database.models import Customer, PurchaseHistory, Product
from backend.models.schemas import CustomerContext

class Customer360Agent:
    def __init__(self, db: Session):
        self.db = db
    
    def get_customer_context(self, customer_id: int) -> CustomerContext:
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
