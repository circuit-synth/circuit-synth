from circuit_synth import *

@circuit(name="top")
def top():
    resistor = Component(symbol="Device:R", ref="R", value="10k",footprint="Resistor_SMD:R_0805_2012Metric")



def main():
    circuit = top()
    circuit.generate_kicad_project(project_name="generated_project")

if __name__ == "__main__":
    main()
    print("KiCad project generated successfully!")
    
# DEBUGGING NOTES:
# Issue: KiCad shows "R?" instead of "R1" despite correct file contents
# 
# Root cause found:
# 1. The schematic file has TWO project entries in instances: "circuit" and "generated_project"
# 2. There are TWO sheet_instances blocks with different paths
# 3. The project name "circuit" is hardcoded as default in kicad_api/schematic/instance_utils.py
# 
# The problem flow:
# 1. SchematicWriter creates a Schematic object WITHOUT project_name attribute
# 2. ComponentManager looks for project_name on schematic, doesn't find it
# 3. Defaults to "circuit" for the first instance
# 4. Later something adds another instance with "generated_project"
# 
# Solution needed:
# Add project_name to the Schematic dataclass or pass it to ComponentManager
# 
# Found the duplicate sheet_instances issue:
# 1. kicad_api/core/s_expression.py:to_schematic() adds sheet_instances at line 774
# 2. kicad/sch_gen/schematic_writer.py:_add_sheet_instances() adds another at line 1284
# 
# The instances duplicate is coming from:
# 1. ComponentManager adds instance with project="circuit" (default)
# 2. SchematicWriter._add_components() adds instance with project=self.project_name