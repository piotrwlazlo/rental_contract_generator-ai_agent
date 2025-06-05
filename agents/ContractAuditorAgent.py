from loguru import logger
from datetime import datetime
from openai import OpenAI
from structures.Context_exchange import ProcessContext
from structures.AuditRiskStructures import AuditResult, Risk, AuditChecklist
from agents.BaseAgent import BaseAgent
from knowledge_maps.audit_checklist_dict import audit_checklist_dict

#Audytor - ma on przeprowadzać audyt - implementuje metode run - wołą perform audit i wynik zapisuje do audit_history
class ContractAuditorAgent(BaseAgent):
    def __init__(self, process_context: ProcessContext, client: OpenAI):
        # Call parent's __init__ to properly initialize the context
        super().__init__(process_context, client)
        self.audit_checklist = AuditChecklist(**audit_checklist_dict)

    def _verbose(self, thoughts = False)-> str:
        response = ""
        if len(self.context.current_contract.paragraphs) == 0:
            logger.warning("Nie wygenerowano żadnych paragrafów")
        
        response += f"{self.context.current_contract.title}\n"
        response += f"\n\n"
            
        for p in self.context.current_contract.paragraphs:
            logger.info(f"Paragraf {p.id}: {p.title}")
            response += f"Paragraf {p.id}: {p.title}\n"
            
            for c in p.clauses:
                logger.action(f"Klauzula {c.id}: {c.text}")
                response += f"{c.id}: {c.text}\n"
                
                if thoughts:
                    for t in c.chain_of_thought:
                        logger.thought(f"[Clause - thought]: {t}")
                        response += f"[Clause - thought]: {t}\n"
                
                    logger.info(c.template)
                    response += f"Clause template: {c.template.model_dump_json(indent=2)}\n"
                
                response += "-" * 50 + "\n"
        
        return response

    def run(self) -> bool:
        logger.info(f"[ContractAuditorAgent] Auditing contract... Version: {self.context.metadata.current_version}")
        audit_result = self._perform_audit()
        
        # Add the audit result to the process context history
        self.context.metadata.audit_history.append(audit_result)
        self.context.metadata.last_update_time = datetime.now()
        
        version_info = f"Zakończono audyt wersji {self.context.metadata.current_version}"
        logger.info(version_info)
        self.context.metadata.llm_history.append({"role": "system", "content": version_info})
        
        # Log the audit result status - ensure we're reporting the correct number of risks
        if audit_result.is_approved:
            logger.info("Końcowa umowa\n")
            logger.info(self._verbose())
            logger.success("Audyt zakończony pomyślnie: Umowa zatwierdzona")
        else:
            risk_count = len(audit_result.risks) if audit_result.risks else 0
            logger.warning(f"Audyt zakończony z zastrzeżeniami: Znaleziono {risk_count} ryzyk")
        
        return audit_result.is_approved

    #perform_audit - sprawdza czy nie przekroczyliśmy maksymalnej liczby prób
    def _perform_audit(self) -> AuditResult:
        if self.context.metadata.current_revision_attempt >= self.context.metadata.max_revision_attempts:
            return AuditResult(
                is_approved = False,
                risks = [
                    Risk(
                        chain_of_thought=["Przekroczono maksymalną liczbę prób rewizji."],
                        content="Umowa nie może zostać zatwierdzona ze względu na przekroczenie maksymalnej liczby prób rewizji.",
                        suggested_changes=["Rozpocznij proces od początku z nowymi danymi."]
                    )
                ],
                timestamp=datetime.now()
            )
        
        # Przeprowadzenie audytu z wykorzystaniem LLM
        logger.info("Rozpoczynam audyt umowy z wykorzystaniem LLM")
        self.current_contract_new = self._verbose()
        
        system_prompt = """
        Jesteś ekspertem prawnym AI specjalizującym się w analizie umów. 
        Twoim zadaniem jest analiza tekstu umowy dostarczonego przez użytkownika, identyfikacja potencjalnych ryzyk prawnych, 
        wskazanie klauzul, które mogą być problematyczne, oraz wyjaśnienie swojego rozumowania krok po kroku. "

        Skup się na zgodności z polskim prawem, wykonalności oraz potencjalnych niejasnościach w tekście. 
        Gdzie to możliwe, dostarczaj praktyczne sugestie.
        
        Pamiętaj że audyt ma na celu znalezienie rażących błedów w umowach, jeżeli znajdziesz ryzyko które uznasz za mało istotne - nie podawaj go
        Jeśli nie znajdziesz w umowie żadnych ryzyk to nie zwracaj nic
        """

        user_prompt = f"""
        Przeanalizuj poniższy tekst umowy i zidentyfikuj potencjalne ryzyka. 
        Skup się na wykrywaniu niezgodności z obowiązującym w Polsce prawem, niejasności oraz klauzul wymagających doprecyzowania. 

        CHECKLIST
        {self.audit_checklist.json()}


        Tekst umowy: 
        {self.current_contract_new}
        """
        
        # Dodaj prompty do historii LLM w kontekście procesu
        self.context.metadata.llm_history.append({"role": "system", "content": system_prompt})
        self.context.metadata.llm_history.append({"role": "user", "content": user_prompt})
        
        try:
            logger.debug("Wysyłanie zapytania do modelu LLM w celu przeprowadzenia audytu")
            response = self.client.chat.completions.create(
                model="openai/gpt-4.1-mini",  # Użyj odpowiedniego modelu dostępnego w systemie
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=AuditResult, 
                temperature=0,  
            )
            
            # Dodaj odpowiedź modelu do historii LLM
            self.context.metadata.llm_history.append({"role": "assistant", "content": response})
            
            logger.info(f"Otrzymano wynik audytu: znaleziono {len(response.risks)} potencjalnych ryzyk")
            
            # Logowanie znalezionych ryzyk i zapisywanie szczegółowych informacji w kontekście
            risk_details = []
            for i, r in enumerate(response.risks):
                risk_info = f"Ryzyko {i+1}: {r.content}"
                logger.info(risk_info)
                risk_details.append(risk_info)
                
                # Logowanie łańcucha myśli (chain of thought)
                for c in r.chain_of_thought:
                    logger.thought(c)
                
                # Logowanie działania
                logger.action(f"Problem: {r.content}")
                
                # Logowanie sugerowanych zmian jako zwykłe komunikaty informacyjne
                for change in r.suggested_changes:
                    logger.info(f"Sugerowana zmiana: {change}")
                print()
                
            # Dodaj szczegółowe informacje o znalezionych ryzykach do kontekstu procesu
            self.context.metadata.llm_history.append({
                "role": "system", 
                "content": f"Audyt wersji {self.context.metadata.current_version}: Znaleziono {len(response.risks)} ryzyk"
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Wystąpił błąd podczas przeprowadzania audytu: {str(e)}")
            return AuditResult(
                is_approved=False,
                risks=[
                    Risk(
                        chain_of_thought=[f"Błąd podczas audytu: {str(e)}"],
                        content="Audyt nie mógł zostać przeprowadzony z powodu błędu technicznego.",
                        suggested_changes=["Sprawdź dostępność API lub ponów próbę później."]
                    )
                ],
                timestamp=datetime.now()
            )

