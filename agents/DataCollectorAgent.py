from loguru import logger
from datetime import datetime
from openai import OpenAI
from pydantic import ValidationError 
from structures.Context_exchange import ProcessContext
from structures.ContractData import ContractData, SetupRentalContract
from structures.ContractStatus import ContractStatus 
from agents.BaseAgent import BaseAgent
from structures.DataCollectorStructures import ContractAnalysis, ContractInputStatus, MissingInfo 
from knowledge_maps.ContractSetupKnowledgeMaps import contract_setup_knowledge_map 
import json

class DataCollectorAgent(BaseAgent):
    def __init__(self, process_context: ProcessContext, client: OpenAI):
        # Call parent's __init__ to properly initialize the context
        super().__init__(process_context, client)
        # Initialize agent-specific attributes
        self.current_contract = SetupRentalContract() 
        self.contract_setup_knowledge_map = contract_setup_knowledge_map

    def __make_api_call(self, user_input: str, verbose: bool = True) -> ContractAnalysis:
        system_prompt = f"""
        Jesteś asystentem wspierającym process zbierania danych dla umowy najmu nieruchomości.
        Twoim celem jest iteracyjne zbieranie informacji od użytkownika, aż wszystkie wymagane pola w strukturze SetupRentalContract zostaną wypełnione.
        Analizuj odpowiedź użytkownika i aktualizuj pola w `current_contract`.
        Jeśli brakuje informacji, zadaj precyzyjne pytanie, aby je uzyskać.
        Jeśli wszystkie informacje są zebrane, ustaw status na COMPLETE.

        Dodatkowe informacje i kontekst:
        {self.contract_setup_knowledge_map}
        """
        
        current_contract_info = f"\nAktualny stan zbieranych danych do umowy (format JSON):\n{self.current_contract}"

        logger.debug(f"Sending to LLM - User input: {user_input}")
        logger.debug(f"Sending to LLM - Current contract state: {current_contract_info}")

        response = self.client.chat.completions.create(
                extra_body={
                    "provider": {
                        "sort": "throughput"
                    } 
                },
                model="qwen/qwen3-235b-a22b", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{user_input}{current_contract_info}"}
                ],
                response_model=ContractAnalysis,
                temperature=0,
                max_retries=2,
            )
        
        if verbose:
            for t in response.thoughts:
                logger.thought(f"Thought: {t.thought}")
                logger.action(f"Action: {t.action}: {t.action_input}")
            logger.info(f"LLM Response: current_contract={response.current_contract}")
            logger.info(f"status={response.status}")
        
        return response
    
    def _generate_summary(self):
        """Generate a readable summary of the current contract data"""
        contract_dict = self.current_contract.model_dump(exclude_none=True)
        return json.dumps(contract_dict, indent=2, ensure_ascii=False)

    def run(self) -> bool:
        logger.info(f"[DataCollectorAgent] Starting data collection.")

        # Ask user if they want to provide a prompt via CLI
        use_default_prompt = input("Czy chcesz użyć domyślnego promptu? (Tak/Nie): ").strip().lower()
        
        if use_default_prompt == "tak":
            user_prompt = """
Wynajmujacy: Adam Nowak ul. Piękna 12 Warszawa 22-222 PESEL 97020819820
Najemca: Krzysztof Kowalski, ul. Ładna 10 Kraków, 33-333 PESEL 99022319820

Nieruchomość: ul. Rajska 10, Warszawa, 22-333, bardzo dobry stan, powierzchnia 52,5 m2 5 pomieszczeń - 2 pokoje, kuchnia, łazienka, przedpokój. 
Wyposażenie: pralka, lodówka, zmywarka, 2 x łóżka, 4 x krzesła, stół
Umowa na 12 miesięcy
Start umowy 12.06.2024 - koniec umowy 12.06.2025

Czynsz 4500 zł. co 10 tego przelewem na konto bankowe 1112223334445556667
Kaucja 4500 zł.
"""
            logger.info("Używanie domyślnego promptu")
        else:
            logger.info("Wpisz swój prompt z danymi do umowy:")
            user_prompt = input("Wprowadź dane do analizy: ").strip()
            if not user_prompt:
                logger.error("Wprowadzono pusty prompt. Kończenie działania.")
                return False
        
        logger.info(f"Analizowanie promptu użytkownika: {user_prompt[:50]}...")
        analysis = self.__make_api_call(user_prompt, verbose=True)
        self.current_contract = analysis.current_contract

        # Add LLM history to context with proper update time
        self.context.metadata.llm_history.append({"role": "user", "content": user_prompt})
        self.context.metadata.llm_history.append({"role": "assistant", "content": str(analysis.current_contract)})
        self.context.metadata.last_update_time = datetime.now()
        
        # Main interaction loop
        while True:
            logger.debug(f"Current analysis status: {analysis.status}")
            
            if analysis.status == ContractInputStatus.INCOMPLETE:
                if analysis.missing_info and len(analysis.missing_info) > 0:
                    # Display question to user
                    question = analysis.missing_info[0].question
                    print(f"\n{question}")
                    logger.info(f"Asking for missing information: {question}")
                    
                    # Get user input for missing information
                    user_input = input("Twoja odpowiedź: ").strip()
                    if not user_input:
                        logger.warning("Wprowadzono pustą odpowiedź. Ponowne pytanie.")
                        continue
                    
                    # Send the response to LLM for analysis
                    analysis = self.__make_api_call(user_input, verbose=True)
                    self.current_contract = analysis.current_contract
                    
                    # Update context history
                    self.context.metadata.llm_history.append({"role": "user", "content": user_input})
                    self.context.metadata.llm_history.append({"role": "assistant", "content": str(analysis.current_contract)})
                    self.context.metadata.last_update_time = datetime.now()
                else:
                    logger.warning("Status INCOMPLETE, ale nie określono brakujących informacji")
                    print("\nBrakuje pewnych informacji. Proszę podać więcej szczegółów:")
                    user_input = input("Twoja odpowiedź: ").strip()
                    analysis = self.__make_api_call(user_input, verbose=True)
                    self.current_contract = analysis.current_contract
            
            elif analysis.status == ContractInputStatus.COMPLETE:
                # Show summary of collected data and ask for confirmation
                print(f"\nZebrane dane umowy:\n{self._generate_summary()}\n")
                print("Czy potwierdzasz poprawność powyższych danych?")
                
                confirmation = input("Wprowadź 'Tak' lub 'Nie': ").strip().lower()
                if confirmation == "tak":
                    logger.info("Dane potwierdzone przez użytkownika")
                    
                    # Change status to CONFIRMED (only within DataCollectorAgent's scope)
                    analysis.status = ContractInputStatus.CONFIRMED
                    
                    # Validate the contract data
                    try:
                        contract_dict = self.current_contract.model_dump(exclude_none=True)
                        final_contract_data = ContractData(**contract_dict)
                        
                        # Store the validated contract data in the context
                        self.context.contract_data = final_contract_data
                        # Note: We don't modify ContractStatus here - that's ContractCoordinator's responsibility
                        logger.info(f"Updated ProcessContext with validated contract data: {final_contract_data}")
                        
                        logger.success("[DataCollectorAgent] Zbieranie danych zakończone pomyślnie i zwalidowane.")
                        return True
                    except ValidationError as e:
                        logger.error(f"Błąd walidacji danych: {e}")
                        print("\nWystąpił błąd walidacji danych. Proszę poprawić dane.")
                        continue
                else:
                    print("\nProszę podać poprawione dane:")
                    user_input = input("Twoja odpowiedź: ").strip()
                    analysis = self.__make_api_call(user_input, verbose=True)
                    self.current_contract = analysis.current_contract
            else:
                logger.error(f"Nieznany status analizy: {analysis.status}")
                # We don't set ContractStatus.ERROR here - that's ContractCoordinator's responsibility
                return False
                
        