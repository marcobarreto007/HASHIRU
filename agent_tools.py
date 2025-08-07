# agent_tools.py
# -*- coding: utf-8 -*-
"""
Define e registra todas as Ferramentas (Tools) disponíveis para o agente HASHIRU.

Cada ferramenta é uma classe que herda de BaseTool, garantindo uma estrutura
consistente com nome, descrição e um método de execução.
"""
import os
from pathlib import Path
from typing import Dict, Any, Type
from pydantic import BaseModel, Field

# --- Classe Base para todas as Ferramentas ---

class BaseTool(BaseModel):
    """
    A classe base abstrata para todas as ferramentas do agente.
    Força a implementação de metadados essenciais e um método de execução.
    """
    name: str
    description: str

    def execute(self, tool_input: Dict[str, Any]) -> str:
        """O método que executa a lógica da ferramenta."""
        raise NotImplementedError("A subclasse deve implementar o método execute.")

    def get_description_for_llm(self) -> str:
        """Formata a descrição da ferramenta para ser enviada ao LLM."""
        return f"- `{self.name}`: {self.description}"

# --- Implementações Concretas das Ferramentas ---

class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = "Lê e retorna o conteúdo completo de um arquivo de texto. Use para examinar arquivos."

    def execute(self, tool_input: Dict[str, Any]) -> str:
        file_path = tool_input.get("file_path")
        if not file_path:
            return "Erro: O caminho do arquivo (file_path) não foi fornecido."
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Erro ao ler o arquivo {file_path}: {e}"

class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = "Escreve ou sobrescreve um arquivo de texto com o conteúdo fornecido. Use para criar ou modificar arquivos."

    def execute(self, tool_input: Dict[str, Any]) -> str:
        file_path = tool_input.get("file_path")
        content = tool_input.get("content")
        if file_path is None or content is None:
            return "Erro: 'file_path' e 'content' são necessários."
        try:
            # Garante que o diretório exista
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Arquivo '{file_path}' escrito com sucesso."
        except Exception as e:
            return f"Erro ao escrever o arquivo {file_path}: {e}"

class ListFilesTool(BaseTool):
    name: str = "list_files"
    description: str = "Lista todos os arquivos e pastas em um diretório específico. Use para explorar a estrutura do projeto."

    def execute(self, tool_input: Dict[str, Any]) -> str:
        directory = tool_input.get("directory", ".")
        try:
            files = os.listdir(directory)
            if not files:
                return f"O diretório '{directory}' está vazio."
            return "\n".join(files)
        except Exception as e:
            return f"Erro ao listar arquivos em '{directory}': {e}"


# --- Registro Central de Ferramentas ---
# O agente usará este dicionário para encontrar e executar as ferramentas.
# A chave é o nome da ferramenta, e o valor é uma instância da classe da ferramenta.
TOOL_REGISTRY: Dict[str, BaseTool] = {
    tool.name: tool for tool in [
        ReadFileTool(),
        WriteFileTool(),
        ListFilesTool(),
    ]
}

def get_tools_description_for_llm() -> str:
    """Gera uma string formatada com a descrição de todas as ferramentas para o prompt do LLM."""
    return "\n".join([tool.get_description_for_llm() for tool in TOOL_REGISTRY.values()])