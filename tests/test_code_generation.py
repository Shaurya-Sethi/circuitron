import circuitron.config as cfg
from circuitron.models import CodeGenerationOutput
from circuitron.utils import validate_code_generation_results


def test_validate_code_generation_results() -> None:
    cfg.setup_environment()
    out = CodeGenerationOutput(complete_skidl_code="from skidl import *\n")
    assert validate_code_generation_results(out) is True
    bad = CodeGenerationOutput(complete_skidl_code="print('hi')")
    assert validate_code_generation_results(bad) is False
