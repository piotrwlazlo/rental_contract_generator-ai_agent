# AI-Powered Contract Processing System

## Overview

This project is an AI-powered system designed to automate the lifecycle of legal contracts, specifically focusing on rental agreements. It leverages multiple AI agents, each specializing in a different phase of contract management: data collection, contract generation, auditing for risks, and revising based on audit feedback. The system is orchestrated by a coordinator agent that manages the flow of information and control between the specialized agents.

## Features

*   **Automated Data Collection**: Interactively gathers necessary contract details from the user.
*   **AI-Driven Contract Generation**: Creates legally sound contract documents based on collected data and predefined knowledge.
*   **Comprehensive Auditing**: Analyzes generated contracts for potential legal risks and compliance issues using an AI legal expert.
*   **Intelligent Revision**: Modifies contract clauses based on audit findings to mitigate risks.
*   **Modular Agent-Based Architecture**: Easily extensible and maintainable due to its design around specialized agents.
*   **Contextual LLM Interaction History**: Keeps a log of all interactions with Large Language Models for transparency and debugging.

## How it Works

The application operates through a sequence of states managed by the `ContractCoordinator`:

1.  **Data Collection (`COLLECTING_DATA`)**: The `DataCollectorAgent` interacts with the user to gather all necessary information for the contract (e.g., lessor/lessee details, property information, rent terms).
2.  **Contract Generation (`GENERATING`)**: Once data collection is complete, the `ContractGeneratorAgent` uses this data and a knowledge base of contract templates/clauses to generate an initial draft of the contract.
3.  **Contract Auditing (`AUDITING`)**: The `ContractAuditorAgent` reviews the generated contract. It uses an AI model and a predefined checklist to identify potential legal risks, ambiguities, or non-compliance issues.
4.  **Contract Revision (`REVISING`)**: If the audit identifies risks, the `ContractReviserAgent` takes over. It uses the audit report to make specific changes to the contract, aiming to address the identified issues. The LLM is prompted with the original paragraph and the identified risk to generate a revised version.
5.  **Iteration**: After revision, the contract typically goes back to the `AUDITING` state. This loop continues until the audit is passed (no significant risks found) or the maximum number of revision attempts is reached.
6.  **Completion/Error**: The process concludes with a `COMPLETED` status if the contract is successfully audited and approved, or an `ERROR` status if issues cannot be resolved or an unrecoverable error occurs.

The entire process is managed within a `ProcessContext` object, which stores the current contract, collected data, metadata (like current status, version, audit history), and LLM interaction logs.

## Project Structure

The project is structured as follows:

*   `agents/`: Contains the implementation of the AI agents, each responsible for a specific phase of the contract lifecycle.
*   `knowledge_maps/`: Stores the knowledge maps used by the agents to guide their decision-making process.
*   `structures/`: Contains the data structures used by the agents to represent the contract and its metadata.
*   `app.py`: The main entry point of the application, which initializes the AI agents and manages the contract lifecycle.
*   `logging_config.py`: Configuration file for logging, which defines the format and level of logging used by the application.
*   `requirements.txt`: A list of dependencies required by the application.
*   `Readme.md`: A description of the project and its features.
