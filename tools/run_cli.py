"""Invoke this project's CLI under isolated Python imports."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vesuvius_surface.__main__ import main

raise SystemExit(main())
