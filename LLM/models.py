from pydantic import BaseModel
from typing import Optional

class ModelRequest(BaseModel):
    session_id: str
    prompt: str
    project_id: Optional[int] = None
    model_name: Optional[str] = None