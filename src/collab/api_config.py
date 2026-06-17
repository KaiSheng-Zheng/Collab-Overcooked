import os
from urllib.parse import urlsplit


DEFAULT_LLM_API_BASE = "http://localhost:31234/v1"
DEFAULT_EMBEDDING_API_BASE = "http://localhost:31235/v1"
DEFAULT_API_KEY = "token-abc123"


def _first_env(names):
    for name in names:
        value = os.getenv(name)
        if value:
            return value.strip()
    return None


def _normalize_openai_base_url(value):
    if not value:
        return value

    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme in ("http", "https") and parsed.path in ("", "/"):
        return f"{value}/v1"
    return value


def get_llm_api_base(explicit=None):
    value = explicit or _first_env(("COLLAB_LLM_API_BASE", "LLM_API_BASE"))
    return _normalize_openai_base_url(value or DEFAULT_LLM_API_BASE)


def get_embedding_api_base(explicit=None):
    value = explicit or _first_env(
        ("COLLAB_EMBEDDING_API_BASE", "EMBEDDING_API_BASE")
    )
    return _normalize_openai_base_url(value or DEFAULT_EMBEDDING_API_BASE)


def read_api_keys(key_file=None):
    env_key = _first_env(("COLLAB_OPENAI_API_KEY", "OPENAI_API_KEY"))
    if env_key:
        return [key.strip() for key in env_key.splitlines() if key.strip()]

    if key_file and os.path.exists(key_file):
        with open(key_file, "r") as f:
            keys = [key.strip() for key in f.read().splitlines() if key.strip()]
        if keys:
            return keys

    return [DEFAULT_API_KEY]


def get_openai_api_key(key_file=None):
    return read_api_keys(key_file)[0]


def get_llm_api_key(key_file=None):
    return (
        _first_env(("COLLAB_LLM_API_KEY", "LLM_API_KEY"))
        or get_openai_api_key(key_file)
    )


def get_embedding_api_key(key_file=None):
    return (
        _first_env(("COLLAB_EMBEDDING_API_KEY", "EMBEDDING_API_KEY"))
        or get_openai_api_key(key_file)
    )


EMBEDDING_MODEL = _first_env(("COLLAB_EMBEDDING_MODEL", "EMBEDDING_MODEL")) or (
    "text-embedding-3-small"
)
