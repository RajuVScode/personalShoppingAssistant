from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.connection import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    location = Column(String(255))
    preferences = Column(JSON, default={})
    style_profile = Column(JSON, default={})
    size_info = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    purchase_history = relationship("PurchaseHistory", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer")

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
    sizes_available = Column(JSON, default=[])
    colors = Column(JSON, default=[])
    tags = Column(JSON, default=[])
    image_url = Column(String(500))
    in_stock = Column(Boolean, default=True)
    rating = Column(Float, default=0.0)
    material = Column(String(255))
    season = Column(String(255))
    care_instructions = Column(Text)

class PurchaseHistory(Base):
    __tablename__ = "purchase_history"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())
    quantity = Column(Integer, default=1)
    
    customer = relationship("Customer", back_populates="purchase_history")
    product = relationship("Product")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    messages = Column(JSON, default=[])
    context = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    customer = relationship("Customer", back_populates="conversations")
