from context_builder import build_context
from rca_engine import run_rca
from response_parser import parse_llm_response

metrics = {
    "error_count": 12
}

incident = {
    "type": "MEMORY_LEAK",
    "severity": "HIGH"
}

context = build_context(metrics, incident)

print("Sending to phi3...\n")

raw_response = run_rca(context)

print("Raw Response:\n", raw_response)

parsed = parse_llm_response(raw_response)

print("\nParsed Output:\n", parsed)