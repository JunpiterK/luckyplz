#!/usr/bin/env python3
"""Generate the lots share card with the catalog renderer."""
from pathlib import Path
from runpy import run_path


if __name__ == "__main__":
    renderer = run_path(str(Path(__file__).with_name("gen-og-games.py")))
    renderer["OUT"].mkdir(parents=True, exist_ok=True)
    renderer["build"]("lots", renderer["GAMES"]["lots"])
