#!/usr/bin/env python3
from loguru import logger
from openai import OpenAI
from agents.ContractCoordinator import ContractCoordinator
from structures.ContractStatus import ContractStatus
import logging_config  # Configures the global loguru logger
import instructor
import os
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    client = instructor.patch(client, mode=instructor.Mode.MD_JSON)
    
    # Get user's preferred starting agent
    starting_status = ContractStatus.COLLECTING_DATA
    
    # Initialize the coordinator with the chosen starting status
    agent = ContractCoordinator(client)
    success = agent.process_contract(starting_status)
    
    if success:
        logger.info("Contract process completed successfully.")
    else:
        logger.error("Contract process failed.")