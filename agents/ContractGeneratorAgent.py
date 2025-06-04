from loguru import logger
from openai import OpenAI
from agents.BaseAgent import BaseAgent
from structures.Context_exchange import ProcessContext
from knowledge_maps.ContractTextTemplate import CONTRACT_TEMPLATE_V1
from knowledge_maps.ContractSetupKnowledgeMaps import CONTRACT_KNOWLEDGE_MAP
from structures.ContractGenerationStructure import Contract, PartContract, Preamble

class ContractGeneratorAgent(BaseAgent):
    def __init__(self, process_context: ProcessContext, client: OpenAI):
        super().__init__(process_context, client)
        self.contract_text_template = CONTRACT_TEMPLATE_V1
        self.contract_knowledge_map = CONTRACT_KNOWLEDGE_MAP
        self.__result = PartContract(paragraphs=[])
        #self.__contract = Contract()
        #self.__contract = self._init_contract()             
    
    def contract_parts(self, text, max_elementy, sep="## "):
        lst = text.split(sep)[1:]
        return [ sep + sep.join(lst[i:i + max_elementy]) for i in range(0, len(lst), max_elementy)]
    
    @property
    def result(self) -> PartContract:
        return self.__result

    def __process_contract(self):
        """
        Przetwarza wiedzę o kontraktach (CONTRACT_KNOWLEDGE_MAP) w mniejszych fragmentach,
        wykonując osobne wywołania API dla każdego fragmentu.
        """
        # Podziel CONTRACT_KNOWLEDGE_MAP na mniejsze fragmenty (chunks)
        chunks = self.contract_parts(self.contract_knowledge_map, 3)  # Podziel na fragmenty po 3 paragrafy
        logger.info(f"Podzielono wiedzę o kontraktach na {len(chunks)} fragmentów")
        
        # Inicjalizuj pustą listę paragrafów dla wyniku końcowego
        all_paragraphs = []
        
        # Iteruj przez każdy fragment i wykonaj osobne wywołanie API
        for i, chunk in enumerate(chunks):
            logger.info(f"Przetwarzanie fragmentu {i+1}/{len(chunks)}")
            
            # Przygotuj prompt systemowy dla danego fragmentu
            system_prompt = f"""
            Jesteś ekspertem prawa cywilnego w Polsce, specjalizującym się w umowach najmu. Twoje zadanie polega na szczegółowym opracowaniu wskazanych paragrafów umowy najmu, zgodnie z aktualnym stanem prawnym i najlepszymi praktykami.
            
            Podczas generowania treści:
            1. Każdy paragraf rozpocznij od numeru i tytułu
            2. Używaj precyzyjnego języka prawniczego
            3. Dbaj o kompletność regulacji
            4. Uwzględniaj ochronę interesów obu stron
            5. Zapewnij zgodność z Kodeksem Cywilnym i ustawą o ochronie praw lokatorów
            
            Struktura każdego paragrafu powinna zawierać:
            - Postanowienia ogólne
            - Szczegółowe prawa i obowiązki stron
            - Konsekwencje naruszenia postanowień
            - Warunki szczególne (jeśli dotyczy)
            
            Wygeneruj treść wskazanych paragrafów. Obecnie skupiamy się na paragrafach:
            {chunk}
            
            Zadbaj o spójność między paragrafami i zgodność z przepisami prawa.
            """
            
            try:
                # Wykonaj wywołanie API dla obecnego fragmentu
                chunk_result = self.client.chat.completions.create(
                extra_body={
                        "provider": {
                            "sort": "price"
                        } 
                    },
                    model="google/gemini-2.5-flash-preview-05-20",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Dane do uzupełnienia:{self.context.contract_data}"}
                    ],
                    response_model=PartContract,
                    temperature=0,
                )
                
                # Zapisz historię wywołania w kontekście
                self.context.metadata.llm_history.append({"role": "system", "content": f"Fragment {i+1}: {system_prompt[:100]}..."})
                self.context.metadata.llm_history.append({"role": "assistant", "content": f"Fragment {i+1}: {str(chunk_result)[:100]}..."})
                
                # Dodaj paragrafy z obecnego fragmentu do wyniku końcowego
                if chunk_result and hasattr(chunk_result, 'paragraphs'):
                    all_paragraphs.extend(chunk_result.paragraphs)
                    logger.info(f"Dodano {len(chunk_result.paragraphs)} paragrafów z fragmentu {i+1}")
                else:
                    logger.warning(f"Fragment {i+1} nie zwrócił żadnych paragrafów")
                    
            except Exception as e:
                logger.error(f"Błąd podczas przetwarzania fragmentu {i+1}: {e}")
        
        # Utwórz pełny wynik z wszystkich zebranych paragrafów
        self.__result = PartContract(paragraphs=all_paragraphs)
        logger.info(f"[ContractGeneratorAgent]: Zakończono generowanie umowy, utworzono {len(all_paragraphs)} paragrafów")
        
        return self.__result
    
    def _create_preamble(self):
        return Preamble(
            contract_date='2025-06-03',
            contract_location="Warszawa",
            party_one=self.context.contract_data.lessor,
            party_two=self.context.contract_data.lessee
        )
    
    def _init_contract(self):
        return Contract(
            paragraphs=self.__result.paragraphs,
            title="Umowa najmu mieszkania",
            preamble=self._create_preamble(),
            version='1',
        )

    def run(self) -> bool:
        logger.info(f"[ContractGeneratorAgent] Generating contract... Version: {self.context.metadata.current_version}")
        #logger.info(f"Contract data: {self.context.contract_data}")
        
        # Wywołaj metodę __process_contract, która teraz przetwarza fragmenty CONTRACT_KNOWLEDGE_MAP
        try:
            # Generowanie kontraktu
            response = self.__process_contract()
            logger.info(f"Wygenerowano kontrakt z {len(response.paragraphs)} paragrafami")

            #Initialize Contract() model
            self.context.current_contract = self._init_contract()
            logger.info(f"Zainicjalizowano kontrakt z {len(self.context.current_contract.paragraphs)} paragrafami")
            
            logger.info("Zapisano obiekt Contract w kontekście procesu dla innych agentów")
            
            """
            # Utwórz ścieżkę bazową projektu dla wszystkich plików wynikowych
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Zapisz wersję szczegółową bez myśli
            try:
                # Wywołaj verbose bez myśli
                verbose_output = self.verbose(thoughts=False)
                
                # Zapisz wynik do pliku
                verbose_file = os.path.join(base_dir, "umowa_najmu_verbose.md")
                with open(verbose_file, "w", encoding="utf-8") as file:
                    file.write(verbose_output)
                logger.info(f"Zapisano szczegółową umowę do pliku '{verbose_file}'")
            except Exception as verbose_error:
                logger.error(f"Błąd podczas generowania szczegółowej umowy: {verbose_error}")
                """
            """       
            # Zapisz wersję z myślami   
            try:
                
                # Wywołaj verbose z myślami
                thoughts_output = self.verbose(thoughts=True)
                
                # Zapisz wynik do pliku
                thoughts_file = os.path.join(base_dir, "umowa_najmu_with_thoughts.md")
                with open(thoughts_file, "w", encoding="utf-8") as file:
                    file.write(thoughts_output)
                logger.info(f"Zapisano umowę z myślami do pliku '{thoughts_file}'")
            except Exception as thoughts_error:
                logger.error(f"Błąd podczas generowania umowy z myślami: {thoughts_error}")
            """
            
            return True
        except Exception as e:
            logger.error(f"Błąd podczas generowania umowy: {e}")
            return False

    