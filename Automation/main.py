"""
File: main.py
Description: Main entry point for SoC specification validation and RTL generation.
Author: Balasaraswathy B

"""

import yaml
from ir.builder import build_soc_ir
from validate.schema_validate import validate_yaml_schema
from validate.semantic_validate import validate_soc_ir
from jinja2 import Environment, FileSystemLoader

SCHEMA_PATH = "schema/soc.schema.json"
SPEC_PATH = "specs/soc.yaml"


def load_yaml(path):
    """Loads a YAML file and returns its contents as a dictionary."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    # Load spec
    yaml_dict = load_yaml(SPEC_PATH)

    # Stage 1: Schema validation
    validate_yaml_schema(yaml_dict, SCHEMA_PATH)

    # Stage 2: Build IR
    soc_ir = build_soc_ir(
        SPEC_PATH,
        peripheral_meta_path="ir/peripheral_meta.yaml"
    )

    # Stage 3: Semantic validation
    validate_soc_ir(soc_ir)

    print("IR VALID AND READY")

    # Stage 4: RTL generation
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("top_level.v.j2")
    rtl = template.render(soc=soc_ir)

    with open(f"{soc_ir.name}.v", "w") as f:
        f.write(rtl)

    print(f"Generated top-level RTL: {soc_ir.name}.v")
