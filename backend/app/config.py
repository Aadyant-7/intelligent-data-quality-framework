"""Non-secret runtime settings shared by local and hosted modes."""

import os

from dotenv import load_dotenv


load_dotenv()


DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
