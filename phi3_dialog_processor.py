import re
from typing import Dict, List, Optional, Tuple

class Phi3DialogProcessor:
    """
    Handles Natural Language Understanding, including intent classification
    and entity extraction.

    This implementation uses a keyword-based approach as a functional
    fallback, designed to be extended with a real NLU model like Phi-3.
    """

    def __init__(self, model_name: str = "microsoft/Phi-3-mini-4k-instruct"):
        self.model_name = model_name
        # In a full implementation, you would load the model and tokenizer here.
        # For example:
        # from transformers import AutoModelForCausalLM, AutoTokenizer
        # self.model = AutoModelForCausalLM.from_pretrained(model_name)
        # self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("Phi3DialogProcessor initialized (keyword-based fallback).")

    def classify_intent(self, text: str) -> Tuple[str, Optional[Dict]]:
        """
        Classifies the user's intent based on keywords and extracts entities.

        :param text: The user's input text.
        :return: A tuple containing the intent and a dictionary of entities.
        """
        text_lower = text.lower()

        # Define keywords for each intent
        intents = {
            'analysis': ['analyze', 'analysis', 'what do you think about', 'opinion on'],
            'market_data': ['price', 'data for', 'market data', 'how is'],
            'web_search': ['search', 'find', 'look up', 'what is', 'who is'],
            'trading': ['buy', 'sell', 'trade', 'position'],
            'help': ['help', 'what can you do', 'capabilities', 'commands'],
            'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon'],
            'goodbye': ['bye', 'goodbye', 'see you'],
            'thanks': ['thank you', 'thanks', 'appreciate it'],
        }

        # Intent classification logic
        for intent, keywords in intents.items():
            if any(keyword in text_lower for keyword in keywords):
                entities = self._extract_entities(text, intent)
                return intent, entities

        # Default to 'chat' if no other intent is found
        return 'chat', None

    def _extract_entities(self, text: str, intent: str) -> Optional[Dict]:
        """Extracts entities like stock symbols from the text."""
        if intent in ['analysis', 'market_data', 'trading']:
            symbol = self._extract_symbol(text)
            if symbol:
                return {'symbol': symbol}
        return None

    def _extract_symbol(self, text: str) -> Optional[str]:
        """
        Extracts a stock symbol (typically a 1-5 letter uppercase word) from text.
        This is a simple regex-based approach.
        """
        # Matches words that are 1-5 letters long and all uppercase.
        # This is a common pattern for US stock tickers.
        match = re.search(r'\b[A-Z]{1,5}\b', text)
        if match:
            return match.group(0)

        # Fallback for lowercase tickers mentioned after a keyword
        text_lower = text.lower()
        triggers = ['analyze', 'about', 'for']
        for trigger in triggers:
            if trigger in text_lower:
                # Try to find a potential ticker after the trigger word
                parts = text_lower.split(trigger)
                if len(parts) > 1:
                    potential_ticker = parts[1].strip().split()[0]
                    if re.match(r'^[a-z]{1,5}$', potential_ticker):
                        return potential_ticker.upper()

        return None

    def generate_response(self, text: str) -> str:
        """
        Generates a conversational response.
        In a full implementation, this would use the Phi-3 model.
        For now, it returns a simple canned response.
        """
        return "I'm sorry, I can only provide specific financial information. How can I help you with analysis, market data, or web search?"
