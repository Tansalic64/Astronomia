#!/usr/bin/env python
"""Lanzador de conveniencia: permite ejecutar `python run.py` desde la raíz
del proyecto sin tener que instalar el paquete ni usar `python -m astronomia`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from astronomia.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
