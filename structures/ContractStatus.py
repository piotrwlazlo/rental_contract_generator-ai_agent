from enum import Enum

#Struktury opisujące w którym miejsca agenta się znajdujemy
# COMPLETED - jeśli cały system zadziała, ERROR jeśli coś się wywróci
#Potrzebny dla klasy ContractCoordinator który będzie globalnym planerem
#Globalny planer ma rozkładać duże zadanie na mniejsze zadanie które mają być wykonywane przez pojedynczych agentów
class ContractStatus(Enum):
    COLLECTING_DATA = "collecting_data"
    GENERATING = "generating"
    AUDITING = "auditing"
    REVISING = "revising"
    COMPLETED = "completed"
    ERROR = "error"