# -*- coding: utf-8 -*-
"""
Módulo de Utilitários de Segurança

Fornece um conjunto de funções robustas para a segurança da aplicação. Isso inclui
sanitização de entradas para prevenir ataques de injeção (XSS, etc.), validação de
caminhos de arquivo para evitar Directory Traversal, e outras checagens essenciais.
"""

import re
import os
import logging

from .config import CONFIG

# Logger configurado para o módulo
logger = logging.getLogger(f"superezio_enterprise.{__name__}")

# Compila as expressões regulares uma vez para melhor performance
_DANGEROUS_PATTERNS = re.compile(
    r"(<script|javascript:|vbscript:|onload=|onerror=|onmouseover=|onfocus=|onclick=)",
    re.IGNORECASE,
)

_DIRECTORY_TRAVERSAL_PATTERN = re.compile(r"\.\.|/")


def sanitize_input(text: str, truncate: bool = True) -> str:
    """
    Sanitiza e trunca uma string de entrada para remover conteúdo potencialmente perigoso.

    - Remove substrings perigosas (ex: <script, javascript:).
    - Trunca a mensagem para o comprimento máximo definido na configuração.

    Args:
        text: A string de entrada a ser sanitizada.
        truncate: Se True, trunca a mensagem se ela exceder o limite.

    Returns:
        A string sanitizada e, opcionalmente, truncada.
    """
    if not isinstance(text, str):
        logger.warning(
            "Entrada de sanitização não era uma string. Retornando string vazia."
        )
        return ""

    # Truncamento
    if truncate and len(text) > CONFIG.max_message_length:
        logger.warning("A entrada excedeu o comprimento máximo e foi truncada.")
        text = text[: CONFIG.max_message_length] + "... [truncated]"

    # Filtragem de padrões perigosos
    text, num_replacements = _DANGEROUS_PATTERNS.subn("[filtered]", text)
    if num_replacements > 0:
        logger.warning(
            "Potenciais vetores de ataque foram removidos da entrada. Foram encontradas %d ocorrências.",
            num_replacements,
        )

    return text


def is_path_safe(path: str, base_dir: str) -> bool:
    """
    Verifica se um caminho de arquivo é seguro e não tenta sair do diretório base.
    Previne ataques de Directory Traversal.

    Args:
        path: O caminho do arquivo a ser verificado.
        base_dir: O diretório base absoluto contra o qual o caminho será validado.

    Returns:
        True se o caminho for seguro, False caso contrário.
    """
    if not path or not base_dir:
        return False

    # Previne ataques de path traversal (ex: ../../etc/passwd)
    if _DIRECTORY_TRAVERSAL_PATTERN.search(path):
        logger.critical(
            "Ataque de Directory Traversal detectado e bloqueado. Caminho: '%s'", path
        )
        return False

    # Resolve o caminho absoluto e verifica se ele está dentro do diretório base
    try:
        absolute_path = os.path.abspath(os.path.join(base_dir, path))
        absolute_base_dir = os.path.abspath(base_dir)

        if not absolute_path.startswith(absolute_base_dir):
            logger.critical(
                "Ataque de Directory Traversal detectado e bloqueado. O caminho resolvido '%s' está fora do diretório base '%s'.",
                absolute_path,
                absolute_base_dir,
            )
            return False

    except Exception as e:
        logger.error(
            "Erro ao validar o caminho de arquivo seguro: %s", e, exc_info=True
        )
        return False

    logger.debug("O caminho '%s' foi validado como seguro.", path)
    return True
