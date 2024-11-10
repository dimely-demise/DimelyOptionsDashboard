import os
import glob
import subprocess
import re

# Directory containing the .ui files
UI_DIRECTORY = "./src/ui"

# Function to compile .ui files to .py files
def compile_ui_files():
    ui_files = glob.glob(os.path.join(UI_DIRECTORY, "*.ui"))
    for ui_file in ui_files:
        output_file = ui_file.replace(".ui", "_ui.py")
        subprocess.run(['pyuic5', ui_file, '-o', output_file])
        add_type_hints(output_file)
        print(f"Compiled and annotated {ui_file} to {output_file}")

# Function to add type hints by modifying the .py file directly
def add_type_hints(py_file: str):
    with open(py_file, 'r') as file:
        lines = file.readlines()

    annotated_lines = []
    widget_pattern = re.compile(r"(self\.\w+)\s*=\s*(QtWidgets\.\w+)\(")

    for line in lines:
        match = widget_pattern.search(line)
        if match:
            variable_name = match.group(1)         # e.g., self.centralwidget
            widget_type = match.group(2)           # e.g., QtWidgets.QWidget

            # Add the type annotation on a new line before the assignment
            annotated_lines.append(f"        {variable_name}: {widget_type}\n")  # Proper indentation
            annotated_lines.append(line)  # Keep the original assignment line
        else:
            annotated_lines.append(line)

    with open(py_file, 'w') as file:
        file.writelines(annotated_lines)

if __name__ == '__main__':
    compile_ui_files()
