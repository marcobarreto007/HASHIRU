# -*- coding: utf-8 -*-
"""
Cache Manager com fallback para memória.

Este módulo fornece um gerenciador de cache que tenta se conectar ao Redis.
Se a conexão falhar, ele automaticamente utiliza um cache em memória como fallback.
"""

import logging
import json
from typing import Optional, Any, Dict
import redis.asyncio as redis
from redis.exceptions import ConnectionError
from pydantic import BaseModel
from api.metrics import CACHE_HITS, CACHE_MISSES

# Configurar um logger para este módulo
logger = logging.getLogger(__name__)

# TODO: Mover para um arquivo de configuração
REDIS_URL = "redis://localhost:6379"
CACHE_TTL_SECONDS = 900  # 15 minutos

class CacheManager:
    """
    Gerenciador de Cache genérico que prioriza Redis, com fallback para um cache em memória.
    Armazena e recupera dados como dicionários serializados em JSON.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized') and self.initialized:
            return

        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, str] = {} # Armazena strings JSON
        self.backend = "uninitialized"
        self.initialized = False
        logger.info("Instância do CacheManager criada.")

    async def initialize(self):
        if self.initialized:
            return

        try:
            logger.info(f"Tentando conectar ao Redis em {REDIS_URL}...")
            # decode_responses=True é importante para obter strings
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
            self.backend = "redis"
            logger.info("✅ Conexão com Redis estabelecida com sucesso. Backend de cache: Redis.")
        except ConnectionError as e:
            logger.warning(f"⚠️ Não foi possível conectar ao Redis: {e}. Usando cache em memória como fallback.")
            self.redis_client = None
            self.backend = "memory"
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao inicializar o cliente Redis: {e}. Usando cache em memória.")
            self.redis_client = None
            self.backend = "memory"

        self.initialized = True

    def get_backend_status(self) -> str:
        return self.backend

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Busca um valor no cache e o retorna como um dicionário.
        """
        if not self.initialized: await self.initialize()

        cached_json_str: Optional[str] = None
        logger.debug(f"Buscando chave '{key}' no cache (backend: {self.backend}).")

        if self.redis_client and self.backend == "redis":
            try:
                cached_json_str = await self.redis_client.get(key)
            except ConnectionError as e:
                logger.error(f"Perda de conexão com o Redis ao buscar a chave '{key}': {e}. Usando cache em memória.")
                self.backend = "memory"
                return await self.get(key)

        elif self.backend == "memory":
            cached_json_str = self.memory_cache.get(key)

        if cached_json_str:
            logger.info("Cache HIT.", extra={"cache_key": key, "cache_status": "HIT", "cache_backend": self.backend})
            CACHE_HITS.labels(backend=self.backend).inc()
            try:
                return json.loads(cached_json_str)
            except json.JSONDecodeError:
                logger.error("Erro ao decodificar JSON do cache.", extra={"cache_key": key, "cache_value": cached_json_str})
                return None

        logger.info("Cache MISS.", extra={"cache_key": key, "cache_status": "MISS", "cache_backend": self.backend})
        CACHE_MISSES.labels(backend=self.backend).inc()
        return None

    async def set(self, key: str, value: Any):
        """
        Armazena um valor no cache, serializando-o para JSON.
        Aceita objetos Pydantic ou dicionários.
        """
        if not self.initialized: await self.initialize()

        # Converte o valor para um dicionário se for um modelo Pydantic
        if isinstance(value, BaseModel):
            dict_value = value.model_dump()
        elif isinstance(value, dict):
            dict_value = value
        else:
            logger.error(f"Tipo de valor não suportado para cache: {type(value)}", extra={"cache_key": key})
            raise TypeError("O valor para cache deve ser um modelo Pydantic ou um dicionário.")

        # Serializa o dicionário para uma string JSON
        try:
            value_json = json.dumps(dict_value)
        except TypeError as e:
            logger.error(f"Erro ao serializar valor para JSON para a chave '{key}': {e}", extra={"cache_key": key})
            raise

        if self.redis_client and self.backend == "redis":
            try:
                await self.redis_client.set(key, value_json, ex=CACHE_TTL_SECONDS)
                logger.info("Chave armazenada no cache.", extra={"cache_key": key, "cache_ttl": CACHE_TTL_SECONDS, "cache_backend": "redis"})
            except ConnectionError as e:
                logger.error(f"Perda de conexão com o Redis ao armazenar a chave '{key}': {e}. Usando cache em memória.", extra={"cache_key": key})
                self.backend = "memory"
                await self.set(key, dict_value) # Tenta novamente com o cache em memória

        elif self.backend == "memory":
            self.memory_cache[key] = value_json
            logger.info("Chave armazenada no cache.", extra={"cache_key": key, "cache_ttl": "infinito", "cache_backend": "memory"})

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Conexão do CacheManager com o Redis fechada.")

cache_manager = CacheManager()
