import tempfile, pathlib, subprocess, sys
from typing import Dict, Union

def run_skidl_script(code: str) -> Dict[str, Union[pathlib.Path, str]]:
    tmp = pathlib.Path(tempfile.mkdtemp())
    py  = tmp / "design.py"
    py.write_text(code)

    subprocess.check_call([sys.executable, str(py)], cwd=tmp)

    net = tmp / "circuit.net"
    svg = tmp / "schematic.svg"
    if not net.exists():
        raise RuntimeError("SKiDL script did not generate circuit.net")
    if not svg.exists():
        raise RuntimeError("SKiDL script did not call generate_svg()")

    return {"code": py, "netlist": net, "svg": svg}
