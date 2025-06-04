from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from structures.ContractStatus import ContractStatus
from structures.ContractGenerationStructure import Contract
from structures.AuditRiskStructures import AuditResult
from structures.ContractData import ContractData

#Struktura dla metadanych w procesie agenta np. status (który agent wykonuje pracę), llm_history czyli wszystkie prompty oraz odpowiedzi od agentów
#current_version dla audytora - jeśli audytor coś poprawi ma się zwiększyć wersja wraz z maksymalną ilością prób
class ProcessMetadata(BaseModel):
    """Model metadanych procesu"""
    status: ContractStatus = Field(default=ContractStatus.COLLECTING_DATA)
    llm_history: List[Dict[str, str]] = Field(default=[])
    current_version: int = Field(default=1)
    max_revision_attempts: int = Field(default=3)
    current_revision_attempt: int = Field(default=0)
    audit_history: List[AuditResult] = Field(default_factory=list)
    process_start_time: datetime = Field(default_factory=datetime.now)
    last_update_time: datetime = Field(default_factory=datetime.now)
    

class ProcessContext(BaseModel):
    """Kontekst całego procesu łączący dane umowy i metadane"""
    current_contract: Optional[Contract] = Field(None)
    contract_data: Optional[ContractData] = Field(None)
    metadata: ProcessMetadata = Field(ProcessMetadata())