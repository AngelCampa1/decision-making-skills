"""Helper process for `test_run_elicitation.py::TestRunLock`.

Acquires the lock on the checkpoint path given as argv[1], reports it holds
the lock, then sleeps. The test kills this process to prove a crashed holder
releases the lock, which requires a real second process: a thread in the
test's own process would share its file-handle table, and the lock this
script tests is scoped to the handle, not the process.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "run_elicitation", Path(__file__).resolve().parents[2] / "scripts" / "run_elicitation.py"
)
assert _spec is not None
assert _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

if __name__ == "__main__":
    checkpoint = Path(sys.argv[1])
    lock = _module.RunLock(checkpoint)
    lock.__enter__()
    print("locked", flush=True)
    time.sleep(60)
