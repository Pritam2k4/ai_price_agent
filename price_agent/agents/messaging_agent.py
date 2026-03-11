import os
from agents.deals import Opportunity
from agents.agent import Agent
import requests
from agents.llm_utils import logged_completion

pushover_url = "https://api.pushover.net/1/messages.json"


class MessagingAgent(Agent):
    name = "Messaging Agent"
    color = Agent.WHITE
    MODEL = "claude-sonnet-4-5"

    def __init__(self):
        """
        Set up this object to either do push notifications via Pushover,
        or SMS via Twilio,
        whichever is specified in the constants
        """
        self.log("Messaging Agent is initializing")
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        self.push_enabled = bool(self.pushover_user and self.pushover_token)
        if self.push_enabled:
            self.log("Messaging Agent is configured for Pushover notifications")
        else:
            self.log("Messaging Agent push disabled (set PUSHOVER_USER + PUSHOVER_TOKEN to enable)")

    def push(self, text):
        """
        Send a Push Notification using the Pushover API
        """
        if not getattr(self, "push_enabled", False):
            return
        self.log("Messaging Agent is sending a push notification")
        payload = {
            "user": self.pushover_user,
            "token": self.pushover_token,
            "message": text,
            "sound": "cashregister",
        }
        try:
            requests.post(pushover_url, data=payload, timeout=10)
        except Exception as e:
            self.log(f"Messaging Agent push failed (continuing): {e}")

    def alert(self, opportunity: Opportunity):
        """
        Make an alert about the specified Opportunity
        """
        text = f"Deal Alert! Price=${opportunity.deal.price:.2f}, "
        text += f"Estimate=${opportunity.estimate:.2f}, "
        text += f"Discount=${opportunity.discount:.2f} :"
        text += opportunity.deal.product_description[:10] + "... "
        text += opportunity.deal.url
        self.push(text)
        self.log("Messaging Agent has completed")

    def craft_message(
        self, description: str, deal_price: float, estimated_true_value: float
    ) -> str:
        user_prompt = "Please summarize this great deal in 2-3 sentences to be sent as an exciting push notification alerting the user about this deal.\n"
        user_prompt += f"Item Description: {description}\nOffered Price: {deal_price}\nEstimated true value: {estimated_true_value}"
        user_prompt += "\n\nRespond only with the 2-3 sentence message which will be used to alert & excite the user about this deal"
        try:
            response = logged_completion(
                model=self.MODEL,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            self.log(f"Messaging Agent craft_message failed; using fallback: {e}")
            return (
                f"Deal Alert! Offered ${deal_price:.2f} vs est ${estimated_true_value:.2f}. "
                f"{description[:120]}"
            )

    def notify(self, description: str, deal_price: float, estimated_true_value: float, url: str):
        """
        Make an alert about the specified details
        """
        self.log("Messaging Agent is using Claude to craft the message")
        text = self.craft_message(description, deal_price, estimated_true_value)
        self.push(text[:200] + "... " + url)
        self.log("Messaging Agent has completed")
