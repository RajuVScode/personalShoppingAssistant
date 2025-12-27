from backend.models.schemas import (
    NormalizedIntent, 
    CustomerContext, 
    EnvironmentalContext,
    EnrichedContext
)
from backend.services.external_apis import ExternalContextService

class ContextAggregator:
    def __init__(self):
        self.external_service = ExternalContextService()
    
    def aggregate(
        self, 
        intent: NormalizedIntent, 
        customer: CustomerContext
    ) -> EnrichedContext:
        destination = getattr(intent, 'location', None) or customer.location
        
        env_data = self.external_service.get_environmental_context(
            destination
        )
        
        environmental = EnvironmentalContext(
            weather=env_data.get("weather"),
            local_events=env_data.get("local_events", []),
            trends=env_data.get("trends", [])
        )
        
        return EnrichedContext(
            intent=intent,
            customer=customer,
            environmental=environmental
        )
