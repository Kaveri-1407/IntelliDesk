import os
from pathlib import Path

from dotenv import load_dotenv
import openai

# Load .env from the IntelliDesk project root (two levels up from this file: utils -> project root)
project_root = Path(__file__).resolve().parents[1]
env_path = project_root / ".env"
load_dotenv(dotenv_path=str(env_path))


def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not found. Please add it to your .env file and restart the app."
        )
    return api_key


def fetch_ai_response(prompt: str) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("Please enter a prompt before clicking Run.")

    openai.api_key = get_openai_api_key()

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500,
    )

    return response.choices[0].message["content"].strip()
