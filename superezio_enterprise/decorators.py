# -*- coding: utf-8 -*-
"""
Módulo de Decorators Enterprise

Fornece decorators reusáveis que integram os principais serviços da aplicação
(cache, rate limiting, logging, etc.) de forma limpa e desacoplada.
"""

import logging
from functools import wraps
from typing import Callable, Any, Coroutine

from superezio_enterprise.cache import cache
from superezio_enterprise.rate_limiter import rate_limiter
from superezio_enterprise.correlation import CorrelationContext

# Logger configurado para o módulo
logger = logging.getLogger(f"superezio_enterprise.{__name__}")


def with_correlation(operation_name: str):
    """
    Decorator que envolve uma função em um CorrelationContext para rastreamento.
    """
    def decorator(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with CorrelationContext(operation_name=operation_name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def with_cache(key_func: Callable[..., str], ttl: int = None):
    """
    Decorator que aplica caching inteligente ao resultado de uma função assíncrona.

    Args:
        key_func: Uma função que gera uma chave de cache única a partir dos
                  argumentos da função decorada.
        ttl: TTL (Time-To-Live) específico para este cache, em segundos.
             Se não for fornecido, usa o padrão do cache.
    """
    def decorator(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = key_func(*args, **kwargs)

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache HIT para a chave: '%s'", cache_key)
                return cached_result

            logger.debug("Cache MISS para a chave: '%s'", cache_key)
            result = await func(*args, **kwargs)

            cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


def with_rate_limit(tokens: int = 1):
    """
    Decorator que aplica o rate limiting antes de executar a função.
    """
    def decorator(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not rate_limiter.acquire(tokens):
                logger.warning("Rate limit excedido. Bloqueando chamada para %s.", func.__name__)
                # Em um app real, poderíamos retornar uma resposta HTTP 429
                # ou uma mensagem específica para o usuário.
                raise ConnectionAbortedError("Rate limit excedido. Tente novamente mais tarde.")

            return await func(*args, **kwargs)
        return wrapper
    return decorator
