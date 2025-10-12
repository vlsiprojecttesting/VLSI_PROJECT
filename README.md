# SoCForge

## 📁 Project Structure

```
├── rtl_templates/         # Contains .v files of cores, peripherals, and buses
├── rtl_skeleton/          # Contains .vtpl (Verilog template) files for cores, peripherals, and buses
├── tb/                    # Contains testbenches (currently for testing purposes)
├── UART/                  # Reference UART implementation (cloned)
├── vaaman-ahb-verilog/    # Reference AHB implementation (cloned)
├── app.py                 # Main Python script for overall execution
└── soc_spec.yaml          # YAML file with SoC specifications
```

---

## ⚙️ Description



- `rtl_templates/` contains the final Verilog (`.v`) implementations of various cores, peripherals, and bus modules.  
- `rtl_skeleton/` contains `.vtpl` (Verilog template) files used for RTL generation.  
- `tb/` includes testbench files to verify generated modules.  
- `UART/` and `vaaman-ahb-verilog/` are **reference folders** for studying UART and AHB implementations.  
- `app.py` serves as the **main execution script**, parsing the YAML file and generating the required RTL structure.

---

## 🧩 Usage

1. Prepare your **YAML specification file** (`soc_spec.yaml`) with desired cores, peripherals, and bus configurations.  
2. Open a terminal or command prompt in the project directory.  
3. Run the following command:

   ```bash
   python app.py
   ```

4. The script will read the YAML file and generate the SoC RTL design automatically.

---

## 💻 Requirements

- **Python:** 3.8 or above  
- **Dependencies:**  
  Install the required Python modules using:

  ```bash
  pip install pyyaml
  ```

- Ensure all directories (`rtl_templates`, `rtl_skeleton`, `tb`) are present in the same root folder.

---

## 🧠 Notes

- Testbench files (`tb/`) are for basic functional testing.  
- You can easily add new cores or peripherals by:  
  1. Creating a new `.vtpl` template in `rtl_skeleton/`.  
  2. Defining the new component in `soc_spec.yaml`.  

