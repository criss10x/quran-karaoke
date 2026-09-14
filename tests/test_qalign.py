"""Self-check for the quran-align loader (no pytest needed: `python3 tests/test_qalign.py`)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qk import qalign


def test_sudais_prefix_tolerated():
    """Upstream Sudais file has ~150 kB of crash-log text before the JSON array."""
    rows = qalign.load("Abdurrahmaan_As-Sudais_192kbps")
    assert len(rows) == 6236, len(rows)
    assert (55, 1) in rows and rows[(55, 1)]


def test_clean_file_still_loads():
    rows = qalign.load("Alafasy_128kbps")
    assert len(rows) == 6236, len(rows)


if __name__ == "__main__":
    test_sudais_prefix_tolerated()
    test_clean_file_still_loads()
    print("ok: qalign loader")
