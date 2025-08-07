# scripts/print_routes.py
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import __init__ as tools_init

rm = getattr(tools_init, "ROUTE_MAP", {})
keys = sorted(rm.keys())

print("ROUTE_MAP keys:", keys)

for k in ["/self", "/self:analyze", "/self:plan", "/self:apply", "/self:status"]:
    print(k, "=>", rm.get(k))
