from pydantic import BaseModel
from typing import Optional

class AlertForwardRequest(BaseModel):
    recipient_contact: str
    message: Optional[str] = "Emergency alert forwarded from Smart Tourist Safety App"