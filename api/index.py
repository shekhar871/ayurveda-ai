import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("APP_MODE", "lite")
os.environ.setdefault("EMBEDDING_DIM", "384")
os.environ.setdefault("PYTHONPATH", str(ROOT))

from mangum import Mangum  # noqa: E402

from src.main import app  # noqa: E402

handler = Mangum(app, lifespan="auto")
