from structures.Context_exchange import ProcessContext
from openai import OpenAI

class BaseAgent:
    """Klasa bazowa dla wszystkich agentów"""

    def __init__(self, process_context: ProcessContext, client: OpenAI):
        self.context = process_context
        self.client = client

    def run(self) -> bool:
        raise NotImplementedError