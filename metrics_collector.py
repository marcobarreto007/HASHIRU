# -*- coding: utf-8 -*-
"""
HASHIRU 14.3 - Sistema de Métricas

Implementa coleta de métricas de desempenho para o HASHIRU 14.3.

Autor: HASHIRU Team (Marco & Equipe)
Versão: 1.1
Data: 2025-08-06
"""

from __future__ import annotations
import json
import os
import time
import uuid
import asyncio
from datetime import datetime, UTC  # Importação do UTC para timezone-aware
from pathlib import Path
import logging

class MetricsCollector:
    """Coleta e armazena métricas de desempenho do sistema"""
    
    def __init__(self, metrics_path: str = "./metrics"):
        self.metrics_path = Path(metrics_path)
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_path / f"metrics_{datetime.now(UTC).strftime('%Y%m%d')}.jsonl"
        self._lock = asyncio.Lock()
        
        self.session_id = str(uuid.uuid4())
        self.session_metrics = {
            "session_id": self.session_id,
            "start_time": datetime.now(UTC).isoformat(),
            "requests": 0,
            "errors": 0,
            "model_usage": {},
            "response_times_ms": [],
            "tool_usage": {}
        }
        
        # Configurar logger
        self.logger = logging.getLogger("HASHIRU.Metrics")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
        
        self.logger.info(f"Sistema de métricas inicializado: {self.metrics_file}")
    
    async def record_request(self, model: str, duration_ms: float, error: bool = False, 
                            user_input_length: int = 0, response_length: int = 0):
        """Registra uma requisição ao modelo"""
        async with self._lock:
            self.session_metrics["requests"] += 1
            if error:
                self.session_metrics["errors"] += 1
                
            self.session_metrics["model_usage"][model] = self.session_metrics["model_usage"].get(model, 0) + 1
            self.session_metrics["response_times_ms"].append(duration_ms)
            
            log_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "session_id": self.session_id,
                "event": "model_request",
                "model": model,
                "duration_ms": duration_ms,
                "error": error,
                "input_length": user_input_length,
                "output_length": response_length
            }
            
            try:
                with open(self.metrics_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                self.logger.debug(f"Métrica de requisição registrada: {model}")
            except Exception as e:
                self.logger.error(f"Erro ao registrar métrica: {e}")
    
    async def record_tool_usage(self, tool_name: str, duration_ms: float, success: bool = True):
        """Registra uso de uma ferramenta"""
        async with self._lock:
            if tool_name not in self.session_metrics["tool_usage"]:
                self.session_metrics["tool_usage"][tool_name] = {
                    "count": 0, 
                    "success": 0, 
                    "failures": 0,
                    "total_duration_ms": 0
                }
                
            stats = self.session_metrics["tool_usage"][tool_name]
            stats["count"] += 1
            stats["total_duration_ms"] += duration_ms
            
            if success:
                stats["success"] += 1
            else:
                stats["failures"] += 1
                
            log_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "session_id": self.session_id,
                "event": "tool_usage",
                "tool": tool_name,
                "duration_ms": duration_ms,
                "success": success
            }
            
            try:
                with open(self.metrics_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                self.logger.debug(f"Métrica de ferramenta registrada: {tool_name}")
            except Exception as e:
                self.logger.error(f"Erro ao registrar métrica de ferramenta: {e}")
    
    async def record_streaming_stats(self, chunk_count: int, total_time_ms: float, chars_generated: int):
        """Registra estatísticas de streaming de respostas"""
        async with self._lock:
            log_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "session_id": self.session_id,
                "event": "streaming",
                "chunk_count": chunk_count,
                "total_time_ms": total_time_ms,
                "chars_generated": chars_generated
            }
            
            try:
                with open(self.metrics_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                self.logger.debug(f"Métrica de streaming registrada: {chunk_count} chunks")
            except Exception as e:
                self.logger.error(f"Erro ao registrar métrica de streaming: {e}")
    
    async def save_summary(self):
        """Salva um resumo da sessão atual"""
        async with self._lock:
            self.session_metrics["end_time"] = datetime.now(UTC).isoformat()
            
            # Calcular estatísticas
            if self.session_metrics["response_times_ms"]:
                times = self.session_metrics["response_times_ms"]
                self.session_metrics["avg_response_time_ms"] = sum(times) / len(times)
                self.session_metrics["min_response_time_ms"] = min(times)
                self.session_metrics["max_response_time_ms"] = max(times)
            
            log_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "session_id": self.session_id,
                "event": "session_summary",
                "summary": self.session_metrics
            }
            
            try:
                with open(self.metrics_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                self.logger.info(f"Resumo da sessão salvo: {self.session_metrics['requests']} requisições")
            except Exception as e:
                self.logger.error(f"Erro ao salvar resumo da sessão: {e}")

# Teste da classe
if __name__ == "__main__":
    async def test_metrics():
        metrics = MetricsCollector()
        await metrics.record_request("gpt-oss:20b", 1500.0, True, 150, 250)
        await metrics.record_tool_usage("read_file", 75.0, True)
        await metrics.save_summary()
        print("✅ Teste de métricas concluído!")
    
    # Executar teste
    asyncio.run(test_metrics())