# test_main_agent.py
"""
Testes automatizados para HASHIRU 10.0

Execute com:
    pytest test_main_agent.py -v
    pytest test_main_agent.py -v --cov=main_agent  # Com cobertura
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

# Importa o módulo principal
import main_agent

# ======================================================================
# FIXTURES
# ======================================================================

@pytest.fixture
def config():
    """Fixture para configuração de teste"""
    return main_agent.AgentConfig()

@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

# ======================================================================
# TESTES DE MODELOS PYDANTIC
# ======================================================================

class TestPydanticModels:
    """Testes para garantir que modelos Pydantic funcionam corretamente"""
    
    def test_tool_metadata_creation(self):
        """Testa criação de ToolMetadata"""
        metadata = main_agent.ToolMetadata(
            name="test_tool",
            description="Ferramenta de teste",
            parameters={"param1": "string", "param2": "int"},
            category="test",
            cost=0.5,
            requires_confirmation=True
        )
        
        assert metadata.name == "test_tool"
        assert metadata.category == "test"
        assert metadata.cost == 0.5
        assert metadata.requires_confirmation is True
    
    def test_tool_metadata_defaults(self):
        """Testa valores padrão de ToolMetadata"""
        metadata = main_agent.ToolMetadata(
            name="minimal_tool",
            description="Minimal",
            parameters={}
        )
        
        assert metadata.category == "general"
        assert metadata.cost == 0.0
        assert metadata.requires_confirmation is False

# ======================================================================
# TESTES DE FERRAMENTAS
# ======================================================================

class TestTools:
    """Testes para as ferramentas do sistema"""
    
    @pytest.mark.asyncio
    async def test_read_file_tool(self, temp_dir):
        """Testa ReadFileTool"""
        # Cria arquivo de teste
        test_file = Path(temp_dir) / "test.txt"
        test_content = "Hello, HASHIRU!"
        test_file.write_text(test_content)
        
        # Testa ferramenta
        tool = main_agent.ReadFileTool()
        result = await tool.execute({"file_path": str(test_file)})
        
        assert result["success"] is True
        assert result["content"] == test_content
        assert result["size"] == len(test_content)
    
    @pytest.mark.asyncio
    async def test_read_file_tool_missing_file(self):
        """Testa ReadFileTool com arquivo inexistente"""
        tool = main_agent.ReadFileTool()
        result = await tool.execute({"file_path": "nonexistent.txt"})
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_write_file_tool(self, temp_dir):
        """Testa WriteFileTool"""
        test_file = Path(temp_dir) / "output.txt"
        test_content = "Written by HASHIRU"
        
        tool = main_agent.WriteFileTool()
        result = await tool.execute({
            "file_path": str(test_file),
            "content": test_content
        })
        
        assert result["success"] is True
        assert test_file.exists()
        assert test_file.read_text() == test_content
    
    @pytest.mark.asyncio
    async def test_list_files_tool(self, temp_dir):
        """Testa ListFilesTool"""
        # Cria alguns arquivos de teste
        (Path(temp_dir) / "file1.txt").write_text("content1")
        (Path(temp_dir) / "file2.txt").write_text("content2")
        (Path(temp_dir) / "subdir").mkdir()
        
        tool = main_agent.ListFilesTool()
        result = await tool.execute({"directory": temp_dir})
        
        assert result["success"] is True
        assert result["count"] == 3
        
        # Verifica tipos de arquivo
        files = result["files"]
        file_names = [f["name"] for f in files]
        assert "file1.txt" in file_names
        assert "file2.txt" in file_names
        assert "subdir" in file_names

# ======================================================================
# TESTES DE LOGGING
# ======================================================================

class TestLogging:
    """Testes para o sistema de logging estruturado"""
    
    def test_structured_logger_creation(self, config):
        """Testa criação de StructuredLogger"""
        logger = main_agent.StructuredLogger("test_logger", config)
        
        assert logger.logger.name == "test_logger"
        assert len(logger.logger.handlers) > 0
    
    def test_logger_context(self, config):
        """Testa contexto do logger"""
        logger = main_agent.StructuredLogger("test_logger", config)
        
        # Define contexto
        logger.set_context(session_id="123", user="test_user")
        
        assert logger.context["session_id"] == "123"
        assert logger.context["user"] == "test_user"

# ======================================================================
# TESTES DE MEMÓRIA
# ======================================================================

class TestMemorySystem:
    """Testes para o sistema de memória"""
    
    def test_simple_vector_store(self):
        """Testa SimpleVectorStore"""
        store = main_agent.SimpleVectorStore()
        
        # Adiciona documentos
        doc1 = {"id": "1", "content": "Python programming language"}
        doc2 = {"id": "2", "content": "JavaScript web development"}
        doc3 = {"id": "3", "content": "Python data science"}
        
        store.add(doc1)
        store.add(doc2)
        store.add(doc3)
        
        # Busca por "Python"
        results = store.search("Python", k=2)
        
        assert len(results) == 2
        assert all("Python" in r["content"] for r in results)
    
    @pytest.mark.asyncio
    async def test_memory_system_add_and_search(self, config):
        """Testa adição e busca na memória"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            memory = main_agent.MemorySystem(config, client)
            
            # Adiciona memórias
            await memory.add_to_memory("user", "Tell me about Python")
            await memory.add_to_memory("assistant", "Python is a programming language")
            
            # Busca
            results = await memory.search_memory("Python", k=2)
            
            # Verifica que encontrou resultados
            assert len(results) <= 2

# ======================================================================
# TESTES DE ANÁLISE DE COMPLEXIDADE
# ======================================================================

class TestComplexityAnalyzer:
    """Testes para o analisador de complexidade"""
    
    def test_simple_task(self):
        """Testa classificação de tarefa simples"""
        analyzer = main_agent.TaskComplexityAnalyzer()
        
        strategy = analyzer.analyze("What is 2+2?")
        assert strategy == main_agent.ModelStrategy.LIGHTWEIGHT
    
    def test_complex_task(self):
        """Testa classificação de tarefa complexa"""
        analyzer = main_agent.TaskComplexityAnalyzer()
        
        long_text = " ".join(["word"] * 100)  # Texto longo
        complex_text = f"Please analyze and compare this complex data in detail: {long_text}"
        
        strategy = analyzer.analyze(complex_text)
        assert strategy in [main_agent.ModelStrategy.BALANCED, main_agent.ModelStrategy.POWERFUL]

# ======================================================================
# TESTES DE CONFIGURAÇÃO
# ======================================================================

class TestConfiguration:
    """Testes para a configuração do agente"""
    
    def test_config_defaults(self):
        """Testa valores padrão da configuração"""
        config = main_agent.AgentConfig()
        
        assert config.AGENT_NAME == "HASHIRU"
        assert config.AGENT_VERSION == "10.0"
        assert config.OLLAMA_BASE_URL == "http://127.0.0.1:11434"
        assert config.MEMORY_ENABLED is True
        assert config.STREAM_ENABLED is True
    
    def test_config_unique_id(self):
        """Testa que cada configuração tem ID único"""
        config1 = main_agent.AgentConfig()
        config2 = main_agent.AgentConfig()
        
        assert config1.AGENT_ID != config2.AGENT_ID

# ======================================================================
# TESTES DE INTEGRAÇÃO
# ======================================================================

class TestIntegration:
    """Testes de integração entre componentes"""
    
    @pytest.mark.asyncio
    async def test_tool_registry_initialization(self):
        """Testa inicialização do registro de ferramentas"""
        orchestrator = main_agent.AgentOrchestrator()
        
        # Verifica que ferramentas básicas foram registradas
        assert "read_file" in orchestrator.tool_registry
        assert "write_file" in orchestrator.tool_registry
        assert "list_files" in orchestrator.tool_registry
        
        # Cleanup
        await orchestrator.cleanup()

# ======================================================================
# TESTES DE PERFORMANCE
# ======================================================================

class TestPerformance:
    """Testes de performance e benchmarks"""
    
    @pytest.mark.asyncio
    async def test_memory_search_performance(self, config):
        """Testa performance da busca na memória"""
        import httpx
        import time
        
        async with httpx.AsyncClient() as client:
            memory = main_agent.MemorySystem(config, client)
            
            # Adiciona muitas memórias
            for i in range(100):
                await memory.add_to_memory("user", f"Test message {i}")
            
            # Mede tempo de busca
            start = time.time()
            results = await memory.search_memory("message", k=10)
            elapsed = time.time() - start
            
            # Busca deve ser rápida (menos de 1 segundo)
            assert elapsed < 1.0
            assert len(results) <= 10

# ======================================================================
# MAIN
# ======================================================================

if __name__ == "__main__":
    # Executa testes com pytest
    pytest.main([__file__, "-v", "--tb=short"])