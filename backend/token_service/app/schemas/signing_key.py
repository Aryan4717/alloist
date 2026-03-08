from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SigningKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    algorithm: str
    created_at: datetime
    is_active: bool
