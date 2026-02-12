"""
File: main.py
Description: Main entry point for SoC specification validation and RTL generation.
Author: Balasaraswathy B Haresh Krishna G S
"""

import os
import yaml
from ir.builder import build_soc_ir
from validate.schema_validate import validate_yaml_schema
from validate.semantic_validate import validate_soc_ir
from jinja2 import Environment, FileSystemLoader
from build.filelist import generate_files_f
import json
from dataclasses import is_dataclass, asdict
from pprint import pprint


def to_serializable(obj):
    if is_dataclass(obj):
        return {k: to_serializable(v) for k, v in asdict(obj).items()}
    elif isinstance(obj, list):
        return [to_serializable(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    else:
        return obj

# -------------------------
# Paths
# -------------------------
SCHEMA_PATH = "schema/soc.schema.json"
SPEC_PATH = "specs/soc.yaml"

# Output directory for generated RTL
OUTPUT_DIR = "/home/hkremote/Desktop/tempfiles/VLSI_PROJECT-main/Automation/top_wrapper"
IP_DIR = "/home/hkremote/Desktop/tempfiles/VLSI_PROJECT-main/Automation/IP"

def load_yaml(path):
    """Loads a YAML file and returns its contents as a dictionary."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":

    # -------------------------
    # Stage 0: Load spec
    # -------------------------
    yaml_dict = load_yaml(SPEC_PATH)

    # -------------------------
    # Stage 1: Schema validation
    # -------------------------
    validate_yaml_schema(yaml_dict, SCHEMA_PATH)

    # -------------------------
    # Stage 2: Build IR
    # -------------------------
    soc_ir = build_soc_ir(
        SPEC_PATH,
        peripheral_meta_path="ir/peripheral_meta.yaml"
    )

    # -------------------------
    # Stage 3: Semantic validation
    # -------------------------
    validate_soc_ir(soc_ir)
    print("IR VALID AND READY")



def to_serializable(obj):
    # Dataclass
    if is_dataclass(obj):
        return {k: to_serializable(v) for k, v in asdict(obj).items()}

    # List / Tuple
    elif isinstance(obj, (list, tuple)):
        return [to_serializable(i) for i in obj]

    # Dict
    elif isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}

    # Regular class object (like PeripheralIR)
    elif hasattr(obj, "__dict__"):
        return {
            k: to_serializable(v)
            for k, v in obj.__dict__.items()
            if not k.startswith("_")   # ignore private/internal fields
        }

    # Primitive types
    else:
        return obj

ir_dict = to_serializable(soc_ir)

print("\n======= EXPANDED IR =======\n")
pprint(ir_dict, width=120)

# Save JSON
with open("soc_ir_dump.json", "w") as f:
    json.dump(ir_dict, f, indent=4)

# Save YAML
with open("soc_ir_dump.yaml", "w") as f:
    yaml.dump(ir_dict, f, sort_keys=False)

print("\nIR successfully saved (JSON + YAML)")






