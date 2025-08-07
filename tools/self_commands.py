# -*- coding: utf-8 -*-
"""
tools/selfmod.py
Comandos de auto-modificação do HASHIRU 6.1:
- /self:analyze
- /self:plan <objetivo>
- /self:apply <objetivo>
- /self:status
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ==============================
# Imports tolerantes
# ==============================
try:
    # Engine de auto-modificação (opcional)
    from utils.self_modification_engine import self_modification_engine
except Exception:
    self_modification_engine = None  # type: ignore[assignment]

try:
    # Configuração autônoma
    from autonomous_config import autonomous_config, is_self_modification_enabled  # type: ignore
    _CONFIG_OK = True
except Exception:
    autonomous_config = None  # type: ignore[assignment]
    def is_self_modification_enabled() -> bool:  # fallback
        return False
    _CONFIG_OK = False


# ==============================
# Constantes e helpers
# ==============================
ARTIFACTS_DIR = Path("artifacts")


def _ensure_artifacts_dir() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _build_analysis_summary(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constrói um resumo compatível, caso o engine não gere "summary".
    Espera analysis['files'] com metadados.
    """
    files: List[Dict[str, Any]] = analysis.get("files", []) or []
    total_files = len(files)
    total_lines = 0

    # Thresholds
    COMPLEXITY_THRESHOLD = 20
    PARAMS_THRESHOLD = 6

    high_complexity_files: List[Dict[str, Any]] = []
    large_functions: List[Dict[str, Any]] = []
    improvement_opportunities: List[Dict[str, Any]] = []

    for f in files:
        if f.get("error"):
            continue

        lines = int(f.get("lines", 0) or 0)
        total_lines += lines

        complexity = int(f.get("complexity", 0) or 0)
        if complexity > COMPLEXITY_THRESHOLD:
            high_complexity_files.append(
                {"file": f.get("path", ""), "complexity": complexity}
            )
            improvement_opportunities.append(
                {
                    "type": "complexity_reduction",
                    "priority": "high",
                    "description": f"Complexidade {complexity} em {f.get('path','')}",
                    "file": f.get("path", ""),
                    "action": "refactor_complex_functions",
                }
            )

        for func in f.get("functions", []) or []:
            args_qtd = int(func.get("args", 0) or 0)
            if args_qtd > PARAMS_THRESHOLD:
                large_functions.append(
                    {
                        "file": f.get("path", ""),
                        "function": func.get("name", ""),
                        "args": args_qtd,
                    }
                )
                improvement_opportunities.append(
                    {
                        "type": "parameter_optimization",
                        "priority": "medium",
                        "description": f"Função {func.get('name','')} com {args_qtd} parâmetros em {f.get('path','')}",
                        "file": f.get("path", ""),
                        "function": func.get("name", ""),
                        "action": "reduce_parameters",
                    }
                )

    high_complexity_files.sort(key=lambda x: x.get("complexity", 0) or 0, reverse=True)
    large_functions.sort(key=lambda x: x.get("args", 0) or 0, reverse=True)

    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "high_complexity_files": high_complexity_files,
        "large_functions": large_functions,
        "improvement_opportunities": improvement_opportunities,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ==============================
# Handlers /self:
# ==============================
async def handle_self_analyze(args: str, block: str) -> str:
    """
    /self:analyze
    Analisa o código atual e identifica oportunidades de melhoria.
    """
    if self_modification_engine is None:
        return "❌ Motor de auto-modificação não disponível. Verifique `utils/self_modification_engine.py`."

    if _CONFIG_OK and not is_self_modification_enabled():
        return "❌ Auto-modificação desabilitada na configuração."

    try:
        analysis = self_modification_engine.analyze_current_codebase()

        # Garantir summary
        summary = analysis.get("summary")
        if not summary:
            summary = _build_analysis_summary(analysis)
            analysis["summary"] = summary

        # Persistir
        _ensure_artifacts_dir()
        with open(ARTIFACTS_DIR / "last_analysis.json", "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        # Construir resposta
        resp_lines: List[str] = []
        resp_lines.append("🔍 **ANÁLISE DO CÓDIGO CONCLUÍDA**\n")
        resp_lines.append("📊 **Resumo Geral:**")
        resp_lines.append(f"- **Arquivos analisados:** {summary['total_files']}")
        resp_lines.append(f"- **Total de linhas:** {summary['total_lines']:,}")
        resp_lines.append(f"- **Arquivos complexos:** {len(summary['high_complexity_files'])}")
        resp_lines.append(f"- **Funções com muitos parâmetros:** {len(summary['large_functions'])}")
        resp_lines.append(f"- **Oportunidades de melhoria:** {len(summary['improvement_opportunities'])}")

        # Complexidade alta
        resp_lines.append("\n🔥 **Arquivos com Alta Complexidade:**")
        for complex_file in summary["high_complexity_files"][:5]:
            resp_lines.append(f"- **{complex_file['file']}** (complexidade: {complex_file['complexity']})")
        extra_c = len(summary["high_complexity_files"]) - 5
        if extra_c > 0:
            resp_lines.append(f"- ... e mais {extra_c} arquivos")

        # Muitas params
        resp_lines.append("\n⚠️ **Funções com Muitos Parâmetros:**")
        for large_func in summary["large_functions"][:5]:
            resp_lines.append(f"- **{large_func['function']}** em {large_func['file']} ({large_func['args']} parâmetros)")
        extra_f = len(summary["large_functions"]) - 5
        if extra_f > 0:
            resp_lines.append(f"- ... e mais {extra_f} funções")

        # Oportunidades
        resp_lines.append("\n💡 **Principais Oportunidades:**")
        for opportunity in summary["improvement_opportunities"][:5]:
            pr = opportunity.get("priority", "medium")
            icon = "🔴" if pr == "high" else "🟡" if pr == "medium" else "🟢"
            resp_lines.append(f"{icon} **{opportunity['type']}:** {opportunity['description']}")
        extra_o = len(summary["improvement_opportunities"]) - 5
        if extra_o > 0:
            resp_lines.append(f"- ... e mais {extra_o} oportunidades")

        # Artifacts e próximos passos
        resp_lines.append("\n📁 **Artifacts Salvos:**")
        resp_lines.append("- `artifacts/last_analysis.json` - Análise completa")
        resp_lines.append(f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        resp_lines.append("\n💡 **Próximos Passos:**")
        resp_lines.append("- Use `/self:plan <objetivo>` para criar plano de melhorias")
        resp_lines.append("- Use `/self:apply <objetivo>` para aplicar melhorias automaticamente")

        return "\n".join(resp_lines)

    except Exception as exc:
        return f"💥 **Erro na análise:** {exc}"


async def handle_self_plan(args: str, block: str) -> str:
    """
    /self:plan <objetivo>
    Cria um plano de melhorias baseado no objetivo especificado.
    """
    if self_modification_engine is None:
        return "❌ Motor de auto-modificação não disponível."

    objective = (args or "").strip()
    if not objective:
        return (
            "❌ **Objetivo não especificado.**\n\n"
            "**Uso:** `/self:plan <objetivo>`\n\n"
            "**Exemplos:**\n"
            "- `/self:plan Otimizar performance do sistema`\n"
            "- `/self:plan Reduzir complexidade do código`\n"
            "- `/self:plan Adicionar cache inteligente`\n"
            "- `/self:plan Corrigir bugs identificados`\n"
            "- `/self:plan Melhorar documentação`"
        )

    try:
        # Reutiliza análise se existir
        try:
            with open(ARTIFACTS_DIR / "last_analysis.json", "r", encoding="utf-8") as f:
                analysis = json.load(f)
        except FileNotFoundError:
            analysis = self_modification_engine.analyze_current_codebase()
            _ensure_artifacts_dir()
            with open(ARTIFACTS_DIR / "last_analysis.json", "w", encoding="utf-8") as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)

        plan = self_modification_engine.generate_improvement_plan(analysis, objective)
        plan.setdefault("user_goal", objective)
        plan.setdefault("priority", "medium")
        plan.setdefault("estimated_impact", "moderate")

        # Estratégia de backup
        backup_enabled = True
        try:
            if _CONFIG_OK:
                backup_enabled = bool(autonomous_config.SELF_MODIFICATION.get("auto_backup", True))
        except Exception:
            backup_enabled = True
        plan["backup_strategy"] = "auto_backup_on_write" if backup_enabled else "no_auto_backup"

        _ensure_artifacts_dir()
        with open(ARTIFACTS_DIR / "last_plan.json", "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)

        # Resposta
        lines = []
        lines.append("📋 **PLANO DE MELHORIAS CRIADO**\n")
        lines.append(f"🎯 **Objetivo:** {objective}")
        lines.append(f"⏰ **Criado em:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"📊 **Prioridade:** {plan.get('priority','medium')}")
        lines.append(f"💪 **Impacto Estimado:** {plan.get('estimated_impact','moderate')}")

        improvements = plan.get("improvements", []) or []
        lines.append(f"\n🔧 **Melhorias Planejadas ({len(improvements)}):**")
        for i, imp in enumerate(improvements[:10], 1):
            pr = imp.get("priority", "medium")
            icon_p = "🔴" if pr == "high" else "🟡" if pr == "medium" else "🟢"
            eff = imp.get("estimated_effort", "medium")
            icon_e = "🔥" if eff == "high" else "⚡" if eff == "medium" else "💨"
            desc = imp.get("description", imp.get("type", "improvement"))
            lines.append(f"{i}. {icon_p}{icon_e} **{imp.get('type','improvement').replace('_',' ').title()}**")
            lines.append(f"   - {desc}")
            if imp.get("file"):
                lines.append(f"   - Arquivo: `{imp['file']}`")
            if imp.get("function"):
                lines.append(f"   - Função: `{imp['function']}`")

        extra = len(improvements) - 10
        if extra > 0:
            lines.append(f"... e mais {extra} melhorias")

        lines.append(f"\n💾 **Estratégia de Backup:** {plan['backup_strategy']}")
        lines.append("📁 **Plano salvo em:** `artifacts/last_plan.json`")
        lines.append("\n🚀 **Próximos Passos:**")
        lines.append(f"- Use `/self:apply {objective}` para executar automaticamente")
        lines.append("- Ou execute melhorias individuais conforme necessário")

        return "\n".join(lines)

    except Exception as exc:
        return f"💥 **Erro ao criar plano:** {exc}"


async def handle_self_apply(args: str, block: str) -> str:
    """
    /self:apply <objetivo>
    Aplica automaticamente as melhorias do plano especificado.
    """
    if self_modification_engine is None:
        return "❌ Motor de auto-modificação não disponível."

    if _CONFIG_OK and not is_self_modification_enabled():
        return "❌ Auto-modificação desabilitada na configuração."

    objective = (args or "").strip()
    if not objective:
        return (
            "❌ **Objetivo não especificado.**\n\n"
            "**Uso:** `/self:apply <objetivo>`\n\n"
            "⚠️ **ATENÇÃO:** Este comando modifica arquivos automaticamente!\n"
            "Certifique-se de ter backups adequados."
        )

    try:
        # Carrega plano existente; se não bater o objetivo, cria novo
        try:
            with open(ARTIFACTS_DIR / "last_plan.json", "r", encoding="utf-8") as f:
                plan = json.load(f)
            if str(plan.get("user_goal", "")).lower() != objective.lower():
                raise FileNotFoundError
        except FileNotFoundError:
            try:
                with open(ARTIFACTS_DIR / "last_analysis.json", "r", encoding="utf-8") as f:
                    analysis = json.load(f)
            except FileNotFoundError:
                analysis = self_modification_engine.analyze_current_codebase()
                _ensure_artifacts_dir()
                with open(ARTIFACTS_DIR / "last_analysis.json", "w", encoding="utf-8") as f:
                    json.dump(analysis, f, ensure_ascii=False, indent=2)

            plan = self_modification_engine.generate_improvement_plan(analysis, objective)
            plan.setdefault("user_goal", objective)
            plan.setdefault("priority", "medium")
            plan.setdefault("estimated_impact", "moderate")
            _ensure_artifacts_dir()
            with open(ARTIFACTS_DIR / "last_plan.json", "w", encoding="utf-8") as f:
                json.dump(plan, f, ensure_ascii=False, indent=2)

        results = self_modification_engine.implement_improvements(plan)
        results.setdefault("implemented", [])
        results.setdefault("failed", [])
        results.setdefault("created_files", [])
        results.setdefault("modified_files", [])
        results.setdefault("backups_created", [])

        _ensure_artifacts_dir()
        with open(ARTIFACTS_DIR / "last_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Monta resposta
        lines = []
        lines.append("🚀 **MELHORIAS APLICADAS AUTOMATICAMENTE**\n")
        lines.append(f"🎯 **Objetivo:** {objective}")
        lines.append(f"⏰ **Executado em:** {time.strftime('%Y-%m-%d %H:%M:%S')}")

        impl = results["implemented"]
        lines.append(f"\n✅ **Melhorias Implementadas ({len(impl)}):**")
        for imp in impl:
            desc = imp.get("description", imp.get("type", "improvement"))
            lines.append(f"- ✅ **{imp.get('type','improvement').replace('_',' ').title()}:** {desc}")

        failed = results["failed"]
        if failed:
            lines.append(f"\n❌ **Melhorias que Falharam ({len(failed)}):**")
            for f in failed:
                imp = f.get("improvement", {})
                lines.append(f"- ❌ **{imp.get('type','improvement')}:** {f.get('error','erro desconhecido')}")

        lines.append(f"\n📁 **Arquivos Criados ({len(results['created_files'])}):**")
        for c in results["created_files"]:
            lines.append(f"- 🆕 `{c}`")

        lines.append(f"\n📝 **Arquivos Modificados ({len(results['modified_files'])}):**")
        for m in results["modified_files"]:
            lines.append(f"- ✏️ `{m}`")

        backups_ok = [b for b in results["backups_created"] if b]
        lines.append(f"\n💾 **Backups Criados ({len(backups_ok)}):**")
        for b in backups_ok:
            lines.append(f"- 🗂️ `{b}`")

        lines.append("\n📊 **Resumo:**")
        lines.append(f"- ✅ Sucessos: {len(results['implemented'])}")
        lines.append(f"- ❌ Falhas: {len(results['failed'])}")
        lines.append(f"- 🆕 Arquivos criados: {len(results['created_files'])}")
        lines.append(f"- ✏️ Arquivos modificados: {len(results['modified_files'])}")
        lines.append(f"- 💾 Backups: {len(backups_ok)}")

        lines.append("\n📁 **Resultados salvos em:** `artifacts/last_results.json`")
        lines.append("\n🎉 **Sistema auto-melhorado com sucesso!**")

        return "\n".join(lines)

    except Exception as exc:
        return f"💥 **Erro na aplicação:** {exc}"


async def handle_self_status(args: str, block: str) -> str:
    """
    /self:status
    Mostra status do sistema de auto-modificação.
    """
    lines = []
    lines.append("🔧 **STATUS DO SISTEMA DE AUTO-MODIFICAÇÃO**\n")

    # Componentes
    engine_ok = self_modification_engine is not None
    config_ok = _CONFIG_OK
    enabled = False
    try:
        enabled = bool(is_self_modification_enabled())
    except Exception:
        enabled = False

    lines.append("⚙️ **Componentes:**")
    lines.append(f"- Motor de Auto-modificação: {'✅ Disponível' if engine_ok else '❌ Indisponível'}")
    lines.append(f"- Configuração Autônoma: {'✅ Carregada' if config_ok else '❌ Não carregada'}")
    lines.append(f"- Auto-modificação: {'✅ Habilitada' if enabled else '❌ Desabilitada'}")

    # Artifacts
    lines.append("\n📁 **Artifacts Disponíveis:**")
    artifacts = ["last_analysis.json", "last_plan.json", "last_results.json"]
    if ARTIFACTS_DIR.exists():
        for name in artifacts:
            p = ARTIFACTS_DIR / name
            if p.exists():
                mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime))
                lines.append(f"- ✅ `{name}` (modificado: {mtime})")
            else:
                lines.append(f"- ❌ `{name}` (não encontrado)")
    else:
        lines.append("- ❌ Diretório artifacts não encontrado")

    # Métricas (best-effort)
    if engine_ok:
        try:
            report = self_modification_engine.create_performance_report()
            total_mods = report.get("total_modifications", 0)
            success_rate = float(report.get("success_rate", 0.0))
            perf_impact = report.get("performance_impact", "unknown")
            config_integration = bool(report.get("config_integration", False))

            lines.append("\n📊 **Métricas de Performance:**")
            lines.append(f"- Total de modificações: {total_mods}")
            lines.append(f"- Taxa de sucesso: {success_rate:.1%}")
            lines.append(f"- Impacto na performance: {perf_impact}")
            lines.append(f"- Integração de config: {'✅' if config_integration else '❌'}")
        except Exception as exc:
            lines.append(f"\n⚠️ **Erro ao obter métricas:** {exc}")

    # Ajuda
    lines.append("\n🔧 **Comandos Disponíveis:**")
    lines.append("- `/self:analyze` - Analisar código atual")
    lines.append("- `/self:plan <objetivo>` - Criar plano de melhorias")
    lines.append("- `/self:apply <objetivo>` - Aplicar melhorias automaticamente")
    lines.append("- `/self:status` - Este status")
    lines.append("\n💡 **Exemplo de Uso:**")
    lines.append("/self:analyze")
    lines.append("/self:plan Otimizar performance")
    lines.append("/self:apply Otimizar performance")
    lines.append("/self:status")

    return "\n".join(lines)


__all__ = [
    "handle_self_analyze",
    "handle_self_plan",
    "handle_self_apply",
    "handle_self_status",
]
