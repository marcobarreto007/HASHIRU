import yfinance as yf
from phi3_dialog_processor import Phi3DialogProcessor
from platinum_analysts_manager import PlatinumAnalystsManager
from web_search import WebSearchEvolution
from dialog_memory import DialogMemoryManager

class DialogOrchestrator:
    """
    The central brain of the SuperEzio Dialog Cockpit.
    It coordinates all interactions between the user and the backend systems.
    """

    def __init__(self):
        print("Initializing Dialog Orchestrator...")
        self.dialog_processor = Phi3DialogProcessor()
        self.analysts_manager = PlatinumAnalystsManager()
        self.web_search = WebSearchEvolution()
        self.memory_manager = DialogMemoryManager()

        # A simple way to get the risk analyst for the 'trading' intent.
        self.risk_analyst = None
        for analyst in self.analysts_manager.analysts:
            if "Risk Manager" in analyst.name:
                self.risk_analyst = analyst
                break

        print(f"Discovered {self.analysts_manager.get_analyst_count()} analysts.")
        print("Dialog Orchestrator initialized successfully.")

    def handle_message(self, user_message: str) -> str:
        """
        Processes a user's message, routes it to the correct component,
        and returns a formatted response.

        :param user_message: The message from the user.
        :return: A string containing the assistant's response.
        """
        self.memory_manager.add_message(role="user", content=user_message)

        intent, entities = self.dialog_processor.classify_intent(user_message)

        print(f"Intent: {intent}, Entities: {entities}")

        response = ""
        try:
            if intent == 'analysis':
                if entities and 'symbol' in entities:
                    symbol = entities['symbol']
                    response = f"Consulting all {self.analysts_manager.get_analyst_count()} Platinum Analysts for {symbol.upper()}...\n\n"
                    response += self.analysts_manager.run_all_analysts(symbol)
                else:
                    response = "Please specify a stock symbol to analyze (e.g., 'Analyze AAPL')."

            elif intent == 'market_data':
                if entities and 'symbol' in entities:
                    symbol = entities['symbol']
                    response = self._get_market_data(symbol)
                else:
                    response = "Please specify a stock symbol for market data (e.g., 'MSFT price')."

            elif intent == 'web_search':
                search_results = self.web_search.search(user_message)
                if search_results:
                    response = "🔍 Here are the top web search results:\n\n"
                    for i, res in enumerate(search_results):
                        response += f"{i+1}. {res['title']}\n   {res.get('body', 'No snippet available.')}\n   Source: {res['href']}\n\n"
                else:
                    response = f"I couldn't find any web results for '{user_message}'."

            elif intent == 'trading':
                 if entities and 'symbol' in entities and self.risk_analyst:
                    symbol = entities['symbol']
                    response = "Trading action requested. First, assessing risk...\n\n"
                    response += self.risk_analyst.analyze(symbol)
                    response += "\n\nRecommendation: For now, I can only provide analysis. Please use your trading platform to execute trades."
                 else:
                    response = "For trading requests, please specify a stock symbol. I will perform a risk assessment."

            elif intent == 'help':
                response = self._get_help_message()

            elif intent == 'greeting':
                response = "Hello! I am the SuperEzio Dialog Assistant. How can I help you today?"

            elif intent == 'thanks':
                response = "You're welcome!"

            elif intent == 'goodbye':
                response = "Goodbye! Have a great day."

            else: # 'chat' or unknown intent
                response = self.dialog_processor.generate_response(user_message)

        except Exception as e:
            print(f"An error occurred in the orchestrator: {e}")
            response = "I'm sorry, an unexpected error occurred. Please try again."

        self.memory_manager.add_message(role="assistant", content=response)
        return response

    def _get_market_data(self, symbol: str) -> str:
        """Fetches and formats real-time market data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            # .info can be slow; use history for price data for better performance
            hist = ticker.history(period="2d")
            if hist.empty:
                 return f"Could not retrieve market data for {symbol}. Please check the ticker."

            price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            volume = hist['Volume'].iloc[-1]

            change = price - prev_close
            change_percent = (change / prev_close * 100)

            response = f"📊 Market Data for {symbol.upper()}:\n"
            response += f"   Price: ${price:.2f}\n"
            response += f"   Change: ${change:.2f} ({change_percent:.2f}%)\n"
            response += f"   Volume: {volume:,}\n"
            response += f"   Previous Close: ${prev_close:.2f}"

            return response
        except Exception as e:
            print(f"yfinance error for {symbol}: {e}")
            return f"I couldn't retrieve market data for {symbol}. It might be an invalid ticker."

    def _get_help_message(self) -> str:
        """Returns the help message with available commands."""
        return """
        I am the SuperEzio Dialog Cockpit assistant. Here's what I can do:

        **Analysis**: Get a comprehensive report from all 8 Platinum Analysts.
        *Example*: "Analyze AAPL" or "What do you think about TSLA?"

        **Market Data**: Get real-time price and volume for a stock.
        *Example*: "NVDA price" or "Current market data for SPY"

        **Web Search**: Search the web for news or information.
        *Example*: "Search for latest NVDA news"

        **Trading**: Request a trade (I will perform a risk assessment).
        *Example*: "Buy AAPL"

        **Chat**: Have a general conversation.
        *Example*: "Hello" or "Thank you"
        """

if __name__ == '__main__':
    # A non-interactive test for the orchestrator
    orchestrator = DialogOrchestrator()
    print("\n--- Dialog Orchestrator Non-Interactive Test ---")

    test_queries = [
        "Analyze AAPL",
        "MSFT price",
        "Search for NVDA news",
        "Buy GOOGL",
        "Hello",
        "Help me"
    ]

    for query in test_queries:
        print(f"\n--- Testing Query ---")
        print(f"You: {query}")
        assistant_response = orchestrator.handle_message(query)
        print(f"Assistant:\n{assistant_response}")

    print("\n--- Test Complete ---")
