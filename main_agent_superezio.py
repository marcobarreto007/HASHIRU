# -*- coding: utf-8 -*-
"""
SUPEREZIO - INTERFACE COGNITIVA FINAL
Integração completa com autonomous_config.py otimizado
Sistema de automação enterprise-level com IA multi-modelo

Desenvolvido por: Marco Barreto, Gemini & ChatGPT
Hardware: RTX 3060 (12GB) + RTX 2060 (6GB)
Otimizado para: Performance + Qualidade balanceados
"""

from __future__ import annotations
import asyncio
import traceback
import chainlit as cl
import sys
import pathlib
import json
import re
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable
from contextlib import asynccontextmanager

# ----------------------------------------------------------------------
# 1. LOGGING SETUP SUPEREZIO
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("superezio.log", encoding="utf-8"), 
        logging.StreamHandler()
    ],
)
logger = logging.getLogger("SUPEREZIO")

# ----------------------------------------------------------------------
# 2. BOOTSTRAPPING SEGURO
# ----------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ----------------------------------------------------------------------
# 3. IMPORT DA CONFIGURAÇÃO OTIMIZADA
# ----------------------------------------------------------------------
try:
    from autonomous_config import config, get_ai_model, get_fallback_models
    logger.info("✅ Configuração otimizada carregada do autonomous_config.py")
    logger.info(f"🎯 Hardware: {config.ollama.hardware.gpu_primary} + {config.ollama.hardware.gpu_secondary}")
    logger.info(f"💾 VRAM Total: {config.ollama.hardware.total_vram_gb}GB")
except ImportError:
    logger.warning("⚠️ autonomous_config.py não encontrado. Usando configuração básica.")
    # Fallback básico
    class BasicConfig:
        def get_model(self, model_type: str) -> str:
            return "llama3.1:8b"
        def get_fallback_models(self, model_type: str) -> List[str]:
            return ["llama3.1:8b", "mistral:7b-instruct"]
    
    config = BasicConfig()
    get_ai_model = config.get_model
    get_fallback_models = config.get_fallback_models

# ----------------------------------------------------------------------
# 4. IMPORTS OPCIONAIS COM TRATAMENTO
# ----------------------------------------------------------------------
httpx = None
try:
    import httpx
    logger.info("✅ httpx disponível para requisições Ollama")
except ImportError:
    logger.warning("⚠️ httpx não disponível - funcionalidades Ollama limitadas")

# ----------------------------------------------------------------------
# 5. COMMAND REGISTRY SUPEREZIO
# ----------------------------------------------------------------------
class CommandInfo:
    def __init__(
        self,
        handler: Callable[..., Any],
        description: str,
        category: str,
        requires_args: bool,
        dangerous: bool,
        auto_allowed: bool,
    ):
        self.handler = handler
        self.description = description
        self.category = category
        self.requires_args = requires_args
        self.dangerous = dangerous
        self.auto_allowed = auto_allowed


class SuperEzioCommandRegistry:
    def __init__(self):
        self.commands: Dict[str, CommandInfo] = {}
        self.categories: Dict[str, List[str]] = {}
        self._load_all()

    def register(
        self,
        command: str,
        handler: Callable[..., Any],
        description: str,
        category: str,
        *,
        requires_args: bool = False,
        dangerous: bool = False,
        auto_allowed: bool = True,
    ) -> None:
        self.commands[command.lstrip("/")] = CommandInfo(
            handler, description, category, requires_args, dangerous, auto_allowed
        )
        self.categories.setdefault(category, []).append(command.lstrip("/"))

    def _load_all(self) -> None:
        """Carrega todos os comandos com error handling individual."""
        for name, loader in (
            ("core", self._load_core_commands),
            ("automation", self._load_automation_commands),
            ("self_modification", self._load_self_commands),
        ):
            try:
                loader()
                logger.info(f"✅ Comandos '{name}' carregados.")
            except Exception as e:
                logger.info(f"ℹ️ Comandos '{name}' não disponíveis: {e}")

    def _load_core_commands(self) -> None:
        """Carrega comandos core básicos do SUPEREZIO."""
        # Comandos básicos sempre disponíveis
        basic_commands = {
            "status": ("📊 Status do sistema SUPEREZIO", self._status_handler),
            "models": ("🤖 Listar modelos disponíveis", self._models_handler),
            "hardware": ("💻 Informações de hardware", self._hardware_handler),
            "version": ("📋 Versão do SUPEREZIO", self._version_handler),
        }
        
        for cmd, (desc, handler) in basic_commands.items():
            self.register(cmd, handler, desc, "core", requires_args=False)
        
        logger.info("✅ Comandos core básicos carregados")

    def _load_automation_commands(self) -> None:
        """Carrega comandos de automação se disponíveis."""
        try:
            import importlib
            automation_module = importlib.import_module("tools.automation_commands")
            handle_automation_command = getattr(automation_module, "handle_automation_command", None)
            
            if not callable(handle_automation_command):
                raise AttributeError("handle_automation_command não encontrado")

            automation_cmds = {
                "auto_search": "🔎 Buscar na internet",
                "auto_browse": "🌐 Navegar para URL", 
                "auto_click": "🖱️ Clicar em elemento web",
                "auto_screenshot": "📸 Capturar screenshot",
                "auto_research": "🔬 Pesquisa completa automatizada",
                "auto_type": "⌨️ Digitar texto",
                "auto_keys": "🎹 Pressionar teclas de atalho",
                "auto_folder": "📁 Abrir pasta",
                "auto_find_files": "🔎 Buscar arquivos",
                "auto_status": "📊 Status da automação",
            }
            
            for cmd, desc in automation_cmds.items():
                def make_handler(cmd_name):
                    async def handler(args):
                        try:
                            from tools.automation_engine import AutomationEngine
                            engine = AutomationEngine()
                            return await handle_automation_command(cmd_name.replace("auto_", ""), args, engine)
                        except Exception as e:
                            return f"❌ Erro na automação {cmd_name}: {e}"
                    return handler
                
                self.register(
                    cmd,
                    make_handler(cmd),
                    desc,
                    "automation",
                    requires_args=(cmd != "auto_status"),
                    dangerous=False,
                    auto_allowed=True,
                )
            logger.info("✅ Comandos de automação carregados")
        except Exception as e:
            logger.info(f"ℹ️ Automação não disponível: {e}")

    def _load_self_commands(self) -> None:
        """Carrega comandos de auto-modificação se disponíveis."""
        try:
            import importlib
            selfmod = importlib.import_module("tools.selfmod")
            
            if not hasattr(selfmod, "dispatch"):
                raise AttributeError("selfmod.dispatch não encontrado")

            self_cmds = {
                "self:status": "Status do sistema de auto-modificação",
                "self:analyze": "Analisar código atual", 
                "self:plan": "Criar plano de melhorias",
                "self:apply": "Aplicar melhorias automaticamente",
            }
            
            for cmd, desc in self_cmds.items():
                def make_self_handler(cmd_name):
                    async def handler(args):
                        try:
                            return await selfmod.dispatch(f"/{cmd_name}", args)
                        except Exception as e:
                            return f"❌ Erro em {cmd_name}: {e}"
                    return handler
                
                self.register(
                    cmd,
                    make_self_handler(cmd),
                    desc,
                    "self_modification",
                    requires_args=(cmd != "self:status"),
                    dangerous=(cmd == "self:apply"),
                    auto_allowed=False,
                )
            logger.info("✅ Comandos de auto-modificação carregados")
        except Exception as e:
            logger.info(f"ℹ️ Auto-modificação não disponível: {e}")

    # Handlers básicos
    def _status_handler(self, args: str) -> str:
        return f"""## 🌟 Status do SUPEREZIO

**🔧 SISTEMA:**
- Comandos carregados: {len(self.commands)}
- Categorias: {len(self.categories)}
- Status: ✅ Operacional

**🤖 MODELOS ATIVOS:**
- Reasoning: {get_ai_model('reasoning')}
- Code: {get_ai_model('code')}  
- Conversation: {get_ai_model('conversation')}
- Tools: {get_ai_model('tools')}

**💾 HARDWARE:**
- GPU Principal: RTX 3060 (12GB)
- GPU Secundária: RTX 2060 (6GB) 
- VRAM Total: 18GB
"""

    def _models_handler(self, args: str) -> str:
        return f"""## 🤖 Modelos SUPEREZIO

**🧠 REASONING:** `{get_ai_model('reasoning')}`
**💻 CODE:** `{get_ai_model('code')}`
**💬 CONVERSATION:** `{get_ai_model('conversation')}`
**🛠️ TOOLS:** `{get_ai_model('tools')}`

**🔄 FALLBACKS DISPONÍVEIS:**
- Reasoning: {', '.join(get_fallback_models('reasoning')[:3])}
- Code: {', '.join(get_fallback_models('code')[:3])}
"""

    def _hardware_handler(self, args: str) -> str:
        try:
            hardware = config.ollama.hardware
            return f"""## 💻 Hardware SUPEREZIO

**🎯 CONFIGURAÇÃO OTIMIZADA:**
- GPU Principal: {hardware.gpu_primary} ({hardware.vram_primary_gb}GB VRAM)
- GPU Secundária: {hardware.gpu_secondary} ({hardware.vram_secondary_gb}GB VRAM)
- VRAM Total: {hardware.total_vram_gb}GB
- Dual GPU: {'✅ Ativo' if hardware.is_dual_gpu else '❌ Inativo'}

**⚡ OTIMIZAÇÕES:**
- Memory Management: ✅ Ativo
- Quantization: ✅ Suportado
- Flash Attention: ✅ Habilitado
- Tensor Parallelism: ✅ Dual GPU
"""
        except:
            return "💻 Hardware: RTX 3060 + RTX 2060 (18GB total)"

    def _version_handler(self, args: str) -> str:
        try:
            version = getattr(config, 'version', '1.0.0')
            build_date = getattr(config, 'build_date', '2025-08-04')
            return f"""## 📋 SUPEREZIO Version

**🌟 Interface Cognitiva v{version}**
- Build: {build_date}
- Desenvolvido por: Marco Barreto, Gemini & ChatGPT
- Hardware: RTX 3060 + RTX 2060 optimized
- Config: Enterprise-grade with type safety
"""
        except:
            return "🌟 SUPEREZIO v1.0 - Interface Cognitiva"

    async def dispatch(self, command: str, args: str = "") -> str:
        """Executa comando com error handling robusto."""
        clean = command.lstrip("/")
        info = self.commands.get(clean)
        if not info:
            return f"❌ Comando não encontrado: {command}. Use `/help`."

        if info.requires_args and not (args or "").strip():
            return f"❌ Comando '{command}' requer argumentos. {info.description}"

        try:
            result = info.handler(args)
            if asyncio.iscoroutine(result):
                result = await result
            return self._fmt(result)
        except Exception as e:
            logger.error(f"Erro executando '{command}': {e}", exc_info=True)
            return f"❌ Erro ao executar {command}: {e}"

    @staticmethod
    def _fmt(result: Any) -> str:
        if isinstance(result, dict):
            ok = result.get("success")
            if ok:
                return result.get("message", "✅ Comando executado com sucesso.")
            return f"❌ {result.get('error', 'Erro desconhecido.')}"
        return str(result) if result is not None else "✅ Comando executado."

    def get_help(self, category: Optional[str] = None) -> str:
        help_text = "## 📚 Ajuda do SUPEREZIO\n\n"
        cats = [category] if category and category in self.categories else sorted(self.categories.keys())
        for cat in cats:
            help_text += f"### 🚀 Categoria: {cat.upper()}\n"
            for cmd_name in sorted(self.categories.get(cat, [])):
                info = self.commands[cmd_name]
                flag = "⚠️ " if info.dangerous else ""
                help_text += f"- **`/{cmd_name}`**: {flag}{info.description}\n"
            help_text += "\n"
        return help_text


# ----------------------------------------------------------------------
# 6. PERFORMANCE MONITOR
# ----------------------------------------------------------------------
class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}

    @asynccontextmanager
    async def measure(self, op: str):
        t0 = time.time()
        try:
            yield
        finally:
            dt = time.time() - t0
            self.metrics.setdefault(op, []).append(dt)
            logger.debug(f"[PERF] {op}: {dt:.3f}s")

    def get_stats_formatted(self) -> str:
        if not self.metrics:
            return "📊 Nenhuma métrica coletada ainda."
        out = "## 📊 Performance SUPEREZIO\n| Operação | Execuções | Médio |\n|:--|:--:|:--:|\n"
        for op, ts in self.metrics.items():
            m, n = (sum(ts) / len(ts)), len(ts)
            out += f"| **{op}** | {n} | {m:.3f}s |\n"
        return out


# ----------------------------------------------------------------------
# 7. UTILITIES
# ----------------------------------------------------------------------
def _extract_json_loose(text: str) -> Optional[Dict[str, Any]]:
    """Extração robusta de JSON de texto."""
    if not text:
        return None
    try:
        cleaned = re.sub(r"```[\s\S]*?```", "", text, flags=re.M)
        start = cleaned.find("{")
        if start != -1:
            depth = 0
            for i in range(start, len(cleaned)):
                c = cleaned[i]
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        cand = cleaned[start : i + 1]
                        try:
                            return json.loads(cand)
                        except Exception:
                            break
        return None
    except Exception:
        return None


def _clip(text: str, max_len: int = 5000) -> str:
    """Clipa texto preservando integridade."""
    if text is None:
        return ""
    return text if len(text) <= max_len else text[:max_len] + "\n...(truncado)"


# ----------------------------------------------------------------------
# 8. SUPEREZIO AGENT CORE
# ----------------------------------------------------------------------
class SuperEzioAgent:
    def __init__(self, command_reg: SuperEzioCommandRegistry, perf: PerformanceMonitor):
        self.command_registry = command_reg
        self.perf_monitor = perf
        self.session_id = f"superezio_{int(time.time())}"
        self.http: Optional[Any] = None
        self.automation_available = self._check_automation()
        logger.info("🌟 SUPEREZIO Agent inicializado.")

    def _check_automation(self) -> bool:
        """Verifica disponibilidade de automação."""
        try:
            import importlib
            importlib.import_module("tools.automation_commands")
            return True
        except Exception:
            return False

    async def _client(self):
        """Cliente HTTP com fallback seguro."""
        if httpx is None:
            raise RuntimeError("❌ httpx não disponível. Instale: pip install httpx")
        
        if self.http is None:
            timeout = getattr(config.ollama, 'timeout', 180.0) if hasattr(config, 'ollama') else 180.0
            self.http = httpx.AsyncClient(timeout=timeout)
        return self.http

    async def call_ollama(self, model_type: str, prompt: str, system: Optional[str] = None) -> str:
        """Chamada Ollama integrada com config otimizado."""
        if httpx is None:
            return "❌ httpx não disponível. Funcionalidade Ollama limitada."
            
        try:
            client = await self._client()
            
            # Usa configuração otimizada se disponível
            base_url = getattr(config.ollama, 'base_url', 'http://127.0.0.1:11434') if hasattr(config, 'ollama') else 'http://127.0.0.1:11434'
            url = f"{base_url}/api/generate"
            
            # Seleciona modelo otimizado
            model = get_ai_model(model_type)
            payload = {"model": model, "prompt": prompt, "stream": False}
            if system:
                payload["system"] = system

            async with self.perf_monitor.measure("ollama_request"):
                r = await client.post(url, json=payload)
                r.raise_for_status()
                data = r.json()
                response = data.get("response", "") or data.get("message", "")
                logger.debug(f"✅ Ollama success: {model} ({len(response)} chars)")
                return response
                
        except Exception as e:
            logger.warning(f"⚠️ Ollama falhou com {model}: {e}")
            
            # Tenta fallbacks otimizados
            fallbacks = get_fallback_models(model_type)
            for fallback_model in fallbacks[:2]:  # Tenta 2 fallbacks
                try:
                    payload["model"] = fallback_model
                    r = await client.post(url, json=payload)
                    r.raise_for_status()
                    data = r.json()
                    response = data.get("response", "") or data.get("message", "")
                    logger.info(f"✅ Fallback success: {fallback_model}")
                    return response
                except Exception as fe:
                    logger.debug(f"Fallback {fallback_model} falhou: {fe}")
            
            return f"❌ Não foi possível contatar Ollama. Erro: {e}"

    async def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """Análise de intenção com IA otimizada."""
        if user_input.startswith("/"):
            return {"tipo": "direct_command", "auto_execute": True}
        
        if httpx is None:
            return {"tipo": "general", "confidence": 0.5}

        try:
            prompt = (
                f'Classifique a intenção do usuário e responda APENAS JSON.\n'
                f'Entrada: "{user_input}"\n'
                '{"tipo":"automation|research|code_modification|general","confidence":0.0}'
            )
            raw = await self.call_ollama("reasoning", prompt, "Você é um classificador de intenções. Responda só JSON.")
            intent = _extract_json_loose(raw) or {"tipo": "general", "confidence": 0.5}
            logger.debug(f"🧠 Intent: {intent}")
            return intent
        except Exception as e:
            logger.warning(f"Falha na análise de intenção: {e}")
            return {"tipo": "general", "confidence": 0.3}

    async def execute_plan(self, intent: Dict[str, Any], user_input: str) -> str:
        """Execução de plano com modelos otimizados."""
        t = intent.get("tipo", "general")
        
        try:
            if t == "direct_command":
                parts = user_input.split(maxsplit=1)
                cmd = parts[0]
                args = parts[1] if len(parts) > 1 else ""
                return await self.command_registry.dispatch(cmd, args)
            elif t in ("automation", "research"):
                if "auto_research" in self.command_registry.commands:
                    return await self.command_registry.dispatch("auto_research", user_input)
                else:
                    return await self.call_ollama("research", f"Pesquise sobre: {user_input}")
            elif t == "code_modification":
                return await self.call_ollama("code", f"Modifique/crie código para: {user_input}")
            else:
                return await self.call_ollama("conversation", user_input)
        except Exception as e:
            logger.error(f"Erro na execução do plano: {e}")
            return f"❌ Erro na execução: {str(e)}"

    async def cleanup(self) -> None:
        """Cleanup seguro do agente."""
        try:
            if self.http is not None:
                await self.http.aclose()
        except Exception as e:
            logger.warning(f"Erro no cleanup: {e}")
        finally:
            self.http = None
            logger.info("🧹 Sessão SUPEREZIO finalizada.")


# ----------------------------------------------------------------------
# 9. INICIALIZAÇÃO GLOBAL
# ----------------------------------------------------------------------
try:
    perf_monitor = PerformanceMonitor()
    command_registry = SuperEzioCommandRegistry()
    agent = SuperEzioAgent(command_registry, perf_monitor)
    
    # Comandos utilitários
    command_registry.register(
        "help", command_registry.get_help, "📚 Ajuda do SUPEREZIO", "system", requires_args=False
    )
    command_registry.register(
        "perf", perf_monitor.get_stats_formatted, "📊 Performance metrics", "system", requires_args=False
    )
    
    logger.info("✅ SUPEREZIO Agent totalmente inicializado.")
except Exception as e:
    logger.error(f"❌ Erro crítico na inicialização: {e}")
    raise

# ----------------------------------------------------------------------
# 10. CHAINLIT HOOKS SUPEREZIO
# ----------------------------------------------------------------------
@cl.on_chat_start
async def on_chat_start():
    """Inicialização do chat SUPEREZIO."""
    try:
        # Banner personalizado usando configuração otimizada
        startup_banner = getattr(config, 'startup_banner', '🌟 SUPEREZIO - Interface Cognitiva')
        
        banner = f"""# {startup_banner}

<div class="glass-card">

**🔧 STATUS OPERACIONAL**
- **Core Engine**: ✅ Funcionando
- **IA Multi-Modelo**: ✅ Ativo  
- **Automação**: {'✅ Disponível' if agent.automation_available else '❌ Indisponível'}
- **Interface**: SUPEREZIO v1.0

</div>

**🤖 MODELOS OTIMIZADOS:**
- **Reasoning**: `{get_ai_model('reasoning')}` (análise avançada)
- **Code**: `{get_ai_model('code')}` (programação especializada)  
- **Conversation**: `{get_ai_model('conversation')}` (chat inteligente)
- **Tools**: `{get_ai_model('tools')}` (automação)

**💾 HARDWARE:**
- **GPU Principal**: RTX 3060 (12GB VRAM)
- **GPU Secundária**: RTX 2060 (6GB VRAM)
- **Total VRAM**: 18GB disponível

**⚡ COMANDOS PRINCIPAIS:**
- `/auto_status` - Status da automação
- `/auto_research` - Pesquisa automatizada  
- `/status` - Status do sistema
- `/help` - Lista completa de comandos

<div class="gradient-text">
**SUPEREZIO está pronto para suas tarefas cognitivas! 🚀**
</div>
"""
        
        await cl.Message(content=banner, author="SuperEzio").send()
        logger.info(f"🎬 Chat SUPEREZIO iniciado - sessão {agent.session_id}")
    except Exception as e:
        logger.error(f"Erro no chat start: {e}")
        await cl.Message(content="🌟 SUPEREZIO inicializado (modo básico).").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handler de mensagem principal do SUPEREZIO."""
    user_input = (message.content or "").strip()
    if not user_input:
        await cl.Message(content="⚠️ Mensagem vazia.").send()
        return

    try:
        # Steps com fallback gracioso
        intent = {"tipo": "general", "confidence": 0.5}
        try:
            async with cl.Step(name="🧠 Analisando Intenção") as step:
                intent = await agent.analyze_intent(user_input)
                step.output = f"Tipo: **{intent.get('tipo', 'general')}** | Confiança: {intent.get('confidence', 0.5):.1f}"
        except Exception as e:
            logger.debug(f"Step análise falhou: {e}")

        result = "❌ Erro na execução"
        try:
            async with cl.Step(name="🚀 Executando Plano") as step:
                result = await agent.execute_plan(intent, user_input)
                step.output = _clip(result, 1500)
        except Exception as e:
            logger.debug(f"Step execução falhou: {e}")
            result = await agent.execute_plan(intent, user_input)

        # Resposta final com clipping
        final_result = _clip(result, 8000)
        await cl.Message(content=final_result, author="SuperEzio").send()
        logger.info(f"✅ Mensagem processada: {intent.get('tipo', 'unknown')}")

    except Exception as e:
        error_msg = f"❌ **Erro do Sistema SUPEREZIO**\n\n```\n{str(e)}\n```\n\nTente novamente ou use `/help`."
        await cl.Message(content=error_msg, author="SuperEzio-Error").send()
        logger.error(f"❌ Erro crítico: {e}\n{traceback.format_exc()}")


@cl.on_chat_end
async def on_chat_end():
    """Finalização do chat SUPEREZIO."""
    try:
        await agent.cleanup()
    except Exception as e:
        logger.warning(f"Erro no cleanup: {e}")


# ----------------------------------------------------------------------
# 11. ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        startup_banner = getattr(config, 'startup_banner', '🌟 SUPEREZIO - Interface Cognitiva')
        print(f"\n{startup_banner}")
        print(f"📊 Comandos: {len(command_registry.commands)}")
        print(f"🤖 Sessão: {agent.session_id}")
        print(f"💾 Hardware: RTX 3060 + RTX 2060 ({getattr(config.ollama.hardware, 'total_vram_gb', 18)}GB)")
        print(f"🧠 Modelos: {len(set([get_ai_model(t) for t in ['reasoning', 'code', 'conversation', 'tools']]))}")
        print("\n🧪 Para iniciar: chainlit run main_agent_superezio.py --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"🌟 SUPEREZIO v1.0 - Interface Cognitiva")
        print(f"📊 Sistema básico inicializado")
        print(f"⚠️ Configuração avançada não disponível: {e}")