# -*- coding: utf-8 -*-
"""
Módulo Streamer de Resposta

Implementa a lógica para streaming de respostas. Isso é crucial para aplicações
que lidam com grandes volumes de dados ou modelos de linguagem, permitindo que
a resposta seja enviada em pedaços (chunks) à medida que é gerada.
"""

import logging
from typing import Generator, Any, Callable, Iterable

from .config import CONFIG

# Logger configurado para o módulo
logger = logging.getLogger(f"superezio_enterprise.{__name__}")


class ResponseStreamer:
    """
    Gerencia o processo de streaming de uma resposta a partir de uma função geradora.

    Se o streaming estiver desabilitado na configuração, ele pode opcionalmente
    agregar a resposta e retorná-la de uma só vez.
    """

    def __init__(self, generator_func: Callable[..., Iterable[Any]]):
        """
        Args:
            generator_func: Uma função que retorna um iterável (como um gerador)
                            que produz os chunks da resposta.
        """
        self.generator_func = generator_func
        logger.debug(
            "ResponseStreamer inicializado para a função: %s", generator_func.__name__
        )

    def stream(self, *args, **kwargs) -> Generator[Any, None, None]:
        """
        Inicia o processo de streaming se habilitado.

        Yields:
            Os chunks de dados gerados pela função.

        Raises:
            RuntimeError: Se o streaming estiver desabilitado e não houver fallback.
            Qualquer exceção gerada pela `generator_func`.
        """
        if not CONFIG.streaming_enabled:
            logger.warning(
                "Tentativa de streaming enquanto a feature está desabilitada. Abortando."
            )
            raise RuntimeError(
                "O streaming de respostas não está habilitado na configuração."
            )

        logger.info("Iniciando o streaming da resposta...")
        try:
            # Itera sobre o gerador e transmite cada chunk
            for chunk in self.generator_func(*args, **kwargs):
                yield chunk
            logger.info("Streaming da resposta concluído com sucesso.")
        except Exception:
            logger.error(
                "Ocorreu um erro durante o streaming da resposta.", exc_info=True
            )
            # Propaga a exceção para que o chamador possa tratá-la
            raise

    def stream_or_collect(self, *args, **kwargs) -> Any:
        """
        Inicia o streaming se habilitado. Se desabilitado, coleta todos os chunks,
        os une e retorna o resultado completo.
        Funciona melhor para chunks de string.
        """
        if CONFIG.streaming_enabled:
            # Retorna o próprio gerador para ser iterado pelo chamador
            return self.stream(*args, **kwargs)
        else:
            logger.info("Streaming desabilitado. Coletando a resposta completa...")
            try:
                # Coleta todos os chunks em uma lista e os une
                response_chunks = list(self.generator_func(*args, **kwargs))
                full_response = "".join(map(str, response_chunks))
                logger.info("Resposta completa coletada com sucesso.")
                return full_response
            except Exception:
                logger.error("Ocorreu um erro ao coletar a resposta.", exc_info=True)
                raise


# Exemplo de uso:
#
# def slow_text_generator(text: str) -> Generator[str, None, None]:
#     """Uma função geradora que simula a geração de texto por um LLM."""
#     import time
#     for word in text.split():
#         yield word + " "
#         time.sleep(0.1)
#
# streamer = ResponseStreamer(generator_func=slow_text_generator)
#
# # Para streaming:
# if CONFIG.streaming_enabled:
#     for chunk in streamer.stream("Esta é uma longa resposta a ser transmitida palavra por palavra."):
#         print(chunk, end="")
#
# # Para coletar tudo de uma vez:
# full_text = streamer.stream_or_collect("Esta é outra resposta.")
# print(full_text)
