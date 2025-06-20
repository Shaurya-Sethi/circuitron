"""Circuitron package.

This module also configures SKiDL so that missing KiCad 6/7/8 environment
variables don't generate noisy warnings when only KiCad 5 libraries are
required.  If ``KICAD_SYMBOL_DIR`` is set, the same path is propagated to
``KICAD6_SYMBOL_DIR``, ``KICAD7_SYMBOL_DIR`` and ``KICAD8_SYMBOL_DIR`` unless
they are already defined.  Warnings about ``KICAD_SYMBOL_DIR`` itself are left
untouched.
"""

from __future__ import annotations

import os

# Propagate KiCad 5 symbol path to later versions if available to avoid
# spurious warnings from SKiDL.
_base = os.environ.get("KICAD_SYMBOL_DIR")
if _base:
    for _var in ("KICAD6_SYMBOL_DIR", "KICAD7_SYMBOL_DIR", "KICAD8_SYMBOL_DIR"):
        os.environ.setdefault(_var, _base)

