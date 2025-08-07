# -*- coding: utf-8 -*-
from pathlib import Path
import sys, json, pathlib, importlib.util, os

# === Diagnóstico de path: garante raiz no sys.path ===
ROOT = Path(__file__).resolve().parents[1]  # ...\HASHIRU_6_1
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

print("[apply_once] cwd     =", os.getcwd())
print("[apply_once] ROOT    =", ROOT)
print("[apply_once] sys.path[0] =", sys.path[0])
print("[apply_once] has utils dir? ", os.path.isdir(ROOT / "utils"))
print("[apply_once] find_spec(utils) =", importlib.util.find_spec("utils"))

# === Importa o engine ===
from utils.self_modification_engine import self_modification_engine

# === Executa pipeline simples ===
analysis = self_modification_engine.analyze_current_codebase()
plan = self_modification_engine.generate_improvement_plan(analysis, "Otimizar performance do sistema")
res = self_modification_engine.implement_improvements(plan)

art = pathlib.Path("artifacts"); art.mkdir(exist_ok=True)
(art / "last_analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
(art / "last_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
(art / "last_results.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

print("[apply_once] modified_files:", res.get("modified_files"))
