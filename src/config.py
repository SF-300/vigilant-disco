from pathlib import Path
import json
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    enabled: bool
    debug: bool

def load_config() -> Config:
    """Load addon configuration from config.json"""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, "r") as f:
        data = json.load(f)
    return Config(**data)

# Singleton instance
config = load_config()