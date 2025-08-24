# -*- coding: utf-8 -*-
"""
Base structures for defining experts.
"""

from dataclasses import dataclass
from typing import Type
from pydantic import BaseModel

@dataclass
class ExpertDefinition:
    """
    A standard structure for defining an expert.

    This dataclass provides a consistent interface for the orchestrator to
    discover and use experts. Each expert module should instantiate this
    class to expose its capabilities.
    """
    name: str
    prompt_template: str
    response_model: Type[BaseModel]
    model_name: str = "llama3"  # Default model, can be overridden by the expert
