import yaml
from typing import Any, Dict
from pydantic import BaseModel, Field

def load_config_safely(yaml_str: str) -> Dict[str, Any]:
    """
    使用 SafeLoader 安全加载 YAML 配置，防止任意代码执行 (ACE)。
    """
    try:
        # 核心安全点：显式使用 SafeLoader
        data = yaml.load(yaml_str, Loader=yaml.SafeLoader)
        if not isinstance(data, dict):
            raise ValueError("Invalid configuration format: expected a dictionary")
        return data
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error: {e}")
