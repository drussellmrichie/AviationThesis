import subprocess
import os
import sys

if __name__ == "__main__":
    subprocess.run([
    sys.executable, "-m", "streamlit", "run",
    # "streamlit", "run",
    "Project_Code/Python3Model/src/gui.py"
])