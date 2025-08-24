import abc

class BaseAnalyst(abc.ABC):
    """Abstract base class for all Platinum Analysts."""

    @abc.abstractmethod
    def analyze(self, symbol: str) -> str:
        """
        Run analysis for a given stock symbol.

        :param symbol: The stock symbol (e.g., 'AAPL').
        :return: A string containing the analysis report.
        """
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of the analyst."""
        pass
