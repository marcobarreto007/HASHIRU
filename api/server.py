# -*- coding: utf-8 -*-
"""
Ezio Finance API Server.

Este arquivo contém a aplicação principal da API FastAPI que expõe os endpoints
para análise financeira.
"""

import logging
import uuid
import time

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configuração do logging enterprise antes de qualquer outra coisa
# É crucial que o logger seja configurado no início para capturar todos os eventos.
try:
    from .logging_setup import setup_enterprise_logging
    from .correlation import correlation_id
    setup_enterprise_logging()
    logger = logging.getLogger("superezio_enterprise.api_server")
except ImportError:
    # Fallback para logging básico se a configuração enterprise falhar
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning("Falha ao carregar logging enterprise, usando configuração básica.")
    # Mock context var if needed
    from contextvars import ContextVar
    correlation_id = ContextVar('correlation_id', default=None)


# Import dos componentes da aplicação
from .orchestrator import AnalysisOrchestrator, OllamaError
from .cache_manager import cache_manager
from contextlib import asynccontextmanager
from .decision_models import AggregateDecision, HealthStatus
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# --------------------------------------------------------------------------
# Gerenciamento do Ciclo de Vida da Aplicação (Lifespan)
# --------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    - Inicializa o cache na inicialização.
    - Fecha as conexões do cache no desligamento.
    """
    logger.info("Iniciando a aplicação Ezio Finance API...")
    await cache_manager.initialize()
    yield
    logger.info("Desligando a aplicação Ezio Finance API...")
    await cache_manager.close()

# --------------------------------------------------------------------------
# Inicialização da Aplicação FastAPI
# --------------------------------------------------------------------------

app = FastAPI(
    title="Ezio Finance API",
    description="API para análise financeira com IA para o Comitê de Investimentos Autônomo (IA-CEO).",
    version="1.1.0", # Versão incrementada para refletir as novas features
    lifespan=lifespan,
)

# --------------------------------------------------------------------------
# Middleware
# --------------------------------------------------------------------------

# Configuração do CORS para permitir o acesso de qualquer origem (adequado para desenvolvimento)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja a origens específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """
    Middleware para gerar e injetar um ID de correlação em cada requisição.
    Isso é essencial para a observabilidade e rastreamento de logs.
    """
    # Obter ID de correlação do header ou criar um novo
    corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    correlation_id.set(corr_id)

    start_time = time.time()
    logger.info(f"Requisição recebida: {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    response.headers["X-Correlation-ID"] = corr_id
    response.headers["X-Process-Time-Ms"] = str(process_time)

    logger.info(f"Requisição finalizada: {response.status_code} em {process_time:.2f}ms")
    return response


# --------------------------------------------------------------------------
# Modelos Pydantic para as Requisições e Respostas da API
# --------------------------------------------------------------------------

class AskRequest(BaseModel):
    """Schema para o corpo da requisição do endpoint /api/ask."""
    query: str = Field(..., description="A pergunta ou comando do usuário.", example="analise o sentimento e os fundamentos da TSLA")
    ticker: str = Field(..., description="O ticker do ativo a ser analisado.", example="TSLA")
    priority: str = Field("normal", description="A prioridade da requisição.", example="normal")

# --------------------------------------------------------------------------
# Endpoints da API
# --------------------------------------------------------------------------

@app.get("/metrics", tags=["Monitoring"])
def get_metrics():
    """
    Endpoint para expor as métricas no formato Prometheus.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/health", response_model=HealthStatus, tags=["Status"])
async def health_check():
    """
    Verifica a saúde da API e suas dependências críticas (Cache, Ollama).
    Retorna 'healthy' apenas se todos os componentes estiverem operacionais.
    """
    logger.info("Executando verificação de saúde completa do sistema.")

    # 1. Verificar Cache
    cache_backend_status = cache_manager.get_backend_status()
    is_cache_healthy = cache_backend_status == "redis"

    # 2. Verificar Ollama
    ollama_client = OllamaClient()
    is_ollama_healthy, ollama_status_msg = await ollama_client.check_health()
    await ollama_client.close()

    # 3. Determinar o status geral
    is_overall_healthy = is_cache_healthy and is_ollama_healthy
    api_status = "healthy" if is_overall_healthy else "degraded"

    dependencies_status = {
        "cache": "ok" if is_cache_healthy else "degraded",
        "ollama": "ok" if is_ollama_healthy else "degraded",
        "cache_backend_in_use": cache_backend_status,
        "ollama_details": ollama_status_msg,
    }

    logger.info(f"Resultado do Health Check: {api_status}", extra={"dependencies": dependencies_status})

    return HealthStatus(
        status=api_status,
        cache_backend=cache_backend_status,
        version=app.version,
        dependencies=dependencies_status,
    )


@app.post("/api/ask", response_model=AggregateDecision, tags=["Análise"])
async def ask_committee(request: AskRequest, http_response: JSONResponse):
    """
    Recebe uma consulta, orquestra o comitê de experts de IA, agrega
    suas análises e retorna a recomendação de investimento consolidada.
    """
    logger.info(f"Endpoint /api/ask (Comitê) chamado para o ticker: {request.ticker}")

    cache_key = f"ezio:ask:committee:{request.ticker}:{request.query}"

    # 1. Tentar obter a resposta do cache
    cached_dict = await cache_manager.get(cache_key)
    if cached_dict:
        http_response.headers["X-Cache"] = "HIT"
        logger.info(f"Cache HIT para a chave: {cache_key}. Validando o resultado do cache.")
        # Validar o dicionário do cache de volta para o modelo Pydantic
        return AggregateDecision.model_validate(cached_dict)

    # 2. Se for um MISS, executar a análise completa do comitê
    logger.info(f"Cache MISS para a chave: {cache_key}. Executando análise do comitê.")
    http_response.headers["X-Cache"] = "MISS"

    orchestrator = AnalysisOrchestrator()
    try:
        # Executa todos os experts em paralelo
        expert_analyses = await orchestrator.run_investment_committee(
            query=request.query, ticker=request.ticker
        )

        # Agrega os resultados em uma decisão final
        final_decision = orchestrator.aggregate_committee_results(
            expert_analyses=expert_analyses, query=request.query, ticker=request.ticker
        )

        # Armazena a decisão final no cache
        # .model_dump() é usado para serializar o objeto Pydantic para um dict, bom para o cache
        await cache_manager.set(cache_key, final_decision.model_dump())

        return final_decision

    except OllamaError as e:
        logger.error(f"Erro de serviço ao processar a análise para {request.ticker}: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(e)},
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao processar a requisição para {request.ticker}.")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Ocorreu um erro interno inesperado: {e}"},
        )
    finally:
        await orchestrator.close_connections()

# TODO: Adicionar o endpoint /api/analise, que pode ser uma versão mais simples
# ou diferente do /api/ask. Por enquanto, focamos no /api/ask que é mais complexo.
