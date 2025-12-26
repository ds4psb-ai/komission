from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import List, Optional
import uuid
from datetime import datetime

class CalibrationChoice(str, Enum):
    A = "A"
    B = "B"

class CalibrationPair(BaseModel):
    pair_id: str
    question: str
    option_a: dict
    option_b: dict
    
    # Mock data example
    # option_a = {"id": "opt_a", "label": "Energetic", "description": "Fast cuts, high tempo"}
    
    model_config = ConfigDict(from_attributes=True)

class CalibrationPairResponse(BaseModel):
    session_id: str
    pairs: List[CalibrationPair]

class CalibrationSubmitRequest(BaseModel):
    creator_id: uuid.UUID
    pair_id: str
    selected_option_id: str
    selection: CalibrationChoice

class CalibrationSubmitResponse(BaseModel):
    status: str
    saved_choice_id: uuid.UUID
