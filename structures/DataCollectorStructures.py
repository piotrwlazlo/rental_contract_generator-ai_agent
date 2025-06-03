from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from structures.ContractData import SetupRentalContract


class ContractInputStatus(Enum):
    INCOMPLETE = "incomplete information"
    COMPLETE = "complete information"
    CONFIRMED = "confirmed"

class ThoughtStep(BaseModel):
    thought: str = Field(..., description="Przemyślenia asystenta co do kroków podczas tworzenia umowy")
    action: str = Field( ... , description="Nazwa działania, które asystent podejmuje np. 'ask' lub 'calculate'.")
    action_input: str = Field(..., description="Dane wejściowe dla działania, np. treść pytania lub dane do obliczeń.")

class MissingInfo(BaseModel):
    field: str = Field(..., description="Nazwa brakującego pola w zamówieniu np. lessor name lub lessee name itp.")
    question: str = Field(..., description="Pytanie, które należy zadać użytkownikowi, aby uzupełnić brakujące informacje.")

class ContractAnalysis(BaseModel):
    thoughts: List[ThoughtStep] = Field(..., description="Lista kroków myślowych i działań wykonanych przez asystenta.")
    current_contract: SetupRentalContract = Field(..., description="Obecny stan umowy najmu.")
    status: ContractInputStatus = Field(..., description="Aktualny status umowy: INCOMPLETE, COMPLETE lub CONFIRMED.")
    missing_info: Optional[List[MissingInfo]] = Field(None, description="Lista brakujących informacji w umowie.")