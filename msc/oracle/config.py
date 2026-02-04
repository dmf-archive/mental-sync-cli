from typing import Any

import yaml


def load_config_safely(yaml_str: str) -> dict[str, Any]:
    try:
        data = yaml.load(yaml_str, Loader=yaml.SafeLoader)
        if not isinstance(data, dict):
            raise ValueError("Invalid configuration format: expected a dictionary")
        return data
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error: {e}")
