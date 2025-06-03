from pydantic import BaseModel, Field, StringConstraints
from typing import Dict, Optional, List, Annotated
from datetime import date, datetime

class ClauseTemplate(BaseModel):
    """
    Reprezentuje szablon danych wymaganych do generowania klauzuli.
    """
    required_fields: Dict[str, str] = Field(..., description="Wymagane pola oraz jego opis: [nazwa: opis z przykładem]")
    optional_fields: Optional[Dict[str, str]] = Field(None, description="Opcjonalne pola i ich opis")

class Clause(BaseModel):
    """
    Reprezentacja pojedynczej klauzuli w umowie
    """
    id: str = Field(..., description="Unikalny identyfikator klauzuli np. 1.1")
    text: str = Field(
        ...,
        description="""
        Treść klauzuli sformułowana zgodnie z zasadami języka prawnego. Musi spełniać następujące kryteria:
        
        1. Konkretność:
        - jednoznaczne określenie praw, obowiązków lub warunków
        - brak niejasności i wieloznaczności w zapisach
        
        2. Formalność:
        - stosowanie stylu urzędowego
        - wykluczenie języka potocznego i kolokwializmów
        
        3. Spójność:
        - logiczne powiązanie z pozostałymi klauzulami
        - brak sprzeczności z innymi postanowieniami
        
        4. Jednoznaczność:
        - zrozumiałość w kontekście prawnym
        - precyzyjne określenie warunków i zakresu stosowania
        
        5. Formatowanie:
        - dopuszczalny podział na zdania lub punkty
        - wyodrębnienie istotnych elementów (wyjątków, warunków, terminów)
        - stosowanie odpowiednich konstrukcji składniowych (np. 'z zastrzeżeniem, że')
        
        Przykład poprawnego zapisu:
        'Strona zobowiązuje się do dokonania płatności w terminie 14 dni od dnia otrzymania faktury, 
        z zastrzeżeniem, że w przypadku opóźnienia płatności naliczane będą odsetki ustawowe 
        w wysokości określonej w obowiązujących przepisach prawa.'
        """
    )
    chain_of_thought: List[str] = Field(
        ..., 
        description="""
        Kroki myślowe prowadzące do stworzenia klauzuli. Każdy krok powinien odpowiadać pytaniu lub decyzji, np.:
        1. Jakie prawo, obowiązek lub warunek musi zostać określony?
        2. Jakie potencjalne wyjątki lub ograniczenia mogą mieć zastosowanie?
        3. Czy istnieją powiązania z innymi klauzulami w dokumencie?
        4. Czy sformułowanie jest zgodne z przepisami prawa?
        5. Czy język klauzuli jest dostosowany do formalnych wymogów?
        """
    )
    template: Optional[ClauseTemplate] = Field(
        None,
        description="Definicja danych wymaganych i opcjonalnych"
    )
    note: Optional[str] = Field(None, description="Dodatkowy komentarz lub uwaga do klauzuli.")

class PartyDetails(BaseModel):
    """
    Reprezentuje dane strony umowy.
    """
    first_name: str = Field(..., description="Imię")
    last_name: str = Field(..., description="Nazwisko")
    address: str = Field(..., description="Adres zamieszkania")
    pesel: Annotated[str, StringConstraints(pattern=r'^\d{11}$')] = Field(
        ..., 
        description="Numer PESEL - 11 cyfr"
    )

class Preamble(BaseModel):
    """
    Reprezentuje preambułę umowy, zawierającą dane stron i inne informacje wprowadzające.
    """
    contract_date: date = Field(
        ..., 
        description="Data zawarcia umowy"
    )
    contract_location: str = Field(
        ..., 
        description="Miejsce zawarcia umowy"
    )
    party_one: PartyDetails = Field(
        ..., 
        description="Pierwsza strona umowy (zazwyczaj Wynajmujący)"
    )
    party_two: PartyDetails = Field(
        ..., 
        description="Druga strona umowy (zazwyczaj Najemca)"
    )

class Paragraph(BaseModel):
    """
    Reprezentacja pojedynczego paragrafu w umowie najmu mieszkania.
    """
    id: int = Field(..., description="Unikalny identyfikator paragrafu, np. 1")
    title: str = Field(..., description="Tytuł paragrafu, np. 'Przedmiot umowy'")
    #chain_of_thought: List[str] = Field(None, description="Kolejne kroki logiczne prowadzące do paragrafu.")
    purpose: str = Field(
        ..., 
        description="Cel paragrafu - krótki opis określający funkcję tego paragrafu w umowie"
    )
    clauses: List[Clause] = Field(
        ..., 
        description="Lista klauzul wchodzących w skład paragrafu"
    )
    note: Optional[str] = Field(
        None, 
        description="Opcjonalne notatki prawne lub wyjaśnienia dotyczące paragrafu"
    )

class PartContract(BaseModel):
    """
    Reprezentacja części umowy składającej się z paragrafów.
    """
    description: Optional[str] = Field(
        None, 
        description="Opcjonalny opis wyjaśniający znaczenie tej części umowy"
    )
    paragraphs: List[Paragraph] = Field(
        ..., 
        description="Lista paragrafów wchodzących w skład tej części umowy"
    )

class Contract(BaseModel):
    """
    Reprezentacja pełnej umowy prawnej wynajmu mieszkania.
    """
    title: str = Field(
        ..., 
        description="Tytuł umowy, np. 'UMOWA NAJMU LOKALU MIESZKALNEGO'"
    )
    preamble: Preamble = Field(
        ..., 
        description="Preambuła umowy zawierająca informacje o stronach i dacie zawarcia"
    )
    paragraphs: List[Paragraph] = Field(
        ...,
        description="Lista paragrafów w umowie."
    )
    version: Optional[str] = Field(
        None, 
        description="Opcjonalna wersja umowy."
    )
    created_at: datetime = Field(
        default_factory=datetime.now, 
        description="Data utworzenia dokumentu umowy"
    )