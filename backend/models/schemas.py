from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel
from datetime import datetime

class CustomerBase(BaseModel):
    name: str
    email: str
    location: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = {}
    style_profile: Optional[Dict[str, Any]] = {}
    size_info: Optional[Dict[str, Any]] = {}

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None
    gender: Optional[str] = None
    sizes_available: Optional[List[str]] = []
    colors: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    image_url: Optional[str] = None
    in_stock: Optional[bool] = True
    rating: Optional[float] = 0.0

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    user_id: int
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    products: Optional[List[ProductResponse]] = []
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}
    updated_intent: Optional[Dict[str, Any]] = {}

class TripSegment(BaseModel):
    destination: str
    start_date: str
    end_date: str
    activities: Optional[List[str]] = []
    notes: Optional[str] = None

class NormalizedIntent(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    occasion: Optional[str] = None
    style: Optional[str] = None
    gender: Optional[str] = None
    color_preferences: Optional[List[str]] = []
    size: Optional[str] = None
    keywords: Optional[List[str]] = []
    raw_query: str = ""
    location: Optional[str] = None
    trip_segments: Optional[List[TripSegment]] = []
    brand: Optional[str] = None

class CustomerContext(BaseModel):
    customer_id: Union[int, str]
    name: str
    preferences: Dict[str, Any] = {}
    style_profile: Dict[str, Any] = {}
    size_info: Dict[str, Any] = {}
    location: Optional[str] = None
    recent_purchases: List[Dict[str, Any]] = []

class SegmentContext(BaseModel):
    destination: str
    start_date: str
    end_date: str
    weather: Optional[Dict[str, Any]] = None
    local_events: Optional[List[Dict[str, Any]]] = []

class EnvironmentalContext(BaseModel):
    weather: Optional[Dict[str, Any]] = None
    local_events: Optional[List[Dict[str, Any]]] = []
    trends: Optional[List[str]] = []
    segments: Optional[List[SegmentContext]] = []

class EnrichedContext(BaseModel):
    intent: NormalizedIntent
    customer: CustomerContext
    environmental: EnvironmentalContext

class AgentState(BaseModel):
    messages: List[ChatMessage] = []
    user_id: int
    raw_intent: str = ""
    is_ambiguous: bool = False
    clarification_question: Optional[str] = None
    normalized_intent: Optional[NormalizedIntent] = None
    customer_context: Optional[CustomerContext] = None
    environmental_context: Optional[EnvironmentalContext] = None
    enriched_context: Optional[EnrichedContext] = None
    retrieved_products: List[ProductResponse] = []
    final_response: str = ""
