from loguru import logger
from datetime import datetime
from openai import OpenAI
from structures.Context_exchange import ProcessContext
from structures.AuditRiskStructures import AuditResult
from structures.ContractGenerationStructure import Contract, Paragraph  
from agents.BaseAgent import BaseAgent

class ContractReviserAgent(BaseAgent):
    def __init__(self, context: ProcessContext, client: OpenAI):
        super().__init__(context, client)

    def run(self) -> bool:
        logger.info(f"[ContractReviserAgent] Revising contract... Version: {self.context.metadata.current_version}")

        if not self.context.metadata.audit_history:
            logger.info("[ContractReviserAgent] No audit history found. Nothing to revise.")
            return True  # Jeśli brak historii audytów, zwróć sukces
            
        last_audit = self.context.metadata.audit_history[-1]
        
        if self._apply_changes(last_audit):
            self.context.metadata.current_version += 1
            self.context.metadata.current_revision_attempt += 1
            self.context.metadata.last_update_time = datetime.now()
            return True
        return False

    #Metoda naprawiająca błędy w umowie na podstawie wyników audytu
    def _apply_changes(self, last_audit: AuditResult) -> bool:
        _contract_data = self.context.current_contract
        
        logger.info(f"Rozpoczynam proces wprowadzania zmian na podstawie audytu")
        logger.info(f"Ostatni audit: {last_audit}")

        if not last_audit.risks:
            logger.info("Brak ryzyk do naprawienia w ostatnim audycie. Kontrakt pozostaje bez zmian.")
            return True

        llm_responses = []

        for risk_idx, risk in enumerate(last_audit.risks):
            logger.info(f"Przetwarzam ryzyko {risk_idx + 1}/{len(last_audit.risks)}: {risk.content}")

            # Znajdowanie odpowiedniego paragrafu z self._contract_data.paragraphs
            matching_paragraph_obj = None
            original_paragraph_index = -1 # Potrzebne do podmiany obiektu na liście
            if hasattr(_contract_data, 'paragraphs') and _contract_data.paragraphs:
                for i, p_obj in enumerate(_contract_data.paragraphs):
                    if p_obj.id == risk.paragraph: # risk.paragraph is the integer ID
                        matching_paragraph_obj = p_obj
                        original_paragraph_index = i
                        break
            
            if not matching_paragraph_obj:
                logger.warning(f"Nie znaleziono paragrafu o ID: {risk.paragraph} w self._contract_data.paragraphs dla ryzyka: '{risk.content}'. Pomijam to ryzyko.")
                continue # Przejdź do następnego ryzyka

            # Formatowanie treści paragrafu dla LLM
            paragraph_details_for_llm = f"ORYGINALNY PARAGRAF UMOWY (ID: {matching_paragraph_obj.id}):\n"
            paragraph_details_for_llm += f"Tytuł: {matching_paragraph_obj.title}\n\n"
            paragraph_details_for_llm += "Klauzule:\n"
            for clause_obj in matching_paragraph_obj.clauses:
                paragraph_details_for_llm += f" {clause_obj.id}: {clause_obj.text}\n"
            paragraph_details_for_llm += "\n" # Dodatkowa nowa linia dla czytelności

            # Budowanie promptu dla LLM
            system_prompt = """
            Jesteś ekspertem prawnym AI specjalizującym się w umowach dot. wynajmu mieszkań. 
            Twoim zadaniem jest poprawa klauzul na podstawie dostarczonego audytu. 
            """
            
            user_prompt = f"""
            Przeanalizuj poniższy problem w umowie i dokonaj rewizji wskazanego paragrafu.
            
            PROBLEM DO ROZWIĄZANIA:
            {risk.content}
            
            UZASADNIENIE PROBLEMU:
            {risk.chain_of_thought}
            
            SUGEROWANE ZMIANY PRZEZ AUDYT (potraktuj jako wskazówki, niekoniecznie dosłowne instrukcje):
            {', '.join(risk.suggested_changes)}
            
            FRAGMENT UMOWY:
            {paragraph_details_for_llm}

            KLUCZOWE DANE KONTRAKTU:
            {self.context.contract_data}

            Proszę o zaproponowanie konkretnej poprawki do umowy, która rozwiąże ten problem.
            Jeżeli problem odnosi się tylko do jednej konkretnej klauzuli zmodyfikuj tylko tą klauzulę, 
            resztę klauzul pozostaw bez zmian
            """
            
            try:
                # Wywołanie API do LLM
                response = self.client.chat.completions.create(
                    model="openai/gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_model = Paragraph,
                    max_retries = 2,
                )
                
                logger.info(f"Otrzymano zrewidowany paragraf (ID: {response.id}) od LLM dla ryzyka: {risk.content[:50]}...")
                logger.debug(f"Pełna odpowiedź LLM (Paragraph object): {response}")

                # Walidacja i uzupełnienie danych z LLM, aby zapewnić spójność
                response.id = matching_paragraph_obj.id # Gwarantujemy zgodność ID paragrafu
                
                # Aktualizacja paragrafu w kontrakcie
                if original_paragraph_index != -1:
                    _contract_data.paragraphs[original_paragraph_index] = response
                    logger.success(f"Paragraf ID: {matching_paragraph_obj.id} został zaktualizowany w kontrakcie.")
                    llm_responses.append({
                        "risk": risk.content,
                        "suggested_changes": risk.suggested_changes,
                        "original_paragraph_id": matching_paragraph_obj.id,
                        "revised_paragraph_title": response.title,
                        "clauses_count": len(response.clauses),
                    })
                    logger.info(f"Zmiana wprowadzona do paragrafu ID: {matching_paragraph_obj.id}")
                    logger.info(f"Paragraf: {llm_responses}")
                else:
                    logger.error(f"Nie udało się znaleźć indeksu dla paragrafu ID: {matching_paragraph_obj.id}. Nie można zaktualizować kontraktu.")
                    llm_responses.append({
                        "risk": risk.content,
                        "suggested_changes": risk.suggested_changes,
                        "llm_response": "Failed to find paragraph index for update",
                        "error": True
                    })

            except Exception as e:
                logger.error(f"Błąd podczas wywoływania LLM lub przetwarzania odpowiedzi dla ryzyka '{risk.content}': {e}")
                llm_responses.append({
                    "risk": risk.content,
                    "suggested_changes": risk.suggested_changes,
                    "llm_response": response
                })
                continue # Przejdź do następnego ryzyka
        
        self.context.metadata.llm_history.append({
            "role": "system", 
            "content": f"Propozycje zmian w umowie na podstawie audytu ({len(llm_responses)} ryzyk)"
        })
        
        for i, responses in enumerate(llm_responses):
            self.context.metadata.llm_history.append({
                "role": "assistant", 
                "content": f"Ryzyko {i+1}: {responses['risk']}...\nOdpowiedź: {responses['suggested_changes']}"
            })
            
        logger.success(f"Wprowadzono propozycje zmian dla {len(llm_responses)} ryzyk")
        return True

    