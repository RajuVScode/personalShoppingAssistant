from backend.models.schemas import (
    NormalizedIntent, 
    CustomerContext, 
    EnvironmentalContext,
    EnrichedContext,
    SegmentContext
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
        trip_segments = getattr(intent, 'trip_segments', None) or []
        
        if trip_segments and len(trip_segments) > 0:
            segments_context = []
            all_events = []
            first_weather = None
            
            for segment in trip_segments:
                if isinstance(segment, dict):
                    dest = segment.get("destination")
                    start = segment.get("start_date")
                    end = segment.get("end_date")
                else:
                    dest = segment.destination
                    start = segment.start_date
                    end = segment.end_date
                
                env_data = self.external_service.get_environmental_context(dest, start, end)
                
                segment_ctx = SegmentContext(
                    destination=dest,
                    start_date=start,
                    end_date=end,
                    weather=env_data.get("weather"),
                    local_events=env_data.get("local_events", [])
                )
                segments_context.append(segment_ctx)
                
                if first_weather is None:
                    first_weather = env_data.get("weather")
                all_events.extend(env_data.get("local_events", []))
            
            trends = self.external_service.trends_service.get_fashion_trends()
            
            environmental = EnvironmentalContext(
                weather=first_weather,
                local_events=all_events[:10],
                trends=trends,
                segments=segments_context
            )
        else:
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
