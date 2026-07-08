import os
from pathlib import Path

from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yaml

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
        "on",
    }


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def load_yaml():
    env = os.getenv("APP_ENV", "development")
    path = Path(f"config.{env}.yaml")
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


def load_dotenv():
    vals = dotenv_values(".env")
    out = {}

    if "NUM_WORKERS" in vals:
        out["workers"] = vals["NUM_WORKERS"]

    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for k, dest in mapping.items():
        if k in vals:
            out[dest] = vals[k]

    return out


def load_os():
    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    out = {}
    for env_key, cfg_key in mapping.items():
        if env_key in os.environ:
            out[cfg_key] = os.environ[env_key]
    return out


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    for layer in (
        load_yaml(),
        load_dotenv(),
        load_os(),
    ):
        for k, v in layer.items():
            config[k] = coerce(k, v)

    for item in set:
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        config[k] = coerce(k, v)

    config["api_key"] = "****"

    return config
