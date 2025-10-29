from pydantic import BaseModel
from typing import Optional

class ModelRequest(BaseModel):
    session_id: str
    # model_name: Optional[str] = None
    prompt: str