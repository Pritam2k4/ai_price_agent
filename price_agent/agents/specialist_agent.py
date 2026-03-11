from agents.agent import Agent
import os


class SpecialistAgent(Agent):
    """
    An Agent that runs our fine-tuned LLM that's running remotely on Modal
    """

    name = "Specialist Agent"
    color = Agent.RED

    def __init__(self):
        """
        Set up this Agent by creating an instance of the modal class
        """
        self.enabled = os.getenv("MODAL_ENABLED", "0") == "1"
        self.pricer = None
        self.log("Specialist Agent is initializing - connecting to modal")
        if not self.enabled:
            self.log("Specialist Agent disabled (set MODAL_ENABLED=1 to enable)")
            return
        try:
            import modal  # type: ignore

            Pricer = modal.Cls.from_name("pricer-service", "Pricer")
            self.pricer = Pricer()
        except Exception as e:
            self.enabled = False
            self.log(f"Specialist Agent disabled (modal unavailable): {e}")

    def price(self, description: str) -> float:
        """
        Make a remote call to return the estimate of the price of this item
        """
        if not getattr(self, "enabled", False) or self.pricer is None:
            self.log("Specialist Agent returning $0.00 (disabled)")
            return 0.0
        try:
            self.log("Specialist Agent is calling remote fine-tuned model")
            result = self.pricer.price.remote(description)
        except Exception as e:
            self.log(f"Specialist Agent failed - returning $0.00: {e}")
            return 0.0
        self.log(f"Specialist Agent completed - predicting ${result:.2f}")
        return result
