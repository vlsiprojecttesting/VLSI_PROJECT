"""
File: builder.py
Description: Builds SoC Intermediate Representation (IR) from YAML spec
Author: Balasaraswathy B
"""

import yaml
from ir.models import (
    SoCIR,
    ClockIR,
    ResetIR,
    CPUConfigIR,
    BusIR,
    MemoryRegionIR,
    AddressRegionIR,
    PeripheralIR,
    PeripheralBusBindingIR,
    BusRoleIR,
    InterruptMapIR
)
"""
Function: build_soc_ir
Description: Builds the SoC IR from the given YAML specification and peripheral metadata.
@param yaml_path: Path to the SoC specification YAML file.
@param peripheral_meta_path: Path to the peripheral metadata YAML file.
@return: SoCIR object representing the SoC intermediate representation.
"""
def build_soc_ir(yaml_path: str, peripheral_meta_path: str) -> SoCIR:
    # -------------------------------------------------
    # Load input YAMLs
    # -------------------------------------------------
    with open(yaml_path, "r") as f:
        spec = yaml.safe_load(f)

    with open(peripheral_meta_path, "r") as f:
        peripheral_meta = yaml.safe_load(f)

    # -------------------------------------------------
    # Top-level sections
    # -------------------------------------------------
    soc_cfg        = spec["soc"]
    cpu_cfg        = spec["cpu"]
    bus_cfg        = spec.get("bus")
    memory_cfg     = spec.get("memory", [])
    peripheral_cfg = spec.get("peripherals", [])
    interrupt_cfg  = spec.get("interrupts", {})

    # -------------------------------------------------
    # Clock / Reset
    # -------------------------------------------------
    clock_ir = ClockIR(
        name=soc_cfg["clock"]["name"],
        frequency_hz=soc_cfg["clock"]["frequency_hz"]
    )

    reset_ir = ResetIR(
        name=soc_cfg["reset"]["name"],
        active_low=soc_cfg["reset"]["active_low"]
    )

    # -------------------------------------------------
    # Bus
    # -------------------------------------------------
    bus_ir = BusIR(
        type=bus_cfg["type"],
        addr_width=bus_cfg["addr_width"],
        data_width=bus_cfg["data_width"]
    )

    # -------------------------------------------------
    # CPU
    # -------------------------------------------------
    cpu_bus_cfg = cpu_cfg.get("bus")
    cpu_bus_ir = BusIR(
        type=cpu_bus_cfg["type"],
        addr_width=cpu_bus_cfg["addr_width"],
        data_width=cpu_bus_cfg["data_width"]
    ) if cpu_bus_cfg else bus_ir

    # Get user parameters or empty dict
    cpu_params = cpu_cfg.get("parameters", {})

    # Define defaults for parameters if not provided in YAML
    cpu_defaults = {
        "BARREL_SHIFTER": 1,
        "ENABLE_MUL": 1,
        "ENABLE_DIV": 1,
        "ENABLE_FAST_MUL": 0,
        "ENABLE_COMPRESSED": 1,
        "ENABLE_COUNTERS": 1,
        "ENABLE_IRQ_QREGS": 0,
        "MEM_WORDS": 256,
        "STACKADDR": 4*256,            # end of memory
        "PROGADDR_RESET": 0x00100000,  # 1 MB into flash
        "PROGADDR_IRQ": 0x00000000
    }

    # Merge defaults with user-specified values
    for key, val in cpu_defaults.items():
        cpu_params.setdefault(key, val)

    cpu_ir = CPUConfigIR(
        type=cpu_cfg["type"],
        parameters=cpu_params,  # now contains both defaults and user overrides
        bus=cpu_bus_ir
    )

    # -------------------------------------------------
    # Memory regions
    # -------------------------------------------------
    memory_ir = []
    for mem in memory_cfg:
        # Calculate addr_bits for template slicing
        word_width = mem.get("parameters", {}).get("word_width", 32)
        addr_bits = (word_width).bit_length() - 1
        mem["addr_bits"] = addr_bits  # store in dict for template

        memory_ir.append(
            MemoryRegionIR(
                name=mem["name"],
                type=mem["type"],
                region=AddressRegionIR(
                    base_addr=mem["base_addr"],
                    size=mem["size"]
                ),
                parameters=mem.get("parameters", {})
            )
        )

    # -------------------------------------------------
    # Peripherals
    # -------------------------------------------------
    peripheral_ir = []

    for p in peripheral_cfg:
        p_type = p["type"]
        if p_type not in peripheral_meta:
            raise ValueError(f"Peripheral '{p_type}' missing in peripheral_meta.yaml")

        # Get supported buses from metadata
        supported_buses = peripheral_meta[p_type]["supported_buses"]

        # Pick the first bus type (or you can extend to allow multiple)
        bus_type = list(supported_buses.keys())[0]
        bus_meta = supported_buses[bus_type]

        # Bus bindings
        roles = bus_meta.get("roles", {})
        adapter = bus_meta.get("adapter")
        if not adapter:
            raise ValueError(f"{p_type} on {bus_type} missing adapter")

        bus_bindings = {
            bus_type: PeripheralBusBindingIR(
                bus_type=bus_type,
                adapter=adapter,
                roles=BusRoleIR(
                    req=roles.get("req", {}),
                    resp=roles.get("resp", {})
                )
            )
        }

        # Top-level ports from metadata
        top_ports = peripheral_meta[p_type].get("top_ports", {})

        # Merge parameters from meta + spec
        spec_params = p.get("parameters", {})
        meta_params = peripheral_meta[p_type].get("parameters", {})
        merged_params = {**meta_params, **spec_params}

        # Store peripheral info in IR
        peripheral_ir.append(
            PeripheralIR(
                name=p["name"],
                type=p_type,
                region=AddressRegionIR(
                    base_addr=p["base_addr"],
                    size=p["size"]
                ),
                irq=p.get("irq"),
                bus_bindings=bus_bindings,
                parameters=merged_params,  # <-- merged
                top_ports=top_ports
            )
        )

        # Store bus_type separately for template (optional)
        peripheral_ir[-1].bus_type = bus_type

    # -------------------------------------------------
    # Interrupt map
    # -------------------------------------------------
    interrupt_ir = InterruptMapIR(
        width=interrupt_cfg.get("width", 32),
        assignments=interrupt_cfg.get("assignments", {})
    )

    # -------------------------------------------------
    # Final SoC IR
    # -------------------------------------------------
    return SoCIR(
        name=soc_cfg["name"],
        clock=clock_ir,
        reset=reset_ir,
        cpu=cpu_ir,
        memory=memory_ir,
        peripherals=peripheral_ir,
        interrupts=interrupt_ir
    )
