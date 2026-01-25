import yaml
from ir.builder import build_soc_ir
from validate.schema_validate import validate_yaml_schema
from validate.semantic_validate import validate_soc_ir

TEST_CASES = [
    ("specs/soc_invalid_schema.yaml", "schema"),
    ("specs/soc_overlap.yaml", "semantic_address"),
    ("specs/soc_irq.yaml", "semantic_irq"),
]

for path, test_type in TEST_CASES:
    try:
        data = yaml.safe_load(open(path))
        validate_yaml_schema(data, "schema/soc.schema.json")
        soc_ir = build_soc_ir(data)
        validate_soc_ir(soc_ir)
    except Exception as e:
        print(f"[{test_type}] Passed: Caught error -> {e}")
    else:
        print(f"[{test_type}] Failed: No error caught!")
