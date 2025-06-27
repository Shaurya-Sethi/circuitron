"""
Migration-compatible main script for Circuitron.

This script provides the same interface as prototype.py but uses the new modular structure.
Use this to test the new architecture while keeping prototype.py as backup.
"""

import asyncio
import sys
from circuitron.pipeline import main

if __name__ == "__main__":
    # Provide the same CLI interface as prototype.py
    asyncio.run(main())
