"""
FastAPI Backend Main Module

This is the main entry point for the AI Shopping Experience backend API.
It provides RESTful endpoints for the shopping assistant application.

Key Endpoints:
- /api/health: Health check endpoint
- /api/login: Customer authentication
- /api/chat: Conversational AI shopping assistant
- /api/customer360/{id}: Customer profile and preferences
- /api/customers/{id}: Customer profile management (GET/PUT)
- /api/products: Product catalog management
- /api/conversation/{id}: Conversation history management

Architecture:
- FastAPI for REST API framework
- SQLAlchemy for database ORM
- Multi-agent orchestrator for AI conversations
- PostgreSQL for data persistence
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from contextlib import asynccontextmanager

from backend.database.connection import engine, get_db, Base
from backend.database.models import Customer, Product, PurchaseHistory, Conversation, CustomerAddress
from pydantic import BaseModel
from backend.models.schemas import (
    ChatRequest, ChatResponse, CustomerCreate, CustomerResponse,
    ProductCreate, ProductResponse
)
from backend.agents.orchestrator import ShoppingOrchestrator
from backend.rag.vector_store import ProductVectorStore
from backend.database.seed import seed_database

db_initialized = False

def initialize_database():
    """
    Initialize the database tables and seed with sample data if needed.
    
    This function:
    1. Creates all database tables from SQLAlchemy models
    2. Seeds the database with sample products and customers if empty
    3. Creates vector index for product search if API key is available
    
    Returns:
        True if initialization succeeded, False otherwise
    """
    global db_initialized
    if db_initialized:
        return True
    
    try:
        print("Attempting database initialization...", flush=True)
        Base.metadata.create_all(bind=engine)
        print("Database tables created", flush=True)
        
        db = next(get_db())
        try:
            print("Checking for existing products...", flush=True)
            existing_products = db.query(Product).first()
            if not existing_products:
                print("Seeding database...", flush=True)
                seed_database(db)
                
                products = db.query(Product).all()
                product_data = [{
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "category": p.category,
                    "subcategory": p.subcategory,
                    "price": p.price,
                    "brand": p.brand,
                    "gender": p.gender,
                    "colors": p.colors,
                    "tags": p.tags,
                    "image_url": p.image_url,
                    "in_stock": p.in_stock,
                    "rating": p.rating
                } for p in products]
                
                if os.getenv("AZURE_OPENAI_API_KEY"):
                    try:
                        vector_store = ProductVectorStore()
                        vector_store.create_index(product_data)
                    except Exception as e:
                        print(f"Warning: Could not create vector index: {e}", flush=True)
            else:
                print("Database already seeded", flush=True)
        finally:
            db.close()
        
        db_initialized = True
        print("Database initialization complete!", flush=True)
        return True
    except Exception as e:
        print(f"Database initialization failed (will retry on request): {e}", flush=True)
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    print("Application startup complete (database may initialize lazily)", flush=True)
    yield

app = FastAPI(
    title="AI Shopping Experience",
    description="Multi-agent AI-powered personalized shopping platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    customer_id: str
    password: str

@app.get("/api/health")
def health_check():
    global db_initialized
    if not db_initialized:
        initialize_database()
    return {
        "status": "healthy", 
        "service": "AI Shopping Experience",
        "database": "connected" if db_initialized else "connecting"
    }

@app.post("/api/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    global db_initialized
    if not db_initialized:
        initialize_database()
    
    try:
        from sqlalchemy import text
        result = db.execute(
            text("SELECT customer_id, first_name, last_name, email, password FROM customers WHERE customer_id = :cid"),
            {"cid": request.customer_id}
        ).fetchone()
        
        if not result:
            return {"success": False, "message": "Customer ID not found"}
        
        if result.password != request.password:
            return {"success": False, "message": "Invalid password"}
        
        return {
            "success": True,
            "customer": {
                "customer_id": result.customer_id,
                "first_name": result.first_name,
                "last_name": result.last_name,
                "email": result.email
            }
        }
    except Exception as e:
        print(f"Login error: {e}", flush=True)
        return {"success": False, "message": "Service temporarily unavailable. Please try again."}

@app.get("/api/greeting/{customer_id}")
def get_greeting(customer_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import text
    result = db.execute(
        text("SELECT first_name, last_name FROM customers WHERE customer_id = :cid"),
        {"cid": customer_id}
    ).fetchone()
    
    if not result:
        return {"greeting": "Good day! How may I assist you with your travel shopping?"}
    
    full_name = f"{result.first_name} {result.last_name}"
    return {"greeting": f"Good day! {full_name}, How may I assist you with your travel shopping?"}

@app.get("/api/customer360/{customer_id}")
def get_customer360(customer_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import text
    result = db.execute(
        text("SELECT first_name, last_name FROM customers WHERE customer_id = :cid"),
        {"cid": customer_id}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    full_name = f"{result.first_name} {result.last_name}"
    
    customer360_data = {
        "profile": {
            "name": full_name,
            "age": 36,
            "location": "San Diego, CA",
            "tier": "NM Insider - Silver"
        },
        "sizes_fit": {
            "tops": "Medium",
            "bottoms": "32×32",
            "shoes": "US 11",
            "height": "6'0\"",
            "build": "Lean / long-torso",
            "skin": "Fair - cool undertone"
        },
        "style_preferences": {
            "preferred_colors": ["Navy", "Charcoal", "Muted Olive", "Ice Blue"],
            "style": "Minimal, Smart-casual, Functional techwear",
            "budget": "$100 - $500"
        },
        "favorite_brands": ["Theory", "Rag & Bone", "Patagonia", "Vince", "Cole Haan"]
    }
    
    return customer360_data

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    orchestrator = ShoppingOrchestrator(db)
    
    conversation = None
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id
        ).first()
    
    if not conversation:
        conversation = db.query(Conversation).filter(
            Conversation.customer_id == request.user_id
        ).order_by(Conversation.id.desc()).first()
    
    conversation_history = []
    existing_intent = {}
    if conversation:
        if conversation.messages:
            conversation_history = conversation.messages
        if conversation.context and isinstance(conversation.context, dict):
            existing_intent = conversation.context.get("accumulated_intent", {})
    
    try:
        result = orchestrator.process_message(
            user_id=request.user_id,
            message=request.message,
            conversation_history=conversation_history,
            existing_intent=existing_intent
        )
    except Exception as e:
        print(f"Error in orchestrator: {e}")
        result = {
            "response": "I apologize, but I encountered an issue processing your request. Please try again.",
            "products": [],
            "clarification_needed": False,
            "clarification_question": None,
            "context": {}
        }
    
    updated_context = result.get("context", {})
    updated_context["accumulated_intent"] = result.get("updated_intent", {})
    
    if conversation:
        messages = list(conversation.messages or [])
        messages.append({"role": "user", "content": request.message})
        messages.append({"role": "assistant", "content": result["response"]})
        conversation.messages = messages
        conversation.context = updated_context
        flag_modified(conversation, "messages")
        flag_modified(conversation, "context")
        db.commit()
    else:
        new_conversation = Conversation(
            customer_id=request.user_id,
            messages=[
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": result["response"]}
            ],
            context=updated_context
        )
        db.add(new_conversation)
        db.commit()
    
    products = [ProductResponse(
        id=p.get("id", 0),
        name=p.get("name", ""),
        description=p.get("description", ""),
        category=p.get("category"),
        subcategory=p.get("subcategory"),
        price=p.get("price"),
        brand=p.get("brand"),
        gender=p.get("gender"),
        image_url=p.get("image_url"),
        in_stock=p.get("in_stock", True),
        rating=p.get("rating", 0)
    ) for p in result.get("products", [])]
    
    agent_thinking = result.get("agent_thinking", [])
    
    return ChatResponse(
        response=result["response"],
        products=products,
        clarification_needed=result.get("clarification_needed", False),
        clarification_question=result.get("clarification_question"),
        context=result.get("context", {}),
        updated_intent=result.get("updated_intent", {}),
        agent_thinking=agent_thinking
    )

@app.post("/api/customers", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    address = db.query(CustomerAddress).filter(CustomerAddress.customer_id == customer_id).first()
    
    return {
        "customer_id": customer.customer_id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email,
        "phone_number": customer.phone_number,
        "gender": customer.gender,
        "date_of_birth": str(customer.date_of_birth) if customer.date_of_birth else None,
        "address": {
            "label": address.label if address else None,
            "address_line1": address.address_line1 if address else None,
            "address_line2": address.address_line2 if address else None,
            "city": address.city if address else None,
            "state": address.state if address else None,
            "postal_code": address.postal_code if address else None,
            "country": address.country if address else None,
        } if address else None
    }

class CustomerUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str | None = None
    gender: str | None = None
    date_of_birth: str | None = None
    address: dict | None = None

@app.put("/api/customers/{customer_id}")
def update_customer(customer_id: str, request: CustomerUpdateRequest, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.first_name = request.first_name
    customer.last_name = request.last_name
    customer.email = request.email
    customer.phone_number = request.phone_number
    customer.gender = request.gender
    
    from datetime import datetime
    if request.date_of_birth:
        try:
            customer.date_of_birth = datetime.strptime(request.date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            customer.date_of_birth = None
    else:
        customer.date_of_birth = None
    
    if request.address:
        address = db.query(CustomerAddress).filter(CustomerAddress.customer_id == customer_id).first()
        has_address_data = any([
            request.address.get("address_line1"),
            request.address.get("city"),
            request.address.get("state"),
            request.address.get("postal_code"),
            request.address.get("country")
        ])
        
        if address:
            address.label = request.address.get("label") or address.label
            address.address_line1 = request.address.get("address_line1") or address.address_line1
            address.address_line2 = request.address.get("address_line2")
            address.city = request.address.get("city") or address.city
            address.state = request.address.get("state")
            address.postal_code = request.address.get("postal_code")
            address.country = request.address.get("country")
        elif has_address_data:
            import uuid
            new_address = CustomerAddress(
                address_id=f"addr-{str(uuid.uuid4())[:8]}",
                customer_id=customer_id,
                label=request.address.get("label"),
                address_line1=request.address.get("address_line1") or "",
                address_line2=request.address.get("address_line2"),
                city=request.address.get("city") or "",
                state=request.address.get("state"),
                postal_code=request.address.get("postal_code"),
                country=request.address.get("country")
            )
            db.add(new_address)
    
    db.commit()
    db.refresh(customer)
    
    return {
        "success": True,
        "message": "Customer updated successfully",
        "customer": {
            "customer_id": customer.customer_id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email
        }
    }

@app.get("/api/products", response_model=list[ProductResponse])
def get_products(
    category: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    products = query.limit(limit).all()
    return products

@app.get("/api/products/{product_id}")
def get_product_details(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    colors = product.colors if product.colors else ["Default"]
    if not colors or len(colors) == 0:
        colors = ["Default"]
    
    color_images = {}
    for idx, color in enumerate(colors):
        color_key = color.lower().replace(" ", "-").replace("/", "-")
        images = [
            f"https://picsum.photos/seed/{product_id}-{color_key}-1/600/800",
            f"https://picsum.photos/seed/{product_id}-{color_key}-2/600/800",
            f"https://picsum.photos/seed/{product_id}-{color_key}-3/600/800",
            f"https://picsum.photos/seed/{product_id}-{color_key}-4/600/800",
        ]
        color_images[color] = images
    
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "subcategory": product.subcategory,
        "price": product.price,
        "brand": product.brand,
        "gender": product.gender,
        "sizes_available": product.sizes_available or [],
        "colors": colors,
        "color_images": color_images,
        "tags": product.tags or [],
        "image_url": product.image_url,
        "in_stock": product.in_stock,
        "rating": product.rating,
        "material": product.material,
        "season": product.season,
        "care_instructions": product.care_instructions
    }

@app.post("/api/reset")
def reset_conversation(user_id: int, db: Session = Depends(get_db)):
    db.query(Conversation).filter(Conversation.customer_id == user_id).delete()
    db.commit()
    return {"status": "conversation reset"}

@app.get("/api/conversation/{user_id}")
def get_conversation(user_id: int, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(
        Conversation.customer_id == user_id
    ).order_by(Conversation.id.desc()).first()
    
    if not conversation or not conversation.messages:
        return {"messages": [], "context": {}}
    
    return {
        "messages": conversation.messages,
        "context": conversation.context or {}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
