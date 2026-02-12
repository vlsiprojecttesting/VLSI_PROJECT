"""
File: main.py
Description: Main entry point for SoC specification validation,
             IR generation, memory map generation, and RTL preparation.
Author: Balasaraswathy B | Haresh Krishna G S
"""

import os
import json
import yaml
from pprint import pprint
from dataclasses import is_dataclass, asdict

from ir.builder import build_soc_ir
from validate.schema_validate import validate_yaml_schema
from validate.semantic_validate import validate_soc_ir
from build.filelist import generate_files_f


# ==========================================================
# Utility: Recursive Serializer
# ==========================================================

def to_serializable(obj):
    if is_dataclass(obj):
        return {k: to_serializable(v) for k, v in asdict(obj).items()}
    elif isinstance(obj, (list, tuple)):
        return [to_serializable(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    elif hasattr(obj, "__dict__"):
        return {
            k: to_serializable(v)
            for k, v in obj.__dict__.items()
            if not k.startswith("_")
        }
    else:
        return obj


# ==========================================================
# Utility: Memory Map Generator
# ==========================================================

def generate_memory_map(ir_dict):

    entries = []

    # ---- Memory ----
    for mem in ir_dict.get("memory", []):
        base = mem["region"]["base_addr"]
        size = mem["region"]["size"]
        end  = base + size - 1

        entries.append({
            "name": mem["name"],
            "type": "memory",
            "base": base,
            "end": end,
            "size": size
        })

    # ---- Peripherals ----
    for periph in ir_dict.get("peripherals", []):
        base = periph["region"]["base_addr"]
        size = periph["region"]["size"]
        end  = base + size - 1

        entries.append({
            "name": periph["name"],
            "type": "peripheral",
            "base": base,
            "end": end,
            "size": size
        })

    # ---- Sort by address ----
    entries.sort(key=lambda x: x["base"])

    # ---- Overlap Check ----
    for i in range(len(entries) - 1):
        if entries[i]["end"] >= entries[i + 1]["base"]:
            print(f"⚠ WARNING: Address overlap between "
                  f"{entries[i]['name']} and {entries[i+1]['name']}")

    # ---- Print Table ----
    print("\n================ MEMORY MAP ================\n")
    print(f"{'Name':<15} {'Type':<12} {'Base Address':<15} "
          f"{'End Address':<15} {'Size (Bytes)':<12}")
    print("-" * 75)

    for e in entries:
        print(f"{e['name']:<15} "
              f"{e['type']:<12} "
              f"0x{e['base']:08X}     "
              f"0x{e['end']:08X}     "
              f"{e['size']:<12}")

    print("\n============================================\n")

    return entries


# ==========================================================
# Paths
# ==========================================================

SCHEMA_PATH = "schema/soc.schema.json"
SPEC_PATH   = "specs/soc.yaml"

OUTPUT_DIR  = "IR_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================================================
# YAML Loader
# ==========================================================

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


# ==========================================================
# MAIN PIPELINE
# ==========================================================

if __name__ == "__main__":

    print("\n===== SoC Automation Flow Started =====\n")

    # ------------------------------------------------------
    # Stage 1: Schema Validation
    # ------------------------------------------------------
    yaml_dict = load_yaml(SPEC_PATH)

    # ------------------------------------------------------
    # 
    # ------------------------------------------------------
    validate_yaml_schema(yaml_dict, SCHEMA_PATH)

    # ------------------------------------------------------
    # Stage 2: Build IR
    # ------------------------------------------------------
    soc_ir = build_soc_ir(
        SPEC_PATH,
        peripheral_meta_path="ir/peripheral_meta.yaml"
    )

    # ------------------------------------------------------
    # Stage 3: Semantic Validation
    # ------------------------------------------------------
    validate_soc_ir(soc_ir)

    print("✔ IR VALID AND READY")

    # ------------------------------------------------------
    # Serialize IR
    # ------------------------------------------------------
    ir_dict = to_serializable(soc_ir)

    print("\n======= EXPANDED IR =======\n")
    pprint(ir_dict, width=120)

    json_path = os.path.join(OUTPUT_DIR, "soc_ir_dump.json")
    yaml_path = os.path.join(OUTPUT_DIR, "soc_ir_dump.yaml")

    with open(json_path, "w") as f:
        json.dump(ir_dict, f, indent=4)

    with open(yaml_path, "w") as f:
        yaml.dump(ir_dict, f, sort_keys=False)

    print(f"\n✔ IR saved to {OUTPUT_DIR}/")

    # ------------------------------------------------------
    # Generate Memory Map
    # ------------------------------------------------------
    memory_map = generate_memory_map(ir_dict)

    memmap_path = os.path.join(OUTPUT_DIR, "memory_map.json")
    with open(memmap_path, "w") as f:
        json.dump(memory_map, f, indent=4)

    print(f"✔ File Generation is succesful and IR output are stored at IR_output as both JSON and YAML file")

    print(f"✔ Memory map saved to {memmap_path}")

    print("\n===== SoC Flow Completed Successfully upto IR Representation=====\n")

