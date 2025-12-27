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
        
        start_date = None
        end_date = None
        occasion = getattr(intent, 'occasion', None)
        if occasion and "travel on" in str(occasion):
            try:
                date_part = occasion.split("travel on ")[-1]
                if " to " in date_part:
                    dates = date_part.split(" to ")
                    start_date = dates[0].strip()
                    end_date = dates[1].strip()
                else:
                    start_date = date_part.strip()
                    end_date = start_date
            except:
                pass
        
        env_data = self.external_service.get_environmental_context(
            destination, start_date, end_date
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
