import importlib
import inspect
import os
from typing import List

from analysts.base_analyst import BaseAnalyst


class PlatinumAnalystsManager:
    """Discovers, loads, and runs all Platinum Analysts."""

    def __init__(self):
        self.analysts: List[BaseAnalyst] = self._discover_analysts()

    def _discover_analysts(self) -> List[BaseAnalyst]:
        """
        Dynamically discovers and instantiates all analyst classes
        in the 'analysts' directory.
        """
        analyst_instances = []
        analyst_dir = 'analysts'
        for filename in os.listdir(analyst_dir):
            if filename.endswith('.py') and not filename.startswith('__') and filename != 'base_analyst.py':
                module_name = f"{analyst_dir}.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseAnalyst) and obj is not BaseAnalyst:
                            analyst_instances.append(obj())
                except ImportError as e:
                    print(f"Error importing analyst module {module_name}: {e}")
        return analyst_instances

    def run_all_analysts(self, symbol: str) -> str:
        """
        Runs all discovered analysts for a given stock symbol and
        returns a consolidated report.

        :param symbol: The stock symbol (e.g., 'AAPL').
        :return: A string containing the consolidated analysis report.
        """
        if not self.analysts:
            return "No analysts found."

        reports = []
        for analyst in self.analysts:
            try:
                report = analyst.analyze(symbol)
                reports.append(f"--- {analyst.name} ---\n{report}")
            except Exception as e:
                reports.append(f"--- {analyst.name} ---\nError: {e}")

        return "\n\n".join(reports)

    def get_analyst_count(self) -> int:
        """Returns the number of discovered analysts."""
        return len(self.analysts)
