"""
File: models.py
Description: Data models for the Intermediate Representation (IR) of a System on Chip (SoC).
Author: Balasaraswathy B
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any

ParameterValue = Union[int, bool, str]


# ---------------- Clock & Reset ----------------

@dataclass
class ClockIR:
    name: str
    frequency_hz: int


@dataclass
class ResetIR:
    name: str
    active_low: bool


# ---------------- Addressing ----------------

@dataclass
class AddressRegionIR:
    base_addr: int
    size: int


# ---------------- Bus Interface ----------------

@dataclass
class BusIR:
    """
    Describes a bus interface, not a fabric.
    Examples:
      - picorv32_mem
      - axi_lite
    """
    type: str
    addr_width: int
    data_width: int


# ---------------- CPU ----------------

@dataclass
class CPUConfigIR:
    type: str
    parameters: Dict[str, ParameterValue]
    bus: BusIR


# ---------------- Memory ----------------

@dataclass
class MemoryRegionIR:
    name: str
    type: str
    region: AddressRegionIR
    parameters: Dict[str, ParameterValue]


# ---------------- Peripherals ----------------
@dataclass
class BusRoleIR:
    req: Dict[str, str]
    resp: Dict[str, str]

@dataclass
class PeripheralBusBindingIR:
    bus_type: str
    adapter: str
    roles: BusRoleIR

class PeripheralIR:
    def __init__(
        self,
        name,
        type,
        region,
        irq=None,
        bus_bindings=None,
        parameters=None,
        top_ports=None,
        bus_type=None,  # add this
    ):
        self.name = name
        self.type = type
        self.region = region
        self.irq = irq
        self.bus_bindings = bus_bindings or {}
        self.parameters = parameters or {}
        self.top_ports = top_ports or {}  # store top_ports
        self.bus_type = bus_type  # <<< store it for Jinja

# ---------------- Interrupts ----------------

@dataclass
class InterruptMapIR:
    width: int
    assignments: Dict[str, int]

# ---------------- Top-level SoC ----------------

@dataclass
class SoCIR:
    name: str
    clock: ClockIR
    reset: ResetIR
    cpu: CPUConfigIR
    memory: List[MemoryRegionIR]
    peripherals: List[PeripheralIR]
    interrupts: InterruptMapIR
