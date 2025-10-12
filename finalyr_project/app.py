import yaml
import os
from string import Template
# Path to your RTL templates
RTL_DIR = "rtl_templates"

# YAML file
yaml_file = "soc_spec.yaml"

# Read YAML
with open(yaml_file, "r") as f:
    soc_spec = yaml.safe_load(f)

# ===== Check for duplicate peripheral names =====
peripheral_names = [p["name"] for p in soc_spec.get("peripherals", [])]
if len(peripheral_names) != len(set(peripheral_names)):
    duplicates = set([name for name in peripheral_names if peripheral_names.count(name) > 1])
    raise ValueError(f"Duplicate peripheral names found in YAML: {', '.join(duplicates)}")
# ================================================

# Compatibility matrix
COMPATIBILITY = {
    "picorv32": {
        "bus": "AHB",
        "compatible_peripherals": ["uart", "spi", "i2c"]
    },
    "riscv_axi_core": {
        "bus": "AXI",
        "compatible_peripherals": ["uart", "spi", "i2c"]
    }
}

soc_name = soc_spec['soc_name']
clk_freq = soc_spec['clock_freq']
core_type = soc_spec["core"]
# Extract bus type properly from YAML (since it's a list of dicts)
bus_entries = soc_spec.get("bus", [])
if not bus_entries:
    raise ValueError("No bus configuration found in YAML.")
bus_type = bus_entries[0]["type"]  # e.g., "AHB"


peripherals = [p["type"] for p in soc_spec["peripherals"]]

# === Compatibility and Bridge Check ===
if core_type not in COMPATIBILITY:
    raise ValueError(f" Unsupported core type: {core_type}")

expected_bus = COMPATIBILITY[core_type]["bus"]

if bus_type != expected_bus:
    print(f"Warning: {core_type} expects {expected_bus} but {bus_type} was provided.")

    # Suggest or auto-add a bridge adapter
    bridge = None
    if expected_bus == "AHB" and bus_type == "AXI":
        bridge = "ahb_to_axi_bridge"
    elif expected_bus == "AXI" and bus_type == "AHB":
        bridge = "axi_to_ahb_bridge"

    if bridge:
        print(f"Suggested fix: Insert '{bridge}' between {core_type} and {bus_type} bus.")
        # Optionally auto-insert:
        soc_spec["bridge"] = bridge
    else:
        raise ValueError("No known bridge available for this combination.")
    exit(1)
else:
    print("Core–Bus compatibility confirmed.")

# Check peripheral compatibility
for periph in peripherals:
    if periph not in COMPATIBILITY[core_type]["compatible_peripherals"]:
        raise ValueError(f" Peripheral '{periph}' is not compatible with {core_type}.")

print(" Peripheral compatibility confirmed.")


# Component mapping
COMPONENT_MAP = {
    'core': {
        'picorv32': [os.path.join(RTL_DIR, 'picorv32.v')]
    },
    'bus': {
        'AHB': [os.path.join(RTL_DIR, 'ahb', f) for f in os.listdir(os.path.join(RTL_DIR, 'ahb')) if f.endswith('.v')]
    },
    'peripheral': {
        'uart': [os.path.join(RTL_DIR, 'uart', 'UART_wrapper.v')]
    }
}

# Start generating top-level RTL
top_rtl = f"`timescale 1ns / 1ps\n\nmodule {soc_name}_top (\n    input clk,\n    input rst\n);\n\n"

#template fetching for top level rtl generation

for bus in soc_spec.get("bus", []):
    bus_type = bus["type"].lower()
    bus_name = bus["name"]

    if bus_type == "ahb":
        with open("rtl_skeleton/bus/ahb.vtpl") as f:
            ahb_template = Template(f.read())

        instance_code = ahb_template.substitute(
            INSTANCE_NAME=bus_name,
            CLK="clk",
            RESET="~rst",
            ADDR_WIDTH=32,
            DATA_WIDTH=32,
            TRANS_SIZE=32
        )

        top_rtl += instance_code + "\n"



for p in soc_spec['peripherals']:
    if p['type'] == 'uart':
        uart_name = p['name']
        baud = p['params']['baud_rate']
        clks_per_bit = int(clk_freq / baud) 

        # Read the UART template only if needed
        with open("rtl_skeleton/peripherals/uart.vtpl") as f:
            uart_template = Template(f.read())

        # Replace placeholders with actual values
        instance_code = uart_template.substitute(
            INSTANCE_NAME=uart_name,
            CLKS_PER_BIT=clks_per_bit,
            RESET="rst",    # top-level reset signal
            CLK="clk"       # top-level clock signal
        )

        # Append to top-level RTL
        top_rtl += instance_code + "\n"

top_rtl += "endmodule\n"


# Write top-level RTL
with open(f"{soc_name}_top.v", "w") as f:
    f.write(top_rtl)

print(f"Top-level RTL generated: {soc_name}_top.v")



"""
#///----ONLY FOR REFERENCE----///
# Start generating top-level RTL
top_rtl = f"`timescale 1ns / 1ps\n\nmodule {soc_name}_top (\n    input clk,\n    input rst\n);\n\n"

# =========================
# Instantiate Core: picorv32
# =========================
top_rtl += f"{soc_spec['core']} core0 (\n"
top_rtl += f"    .clk(clk),\n"
top_rtl += f"    .resetn(~rst) // Active-low reset\n"
top_rtl += f");\n\n"

# =========================
# Instantiate Bus: AHB
# =========================
bus_files = COMPONENT_MAP['bus'][soc_spec['bus']]
bus_wrapper_file = [f for f in bus_files if 'top_wrapper' in f][0]
bus_name = os.path.splitext(os.path.basename(bus_wrapper_file))[0]
top_rtl += f"{bus_name} bus0 (\n"
top_rtl += f"    .hclk(clk),\n"
top_rtl += f"    .sram_clk(clk),\n"
top_rtl += f"    .hresetn(~rst),\n"
# Tie other inputs to 0 or leave empty
top_rtl += f"    .stop_trans(1'b0),\n"
top_rtl += f"    .start_trans(1'b0),\n"
top_rtl += f"    .ext_haddr(32'b0),\n"
top_rtl += f"    .ext_hwdata(32'b0),\n"
top_rtl += f"    .ext_hwrite(1'b0),\n"
top_rtl += f"    .ext_hburst(3'b0),\n"
top_rtl += f"    .ext_hsize(3'b0),\n"
top_rtl += f"    .dft_en(1'b0),\n"
top_rtl += f"    .bist_en(1'b0),\n"
top_rtl += f"    .o_hrdata()\n"
top_rtl += f");\n\n"

# =========================
# Instantiate Peripherals: UART
# =========================
for p in soc_spec['peripherals']:
    if p['type'] == 'uart':
        uart_name = p['name']
        baud = p['params']['baud_rate']
        clks_per_bit = int(clk_freq / baud)
        top_rtl += f"uart #(.CLKS_PER_BIT({clks_per_bit})) {uart_name} (\n"
        top_rtl += "    .reset(rst),\n"
        top_rtl += "    .txclk(clk),\n"
        top_rtl += "    .ld_tx_data(1'b0),\n"
        top_rtl += "    .tx_data(8'b0),\n"
        top_rtl += "    .rxclk(clk),\n"
        top_rtl += "    .rx_in(1'b0),\n"
        top_rtl += "    .tx_out(),\n"
        top_rtl += "    .tx_empty(),\n"
        top_rtl += "    .rx_data(),\n"
        top_rtl += "    .rx_empty()\n"
        top_rtl += ");\n\n"

top_rtl += "endmodule\n"

"""
