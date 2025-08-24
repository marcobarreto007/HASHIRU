from analysts.base_analyst import BaseAnalyst

class FundamentalAnalyst(BaseAnalyst):
    """Performs fundamental analysis."""

    @property
    def name(self) -> str:
        return "Fundamental Analyst"

    def analyze(self, symbol: str) -> str:
        # Placeholder implementation
        return f"FundamentalAnalyst Report for {symbol}: Company financials look stable."
