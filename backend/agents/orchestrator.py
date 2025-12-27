from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from backend.agents.clarifier import ClarifierAgent
from backend.agents.intent_processor import IntentProcessor
from backend.agents.customer360 import Customer360Agent
from backend.agents.context_aggregator import ContextAggregator
from backend.agents.product_recommender import ProductRecommenderAgent
from backend.models.schemas import (
    ChatMessage, NormalizedIntent, CustomerContext, 
    EnvironmentalContext, EnrichedContext
)

class GraphState(TypedDict):
    messages: list
    user_id: int
    raw_query: str
    is_ambiguous: bool
    clarification_question: str
    assistant_message: str
    clarifier_intent: dict
    normalized_intent: dict
    customer_context: dict
    environmental_context: dict
    enriched_context: dict
    products: list
    final_response: str
    conversation_history: list

class ShoppingOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.clarifier = ClarifierAgent()
        self.intent_processor = IntentProcessor()
        self.customer360 = Customer360Agent(db)
        self.context_aggregator = ContextAggregator()
        self.recommender = ProductRecommenderAgent()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(GraphState)
        
        workflow.add_node("clarify", self._clarify_node)
        workflow.add_node("process_intent", self._intent_node)
        workflow.add_node("get_customer_context", self._customer_context_node)
        workflow.add_node("aggregate_context", self._aggregate_context_node)
        workflow.add_node("recommend", self._recommend_node)
        
        workflow.set_entry_point("clarify")
        
        workflow.add_conditional_edges(
            "clarify",
            self._should_clarify,
            {
                "clarify": END,
                "proceed": "process_intent"
            }
        )
        
        workflow.add_edge("process_intent", "get_customer_context")
        workflow.add_edge("get_customer_context", "aggregate_context")
        workflow.add_edge("aggregate_context", "recommend")
        workflow.add_edge("recommend", END)
        
        return workflow.compile()
    
    def _clarify_node(self, state: GraphState) -> GraphState:
        existing_intent = state.get("clarifier_intent", {})
        
        result = self.clarifier.analyze(
            state["raw_query"],
            state.get("conversation_history", []),
            existing_intent=existing_intent
        )
        
        state["is_ambiguous"] = result.get("needs_clarification", False)
        state["clarification_question"] = result.get("clarification_question", "")
        state["assistant_message"] = result.get("assistant_message", "")
        state["clarifier_intent"] = result.get("updated_intent", {})
        
        if state["is_ambiguous"]:
            state["final_response"] = result.get("assistant_message", "") or state["clarification_question"]
        
        return state
    
    def _should_clarify(self, state: GraphState) -> Literal["clarify", "proceed"]:
        if state.get("is_ambiguous", False):
            return "clarify"
        return "proceed"
    
    def _intent_node(self, state: GraphState) -> GraphState:
        intent = self.intent_processor.process(state["raw_query"])
        intent_dict = intent.model_dump()
        
        clarifier_intent = state.get("clarifier_intent", {})
        if clarifier_intent:
            if clarifier_intent.get("destination") and not intent_dict.get("location"):
                intent_dict["location"] = clarifier_intent["destination"]
            if clarifier_intent.get("travel_date"):
                intent_dict["occasion"] = f"travel on {clarifier_intent['travel_date']}"
            if clarifier_intent.get("activities"):
                activities = clarifier_intent["activities"]
                if isinstance(activities, str):
                    activities = [a.strip() for a in activities.split(",")]
                existing_keywords = intent_dict.get("keywords") or []
                intent_dict["keywords"] = existing_keywords + activities
            if clarifier_intent.get("budget_amount"):
                intent_dict["budget_max"] = clarifier_intent["budget_amount"]
            if clarifier_intent.get("clothes"):
                intent_dict["style"] = clarifier_intent["clothes"]
            if clarifier_intent.get("preferred_brand"):
                intent_dict["brand"] = clarifier_intent["preferred_brand"]
            if clarifier_intent.get("trip_segments"):
                intent_dict["trip_segments"] = clarifier_intent["trip_segments"]
        
        state["normalized_intent"] = intent_dict
        return state
    
    def _customer_context_node(self, state: GraphState) -> GraphState:
        context = self.customer360.get_customer_context(state["user_id"])
        state["customer_context"] = context.model_dump()
        return state
    
    def _aggregate_context_node(self, state: GraphState) -> GraphState:
        intent = NormalizedIntent(**state["normalized_intent"])
        customer = CustomerContext(**state["customer_context"])
        
        enriched = self.context_aggregator.aggregate(intent, customer)
        state["enriched_context"] = enriched.model_dump()
        state["environmental_context"] = enriched.environmental.model_dump()
        
        return state
    
    def _recommend_node(self, state: GraphState) -> GraphState:
        enriched = EnrichedContext(**state["enriched_context"])
        
        products, explanation = self.recommender.get_recommendations(enriched)
        
        state["products"] = products
        state["final_response"] = explanation
        
        return state
    
    def process_message(self, user_id: int, message: str, conversation_history: list = None, existing_intent: dict = None) -> dict:
        initial_state: GraphState = {
            "messages": [],
            "user_id": user_id,
            "raw_query": message,
            "is_ambiguous": False,
            "clarification_question": "",
            "assistant_message": "",
            "clarifier_intent": existing_intent or {},
            "normalized_intent": {},
            "customer_context": {},
            "environmental_context": {},
            "enriched_context": {},
            "products": [],
            "final_response": "",
            "conversation_history": conversation_history or []
        }
        
        final_state = self.graph.invoke(initial_state)
        
        return {
            "response": final_state["final_response"],
            "products": final_state["products"],
            "clarification_needed": final_state["is_ambiguous"],
            "clarification_question": final_state["clarification_question"],
            "updated_intent": final_state.get("clarifier_intent", {}),
            "context": {
                "intent": final_state.get("normalized_intent", {}),
                "environmental": final_state.get("environmental_context", {})
            }
        }
