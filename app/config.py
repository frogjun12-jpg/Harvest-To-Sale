import os
from pathlib import Path

from dotenv import load_dotenv


def load_app_env() -> None:
    env_file = os.getenv("APP_ENV_FILE", ".env")
    load_dotenv(Path(env_file), override=False)
