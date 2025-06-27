import tempfile, pathlib, subprocess, sys, os
from typing import Dict, Union


def run_skidl_script(code: str) -> tuple[bool, str]:
    """Execute SKiDL code and return success status and output message."""
    try:
        tmp = pathlib.Path(tempfile.mkdtemp())
        py = tmp / "design.py"
        py.write_text(code)

        env = os.environ.copy()
        base = env.get("KICAD_SYMBOL_DIR")
        if base:
            for var in ("KICAD6_SYMBOL_DIR", "KICAD7_SYMBOL_DIR", "KICAD8_SYMBOL_DIR"):
                env.setdefault(var, base)

        result = subprocess.run(
            [sys.executable, str(py)], 
            cwd=tmp, 
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )

        net = tmp / "circuit.net"
        svg = tmp / "schematic.svg"
        
        if result.returncode != 0:
            return False, f"Script execution failed:\n{result.stderr}"
        
        if not net.exists():
            return False, "SKiDL script did not generate circuit.net"
        
        if not svg.exists():
            return False, "SKiDL script did not call generate_svg()"

        return True, f"Generated files: {net}, {svg}\nOutput: {result.stdout}"
        
    except subprocess.TimeoutExpired:
        return False, "Script execution timed out"
    except Exception as e:
        return False, f"Execution error: {str(e)}"
