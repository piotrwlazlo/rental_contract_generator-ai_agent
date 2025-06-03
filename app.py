#!/usr/bin/env python3
from loguru import logger
from openai import OpenAI
from agents.ContractCoordinator import ContractCoordinator
from structures.ContractStatus import ContractStatus
import logging_config  # Configures the global loguru logger
import instructor
import os
from dotenv import load_dotenv

def get_starting_agent():
    """
    Asks the user which agent they want to start the process from.
    Returns the appropriate ContractStatus enum value.
    """
    print("\nWybierz, od którego agenta chcesz rozpocząć proces:")
    print("1. DataCollectorAgent - Zbieranie danych (domyślnie)")
    print("2. ContractAuditorAgent - Audytowanie umowy")
    
    choice = input("Twój wybór (1 lub 2): ").strip()
    
    if choice == "2":
        logger.info("Wybrano rozpoczęcie procesu od agenta audytującego.")
        return ContractStatus.AUDITING
    else:
        logger.info("Wybrano standardowy początek procesu od agenta zbierającego dane.")
        return ContractStatus.COLLECTING_DATA

if __name__ == "__main__":
    load_dotenv()
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    client = instructor.patch(client, mode=instructor.Mode.MD_JSON)
    
    # Get user's preferred starting agent
    starting_status = get_starting_agent()
    
    # Initialize the coordinator with the chosen starting status
    agent = ContractCoordinator(client)
    success = agent.process_contract(starting_status)
    
    if success:
        logger.info("Contract process completed successfully.")
    else:
        logger.error("Contract process failed.")