#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for capability detection and response functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock

# Import the modules we need to test
from main_agent_superezio import SuperEzioCommandRegistry, SuperEzioAgent, PerformanceMonitor


@pytest.mark.asyncio
async def test_capability_question_detection():
    """Test that capability questions are properly detected."""
    perf_monitor = PerformanceMonitor()
    command_registry = SuperEzioCommandRegistry()
    agent = SuperEzioAgent(command_registry, perf_monitor)
    
    # Test Portuguese capability question
    intent = await agent.analyze_intent("me diz o que vc é capaz de fazer")
    assert intent["tipo"] == "capability_question"
    assert intent["confidence"] == 0.9
    
    # Test English capability question
    intent = await agent.analyze_intent("what can you do?")
    assert intent["tipo"] == "capability_question"
    assert intent["confidence"] == 0.9
    
    # Test non-capability question
    intent = await agent.analyze_intent("olá, como você está?")
    assert intent["tipo"] != "capability_question"
    
    await agent.cleanup()


@pytest.mark.asyncio
async def test_capabilities_command():
    """Test that the /capabilities command works."""
    command_registry = SuperEzioCommandRegistry()
    
    # Test direct command dispatch
    response = await command_registry.dispatch("capabilities", "")
    assert "🌟 O que o SUPEREZIO é capaz de fazer" in response
    assert "AUTOMAÇÃO INTELIGENTE" in response
    assert "GERAÇÃO E ANÁLISE DE CÓDIGO" in response
    assert "RECURSOS ENTERPRISE" in response


@pytest.mark.asyncio
async def test_capability_question_execution():
    """Test that capability questions execute properly."""
    perf_monitor = PerformanceMonitor()
    command_registry = SuperEzioCommandRegistry()
    agent = SuperEzioAgent(command_registry, perf_monitor)
    
    # Test the complete flow from question to response
    user_input = "me diz o que vc é capaz de fazer"
    intent = await agent.analyze_intent(user_input)
    response = await agent.execute_plan(intent, user_input)
    
    assert "🌟 O que o SUPEREZIO é capaz de fazer" in response
    assert len(response) > 1000  # Should be a comprehensive response
    
    await agent.cleanup()


def test_capabilities_command_registration():
    """Test that capabilities commands are properly registered."""
    command_registry = SuperEzioCommandRegistry()
    
    # Test that both Portuguese and English versions are registered
    assert "capabilities" in command_registry.commands
    assert "capacidades" in command_registry.commands
    
    # Test command info
    capabilities_info = command_registry.commands["capabilities"]
    assert "Capacidades" in capabilities_info.description
    assert capabilities_info.category == "core"
    assert not capabilities_info.requires_args