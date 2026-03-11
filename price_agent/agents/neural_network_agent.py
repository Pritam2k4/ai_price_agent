from agents.agent import Agent
from agents.deep_neural_network import DeepNeuralNetworkInference


class NeuralNetworkAgent(Agent):
    name = "Neural Network Agent"
    color = Agent.MAGENTA

    def __init__(self):
        """
        Initialize this object by loading in the saved model weights
        and the SentenceTransformer vector encoding model
        """
        self.log("Neural Network Agent is initializing")
        self.neural_network = DeepNeuralNetworkInference()
        self.neural_network.setup()
        self.enabled = True
        try:
            self.neural_network.load("deep_neural_network.pth")
            self.log("Neural Network Agent is ready and weights are loaded")
        except Exception as e:
            self.enabled = False
            self.log(f"Neural Network Agent disabled (could not load weights): {e}")

    def price(self, description: str) -> float:
        """
        Use the Deep Neural Network to estimate the price of the described item
        :param description: the product to be estimated
        :return: the price as a float
        """
        self.log("Neural Network Agent is starting a prediction")
        if not getattr(self, "enabled", False):
            self.log("Neural Network Agent returning $0.00 (disabled)")
            return 0.0
        try:
            result = self.neural_network.inference(description)
        except Exception as e:
            self.log(f"Neural Network Agent failed - returning $0.00: {e}")
            return 0.0
        self.log(f"Neural Network Agent completed - predicting ${result:.2f}")
        return result
