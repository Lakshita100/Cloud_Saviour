from context_builder import build_context
from rca_engine import run_rca

metrics = {"error_count": 12}
incident = {"type": "MEMORY_LEAK", "severity": "HIGH"}

prompt = build_context(metrics, incident)

result = run_rca(prompt)

print(result)