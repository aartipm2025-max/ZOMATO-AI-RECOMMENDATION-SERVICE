import pathlib
import sys
import os
import tempfile


# Ensure the src/ directory is on the Python path for imports.
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Ensure pytest and tempfile can use a writable temp directory.
# Some environments deny access to the default user temp path.
WRITABLE_TMP = PROJECT_ROOT / ".tmp"
WRITABLE_TMP.mkdir(parents=True, exist_ok=True)
os.environ["TMPDIR"] = str(WRITABLE_TMP)
os.environ["TEMP"] = str(WRITABLE_TMP)
os.environ["TMP"] = str(WRITABLE_TMP)
tempfile.tempdir = str(WRITABLE_TMP)

