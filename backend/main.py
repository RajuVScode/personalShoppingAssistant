import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from backend.database.connection import engine, get_db, Base
from backend.database.models import Customer, Product, PurchaseHistory, Conversation
from backend.models.schemas import (
    ChatRequest, ChatResponse, CustomerCreate, CustomerResponse,
    ProductCreate, ProductResponse
)
from backend.agents.orchestrator import ShoppingOrchestrator
from backend.rag.vector_store import ProductVectorStore
from backend.database.seed import seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    try:
        existing_products = db.query(Product).first()
        if not existing_products:
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
                vector_store = ProductVectorStore()
                vector_store.create_index(product_data)
    finally:
        db.close()
    
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

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "AI Shopping Experience"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    orchestrator = ShoppingOrchestrator(db)
    
    conversation = None
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id
        ).first()
    
    conversation_history = []
    if conversation and conversation.messages:
        conversation_history = conversation.messages
    
    result = await orchestrator.process_message(
        user_id=request.user_id,
        message=request.message,
        conversation_history=conversation_history
    )
    
    if conversation:
        messages = conversation.messages or []
        messages.append({"role": "user", "content": request.message})
        messages.append({"role": "assistant", "content": result["response"]})
        conversation.messages = messages
        db.commit()
    else:
        new_conversation = Conversation(
            customer_id=request.user_id,
            messages=[
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": result["response"]}
            ],
            context=result.get("context", {})
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
    
    return ChatResponse(
        response=result["response"],
        products=products,
        clarification_needed=result.get("clarification_needed", False),
        clarification_question=result.get("clarification_question"),
        context=result.get("context", {})
    )

@app.post("/api/customers", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.get("/api/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.get("/api/products", response_model=list[ProductResponse])
async def get_products(
    category: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    products = query.limit(limit).all()
    return products

@app.post("/api/reset")
async def reset_conversation(user_id: int, db: Session = Depends(get_db)):
    db.query(Conversation).filter(Conversation.customer_id == user_id).delete()
    db.commit()
    return {"status": "conversation reset"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
