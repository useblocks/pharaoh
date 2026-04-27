"""Jama CLI wiring with env-var fallbacks."""

import os

JAMA_URL_ENV = "JAMA_URL"
JAMA_USERNAME_ENV = "JAMA_USERNAME"
JAMA_PASSWORD_ENV = "JAMA_PASSWORD"
JAMA_PROJECT_ID_ENV = "JAMA_PROJECT_ID"


def resolve_credential(field: str, cli_value: str) -> str:
    if cli_value:
        return cli_value
    env_name = f"JAMA_{field.upper()}"
    return os.environ.get(env_name, "")
