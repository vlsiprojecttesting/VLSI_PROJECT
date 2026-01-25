"""
File: semantic_validate.py
Description: Semantic validation of the SOC Intermediate Representation (IR).
Author: Balasaraswathy B
Date: 23/01/2026
"""
from ir.models import *
"""
Function:check_address_overlap
Description:Checks for overlapping memory regions in the SOC IR.
@param regions:List of memory regions and peripherals.
@return:None. Raises ValueError if overlap is detected.
"""
def check_address_overlap(regions: list) -> None:
    used = []
    for r in regions:
        start = r.region.base_addr
        end = start + r.region.size - 1
        for s, e in used:
            if not (end < s or start > e):
                raise ValueError(f"Address overlap detected: {r.name}")
        used.append((start, end))
"""
Function:check_irq_validity
Description:Checks that all IRQs used by peripherals are defined in the SOC IR.
@param ir:SOC Intermediate Representation.
@return:None. Raises ValueError if undefined IRQ is used.
"""
def check_irq_validity(ir: SoCIR) -> None:
    irq_set = set(ir.interrupts.assignments.keys())
    for p in ir.peripherals:
        if p.irq and p.irq not in irq_set:
            raise ValueError(f"Peripheral {p.name} uses undefined IRQ {p.irq}")
"""
Function:validate_soc_ir
Description:Validates the SOC Intermediate Representation for address overlaps and IRQ validity.
@param ir:SOC Intermediate Representation.
@return:None. Raises ValueError if any validation fails.
"""
def validate_soc_ir(ir: SoCIR) -> None:
    check_address_overlap(ir.memory + ir.peripherals)
    check_irq_validity(ir)
