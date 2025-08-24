from analysts.base_analyst import BaseAnalyst

class EventDetectorAnalyst(BaseAnalyst):
    """Detects significant events for a stock."""

    @property
    def name(self) -> str:
        return "Event Detector Analyst"

    def analyze(self, symbol: str) -> str:
        # Placeholder implementation
        return f"EventDetectorAnalyst Report for {symbol}: No significant events detected."
