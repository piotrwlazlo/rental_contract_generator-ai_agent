from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import Field


class Risk(BaseModel):
    chain_of_thought: List[str] = Field(
        ..., 
        description="Kroki wyjaśniające prowadzące do zidentyfikowanego ryzyka. Te kroki powinny dostarczać szczegółowego uzasadnienia wykrycia problemu."
    )
    paragraph: int = Field(
        ..., 
        description="Paragraf umowy, w którym jest zidentyfikowane ryzyko (od 1 do 14)",
    )
    content: str = Field(
        ..., 
        description="Opis zidentyfikowanego ryzyka. Powinien jasno i zwięźle podsumowywać problem."
    )

    suggested_changes: List[str] = Field(
        ..., 
        description="Propozycje zmian w celu zmniejszenia lub wyeliminowania zidentyfikowanego ryzyka. Każda propozycja powinna być jasna, konkretna i możliwa do wdrożenia."
    )

class AuditRisk(BaseModel):
    risks: List[Risk] = Field(..., description = "Lista wykrytych ryzyk. Każde ryzyko musi zawierać dokładne uzasadnienie")


class AuditResult(BaseModel):
    is_approved: bool = Field(False, description="Czy audyt przeszedł bez żadnych uwag?")
    risks: List[Risk] = Field(
        ..., 
        description="Lista wszystkich zidentyfikowanych ryzyk. Każde ryzyko zawiera szczegółowe uzasadnienie oraz podsumowanie opisu."
    )
    timestamp: datetime = Field(datetime.now, description="Kiedy był robiony audyt")

class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class Category(Enum):
    ESSENTIAL_ELEMENTS = "Elementy konieczne umowy"
    FORM = "Forma umowy"
    DURATION = "Czas trwania"
    OBLIGATIONS = "Obowiązki stron"
    PAYMENTS = "Płatności"
    TERMINATION = "Wypowiedzenie i zakończenie"
    MAINTENANCE = "Utrzymanie i naprawy"
    RIGHTS = "Prawa stron"
    OTHER = "Inne"

class LegalReference(BaseModel):
    article: str = Field(..., description="Numer artykułu np. 'Art 639'")
    paragraph: Optional[str] = Field(None, description="Numer paragrafu (jeśli istnieją)")
    description: str = Field(..., description="Opis treści artykułu")

class Check(BaseModel):
    question: str = Field(..., description="Pytanie kontrolne związane z audytem")
    legal_basis: List[LegalReference] = Field(..., Field="Podstawa prawna")
    possible_issues: List[str] = Field(..., description="")
    priority: Optional[Priority] = Field(None, description="Priorytet pytania (niższa wartość oznacza wyższy priorytet).")
    category: Optional[Category] = Field(None, description="Kategoria pytania, np. 'Płatności'.")
    note: Optional[str] = Field(None, description="Dodatkowy komentarz")
    validation_hint: Optional[str] = Field(None, description="Wskazówka jak zweryfikować zgodność")

class AuditChecklist(BaseModel):
    questions: List[Check] = Field(..., description="Lista pytań kontrolnych do przeprowadzenia audytu")
    checklist_name: str = Field(..., description="Nazwa checklisty.")
    version: Optional[str] = Field(1.0, description="Opcjonalna wersja checklisty (np. '10').")
    applicable_law_version: str = Field(...,description="Wersja przepisów prawnych")