import circuitron.config as cfg
cfg.setup_environment()
from circuitron.utils import validate_code_generation_results
from circuitron.models import CodeGenerationOutput


def test_validate_code_generation_results():
    out = CodeGenerationOutput(complete_skidl_code="from skidl import *\n")
    assert validate_code_generation_results(out) is True
    bad = CodeGenerationOutput(complete_skidl_code="print('hi')")
    assert validate_code_generation_results(bad) is False
