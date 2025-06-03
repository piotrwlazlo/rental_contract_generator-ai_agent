from loguru import logger
from openai import OpenAI
from structures.Context_exchange import ProcessContext
from structures.ContractStatus import ContractStatus
from agents.DataCollectorAgent import DataCollectorAgent
from agents.ContractGeneratorAgent import ContractGeneratorAgent
from agents.ContractAuditorAgent import ContractAuditorAgent
from agents.ContractReviserAgent import ContractReviserAgent


# GlobalAgent - globalny planer koordynujący pracę całego systemu agentowego
#inicjalizujemy w nim process context czyli metadane procesu oraz wywołujemy konkretnego agenta w zależności od tego w którym miejscu procesu jesteśmy
class ContractCoordinator:
    def __init__(self, client):
        self.process_context = ProcessContext()
        
        self.agents = {
            ContractStatus.COLLECTING_DATA: DataCollectorAgent(self.process_context, client),
            ContractStatus.GENERATING: ContractGeneratorAgent(self.process_context, client),
            ContractStatus.AUDITING: ContractAuditorAgent(self.process_context, client),
            ContractStatus.REVISING: ContractReviserAgent(self.process_context, client)
        }

    #Procesujemy kontrakt - jeśli status systemu nie będzie COMPLETED albo ERROR ma on się kręcić w kółko
    def process_contract(self, starting_status: ContractStatus = None) -> bool:
        """
        Rozpoczyna przetwarzanie kontraktu od określonego statusu.
        
        Args:
            starting_status: Opcjonalny początkowy status procesu. Jeśli None, używany jest domyślny status.
        
        Returns:
            bool: True jeśli proces zakończył się sukcesem, False w przeciwnym przypadku.
        """
        # Ustawienie początkowego statusu, jeśli został podany
        if starting_status is not None:
            logger.info(f"Ustawianie początkowego statusu procesu na: {starting_status.value}")
            self.process_context.metadata.status = starting_status
            
            # Jeśli zaczynamy od audytu, musimy mieć dane kontraktu
            if starting_status == ContractStatus.AUDITING:
                logger.info("Inicjalizacja przykładowych danych kontraktu dla audytu")
                self._initialize_sample_contract_data()
        
        while self.process_context.metadata.status not in [ContractStatus.COMPLETED, ContractStatus.ERROR]:
            current_agent = self.agents.get(self.process_context.metadata.status)
            
            if current_agent is None:
                self.process_context.metadata.status = ContractStatus.ERROR
                logger.error("Unknown agent!")
                return False

            #Uruchamiamy konkretnego agenta i jego wynik zapisujemy w success
            success = current_agent.run()

            #Póki nie ma wyniku od agenta ma się wykonywać ta logika
            #Tu jest logika agenta AUDITING - znowu sprawdzamy czy audytor nie wpadł w pętle - jeśli nie - przepinamy się na REVISORA
            #Wykonuje się też opcja update_status
            if not success:
                if self.process_context.metadata.status == ContractStatus.AUDITING:
                    if self.process_context.metadata.current_revision_attempt >= self.process_context.metadata.max_revision_attempts:
                        logger.error("Przekroczono maksymalną liczbę prób rewizji")
                        self.process_context.metadata.status = ContractStatus.ERROR
                        return False
                        
                    self.process_context.metadata.status = ContractStatus.REVISING
                else:
                    self.process_context.metadata.status = ContractStatus.ERROR
                    return False
            else:
                self._update_status()
            
        return self.process_context.metadata.status == ContractStatus.COMPLETED

    def _initialize_sample_contract_data(self):
        """
        Inicjalizuje przykładowe dane kontraktu dla trybu audytu.
        Te dane są używane, gdy pomijamy fazę zbierania danych.
        """
        from structures.ContractData import ContractData, Party, Address, Property, LeaseDuration, Rent, Deposit
        
        # Tworzymy przykładowe dane stron umowy
        lessor = Party(
            name="Adam Nowak", 
            address=Address(street="ul. Piękna 12", city="Warszawa", postal_code="22-222"), 
            pesel="97020819820"
        )
        
        lessee = Party(
            name="Krzysztof Kowalski", 
            address=Address(street="ul. Ładna 10", city="Kraków", postal_code="33-333"), 
            pesel="99022319820"
        )
        
        # Tworzymy szczegóły nieruchomości
        property_details = Property(
            address=Address(street="ul. Rajska 10", city="Warszawa", postal_code="22-333"),
            condition="bardzo dobry stan",
            area=52.5,
            rooms_number=5,
            equipment=["pralka", "lodówka", "zmywarka", "2 x łóżka", "4 x krzesła", "stół"],
            intended_use="residential"
        )
        
        # Tworzymy dane okresu najmu
        lease_duration = LeaseDuration(
            length=12,
            step="month",
            is_indefinite=False,
            start_date="2024-06-12",
            end_date="2025-06-12"
        )
        
        # Tworzymy dane czynszu i kaucji
        deposit = Deposit(
            amount=4500,
            currency="PLN",
            type="jednorazowa"
        )
        
        rent_details = Rent(
            amount=4500,
            currency="PLN",
            payment_schedule="monthly",
            payment_day=10,
            payment_method="bank_transfer",
            deposit=deposit
        )
        
        # Tworzymy kompletny obiekt ContractData
        contract_data = ContractData(
            lessor=lessor,
            lessee=lessee,
            property_details=property_details,
            lease_duration=lease_duration,
            rent_details=rent_details
        )
        
        # Ustawiamy dane w kontekście procesu
        self.process_context.contract_data = contract_data
        logger.info("Zainicjalizowano przykładowe dane kontraktu dla trybu audytu")

    #Tu mamy logikę przekazywania pałeczki w systemie - przepinamy się z jednego agenta na drugiego
    def _update_status(self):
        status_flow = {
            ContractStatus.COLLECTING_DATA: ContractStatus.GENERATING,
            ContractStatus.GENERATING: ContractStatus.AUDITING,
            ContractStatus.AUDITING: ContractStatus.COMPLETED,
            ContractStatus.REVISING: ContractStatus.AUDITING,
        }

       #Zapisujemy również informacje który agent teraz działą w zmiennej status
        self.process_context.metadata.status = status_flow.get(
            self.process_context.metadata.status, 
            ContractStatus.ERROR
        )