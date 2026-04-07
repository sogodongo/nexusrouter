from pydantic import BaseModel
from typing import Optional


class ManualEventRequest(BaseModel):
    subject:  str
    sender:   str
    body:     str
    source:   str = "manual"

    model_config = {
        "json_schema_extra": {
            "example": {
                "subject": "Payment failed for order ORD-4401",
                "sender":  "john@acmecorp.com",
                "body":    "My payment failed and my service is down.",
                "source":  "manual",
            }
        }
    }


class OutcomeResponse(BaseModel):
    event_id:   str
    status:     str
    intent:     Optional[str] = None
    urgency:    Optional[str] = None
    agent:      Optional[str] = None
    elapsed_s:  Optional[float] = None
    resolution: Optional[str] = None
    reason:     Optional[str] = None
