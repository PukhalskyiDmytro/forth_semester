from pathlib import Path
import runpy


if __name__ == "__main__":
    lab3_path = Path(__file__).resolve().parents[1] / "lab3.py"
    runpy.run_path(str(lab3_path), run_name="__main__")
