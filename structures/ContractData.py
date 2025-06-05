from pydantic import BaseModel, Field, StringConstraints
from typing import List, Optional, Literal, Annotated
from structures.AuditRiskStructures import AuditResult

#Struktura do przechowywania danych do kontraktu oraz zbiór ryzyk dla audytora
class Address(BaseModel):
    street: str = Field(..., description="Nazwa ulicy wraz z numerem")
    city: str = Field(..., description="Nazwa miejscowości")
    postal_code: str = Field(..., description="Kod pocztowy")

class Party(BaseModel):
    name: str = Field(..., description="Nazwa osoby fizycznej lub prawnej")
    address: Address = Field(..., description="Adres strony")
    pesel: Annotated[str, StringConstraints(pattern=r'^\d{11}$')] = Field(..., description="PESEL")
    phone: Optional[str] = Field(None, description="Numer telefonu")

class LeaseDuration(BaseModel):
    length: int = Field(12, description="Długość wynajmu, liczba jednostek czasu")
    step: Literal['month', 'year'] = Field("month", description="Jednostka czasu, np. 'miesiąc' lub 'rok'")
    is_indefinite: bool = Field(False, description="Czy czas trwania umowy jest nieoznaczony")
    start_date: Optional[str] = Field(None, description="Data rozpoczęcia umowy")
    end_date: Optional[str] = Field(None, description="Data zakończenia umowy")

class Property(BaseModel):
    address: Address = Field(..., description="Adres nieruchomości")
    condition: Optional[str] = Field(None, description="Ocena stanu nieruchomości przy przekazaniu")
    area: float = Field(..., description="Powierzchnia użytkowa nieruchomości w metrach kwadratowych (m2)")
    rooms_number: int = Field(..., description="Liczba pomieszczeń w nieruchomości")
    equipment: List[str] = Field(..., description="Lista wyposażenia i elementów stałych w nieruchomości")
    intended_use: Optional[Literal['residential', 'commercial', 'industrial', 'mixed-use', 'recreational']] = Field(
        "residential", description="Cel/sposób używania nieruchomości (np. mieszkalna, komercyjna, przemysłowa, wielofunkcyjna, rekreacyjna)"
    )

class Deposit(BaseModel):
    amount: int = Field(..., description="Wysokość kaucji w jednostkach waluty, np. 3000")
    currency: Literal["PLN", "EUR"] = Field("PLN", description="Waluta kaucji, np. PLN")
    type: Literal["jednorazowa", "wielokrotna"] = Field("jednorazowa", description="Rodzaj kaucji: 'jednorazowa' lub 'wielokrotna'")
    conditions: Optional[str] = Field(None, description="Dodatkowe warunki dotyczące kaucji, np. 'zwrot do 10 dni po zakończeniu umowy'")


class Rent(BaseModel):
    amount: int = Field(..., description="Wysokość czynszu w jednostkach waluty, np. 2500")
    currency: Literal["PLN", "EUR"] = Field("PLN", description="Waluta czynszu, np. PLN")
    payment_schedule: Literal['monthly', 'quarterly', 'annually'] = Field("monthly", description="Harmonogram płatności, np. 'monthly', 'quarterly', 'annually'")
    payment_day: int = Field(10, ge=1, le=31, description="Dzień miesiąca, w którym płatność jest dokonywana (1-31), np. 10")
    payment_method: Literal['bank_transfer', 'cash', 'credit_card'] = Field("bank_transfer", description="Sposób płatności, np. 'bank_transfer', 'cash', 'credit_card'")
    bank_account_number: Optional[str] = Field(..., description="NUmer konta bankowego jeśli metodą płatności jest bank_transfer")
    additional_fees: Optional[List[str]] = Field(None, description="Opłaty dodatkowe, np. 'opłata za wodę', 'opłata za prąd'")
    deposit: Deposit = Field(None, description="Warunki dotyczące kaucji")


class ContractData(BaseModel):
    """Model danych umowy"""
    lessor: Party = Field(..., description="Dane wynajmującego")
    lessee: Party = Field(..., description="Dane najemcy")
    property_details: Property = Field(..., description="Szczegóły nieruchomości")
    lease_duration: LeaseDuration = Field(..., description="Okres wynajmu")
    rent_details: Rent = Field(..., description="Szczegóły dotyczące czynszu")

class SetupRentalContract(BaseModel):
    lessor: Optional[Party] = Field(None, description="Dane wynajmującego")
    lessee: Optional[Party] = Field(None, description="Dane najemcy")
    property_details: Optional[Property] = Field(None, description="Szczegóły nieruchomości")
    lease_duration: Optional[LeaseDuration] = Field(None, description="Okres wynajmu")
    rent_details: Optional[Rent] = Field(None, description="Szczegóły dotyczące czynszu")
