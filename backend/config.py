from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

for env_path in (BASE_DIR / ".env", ROOT_DIR / ".env"):
    if env_path.exists():
        load_dotenv(env_path, override=False)

SLACK_TOKEN = os.getenv("SLACK_TOKEN", "").strip()
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#all-janhvi").strip()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()

# /for github
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
