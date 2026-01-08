from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.connection import Base

class Customer(Base):
    __tablename__ = "customers"
    
    customer_id = Column(String(20), primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(30))
    date_of_birth = Column(Date)
    gender = Column(String(30))
    preferred_channel = Column(String(20))
    marketing_opt_in = Column(Boolean, default=False)
    vip_flag = Column(Boolean, default=False)
    lifetime_value_cents = Column(Integer, default=0)
    avg_order_value_cents = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    preferred_store_id = Column(String(20))
    notes = Column(Text)
    password = Column(String(255), nullable=False, default="password123")
    
    purchase_history = relationship("PurchaseHistory", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer")
    preferences = relationship("CustomerPreferences", back_populates="customer", uselist=False)
    addresses = relationship("CustomerAddress", back_populates="customer")

class CustomerAddress(Base):
    __tablename__ = "customer_addresses"
    
    address_id = Column(String(30), primary_key=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), nullable=False)
    label = Column(String(50))
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(100), default="USA")
    is_default_shipping = Column(Boolean, default=False)
    is_default_billing = Column(Boolean, default=False)
    
    customer = relationship("Customer", back_populates="addresses")

class CustomerPreferences(Base):
    __tablename__ = "customer_preferences"
    
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), primary_key=True)
    categories_interested = Column(JSON, default=list)
    price_sensitivity = Column(String(20))
    preferred_brands = Column(JSON, default=list)
    preferred_styles = Column(JSON, default=list)
    preferred_shopping_days = Column(String(30))
    
    customer = relationship("Customer", back_populates="preferences")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    subcategory = Column(String(100))
    price = Column(Float)
    brand = Column(String(100))
    gender = Column(String(50))
    sizes_available = Column(JSON, default=list)
    colors = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    image_url = Column(String(500))
    in_stock = Column(Boolean, default=True)
    rating = Column(Float, default=0.0)
    material = Column(String(255))
    season = Column(String(255))
    care_instructions = Column(Text)

class PurchaseHistory(Base):
    __tablename__ = "purchase_history"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())
    quantity = Column(Integer, default=1)
    
    customer = relationship("Customer", back_populates="purchase_history")
    product = relationship("Product")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"))
    messages = Column(JSON, default=list)
    context = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    customer = relationship("Customer", back_populates="conversations")
