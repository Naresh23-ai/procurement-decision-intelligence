from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database.db import seed_criteria

if __name__ == '__main__':
    seed_criteria()
    print('SQLite database initialized and criteria seeded.')
