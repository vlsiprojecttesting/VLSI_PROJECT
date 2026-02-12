import os
import re
import yaml


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def extract_instantiated_modules(verilog_text):
    """
    Extract instantiated module names from Verilog.
    Handles parameterized instantiations.
    """
    pattern = re.compile(
        r'^\s*(\w+)\s*(?:#\s*\(.*?\)\s*)?\w+\s*\(',
        re.MULTILINE | re.DOTALL
    )
    return set(pattern.findall(verilog_text))

def load_ip_manifest(ip_root_dir):
    """
    Load IP manifest YAML.
    """
    manifest_path = os.path.join(ip_root_dir, "ip_manifest.yaml")
    with open(manifest_path, "r") as f:
        return yaml.safe_load(f)


def build_module_index(ip_root_dir):
    """
    Build module_name -> file_path map.
    Ignores testbenches and sim-only files.
    """
    module_index = {}

    IGNORE_PATTERNS = (
        "_tb.v",
        "tb.v",
        "TB",
        "cells_sim.v"
    )

    for root, _, files in os.walk(ip_root_dir):
        for fname in files:
            if not fname.endswith(".v"):
                continue

            if any(pat in fname for pat in IGNORE_PATTERNS):
                continue

            path = os.path.join(root, fname)

            with open(path, "r") as f:
                text = f.read()

            m = re.search(r'\bmodule\s+(\w+)', text)
            if m:
                module_index[m.group(1)] = path

    return module_index


def get_ip_rtl_for_module(module_name, manifest, ip_root_dir):
    """
    If module_name is an IP top, return all RTL files of that IP.
    """
    for ip in manifest.values():
        if ip["top"] == module_name:
            return [
                os.path.join(ip_root_dir, rel_path)
                for rel_path in ip["rtl"]
            ]
    return []


# ------------------------------------------------------------
# Main API
# ------------------------------------------------------------
def generate_files_f(top_rtl_path, ip_root_dir, output_dir):
    """
    Generate files.f by resolving RTL dependencies starting from top_rtl_path.
    Ensures correct compile order (top RTL first) for PicoRV32 macros.
    """

    manifest = load_ip_manifest(ip_root_dir)
    module_index = build_module_index(ip_root_dir)

    resolved_files = set()
    visited_modules = set()

    def dfs(file_path):
        # Stop if this file is already processed
        if file_path in resolved_files:
            return

        resolved_files.add(file_path)

        with open(file_path, "r") as f:
            text = f.read()

        instantiated_modules = extract_instantiated_modules(text)

        for mod in instantiated_modules:
            if mod in visited_modules:
                continue
            visited_modules.add(mod)

            # 1) IP-level resolution (FFT, CORE, etc.)
            ip_files = get_ip_rtl_for_module(mod, manifest, ip_root_dir)
            for ip_file in ip_files:
                dfs(ip_file)

            # 2) Normal module -> file resolution
            if mod in module_index:
                dfs(module_index[mod])

    # --------------------------------------------------
    # Start dependency resolution from the TOP RTL
    # --------------------------------------------------
    dfs(top_rtl_path)

    # --------------------------------------------------
    # Enforce correct compile order:
    # picogen.v MUST come before picorv32.v
    # --------------------------------------------------
    ordered_files = []

    # 1) Top RTL FIRST (critical for PicoRV32 macros)
    ordered_files.append(top_rtl_path)

    # 2) All other resolved files
    for vf in sorted(resolved_files):
        if vf != top_rtl_path:
            ordered_files.append(vf)

    # --------------------------------------------------
    # Write files.f
    # --------------------------------------------------
    os.makedirs(output_dir, exist_ok=True)
    files_f_path = os.path.join(output_dir, "files.f")

    with open(files_f_path, "w") as f:
        for vf in ordered_files:
            f.write(vf + "\n")

    return files_f_path

