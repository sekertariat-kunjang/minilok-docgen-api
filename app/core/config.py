import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variable from the minilok-docgen-api root .env file
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
PROFILE_FILE = BASE_DIR / "profile.json"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

SUMOPOD_API_KEY = os.environ.get("SUMOPOD_API_KEY") or os.environ.get("VITE_SUMOPOD_API_KEY")
SUMOPOD_BASE_URL = os.environ.get("SUMOPOD_BASE_URL", "https://ai.sumopod.com/v1")
