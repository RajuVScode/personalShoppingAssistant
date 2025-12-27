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
    
    async def aggregate(
        self, 
        intent: NormalizedIntent, 
        customer: CustomerContext
    ) -> EnrichedContext:
        env_data = await self.external_service.get_environmental_context(
            customer.location
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
