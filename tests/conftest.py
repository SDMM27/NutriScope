import sys
from pathlib import Path

# permet `from src.cleaning import ...` quel que soit le dossier d'où pytest est lancé
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
