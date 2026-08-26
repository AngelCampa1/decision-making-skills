"""Tests for the calibration script's corpus lock.

The lock itself moved to :mod:`decision_evals.generators.audit` when the
evolution loop became a second caller, and its tests moved with it to
``tests/unit/test_audit.py``. What is left here is the wiring: that the script
imports and calls the shared lock rather than growing a second copy of it. A
second hash function is a second answer, and the two would agree right up until
one of them learned about a new field.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from decision_evals.generators import audit


def _load() -> ModuleType:
    """Import ``scripts/calibrate.py``, which is not part of the package."""
    path = Path(__file__).resolve().parents[2] / "scripts" / "calibrate.py"
    spec = importlib.util.spec_from_file_location("calibrate", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["calibrate"] = module
    spec.loader.exec_module(module)
    return module


calibrate = _load()


def test_the_script_uses_the_shared_lock() -> None:
    assert calibrate.assert_checkpoint_matches is audit.assert_checkpoint_matches
    assert calibrate.CorpusMismatchError is audit.CorpusMismatchError


def test_the_script_defines_no_fingerprint_of_its_own() -> None:
    source = (Path(__file__).resolve().parents[2] / "scripts" / "calibrate.py").read_text(
        encoding="utf-8"
    )
    assert "def corpus_fingerprint" not in source
