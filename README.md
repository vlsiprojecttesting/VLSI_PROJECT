rtl_templates/ contains the final Verilog (.v) implementations of various cores, peripherals, and bus modules.

rtl_skeleton/ contains .vtpl (Verilog template) files used for RTL generation.

tb/ includes testbench files to verify generated modules.

UART/ and vaaman-ahb-verilog/ are reference folders for studying UART and AHB implementations.

app.py serves as the main execution script, parsing the YAML file and generating the required RTL structure.
