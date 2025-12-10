"""
LLM 模型客户端工厂
支持多种大模型的统一接口封装
"""
import os
from typing import Dict, Any, Optional, Union, List, overload
from dataclasses import dataclass, field
from autogen_ext.models.openai import OpenAIChatCompletionClient
from loguru import logger


@dataclass
class ModelConfig:
    """模型配置类"""
    model: str
    api_key_env: str  # 环境变量名
    base_url: str
    vision: bool = False
    function_calling: bool = True
    json_output: bool = True
    family: str = "unknown"


# 模型配置注册表
MODELS: Dict[str, ModelConfig] = {
    "deepseek": ModelConfig(
        model="deepseek-chat",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1",
    ),
    "qwenvl": ModelConfig(
        model="qwen-vl-plus",
        api_key_env="QWENVL_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        vision=True,
    ),
    "openai": ModelConfig(
        model="gpt-4",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    ),
    "gpt4v": ModelConfig(
        model="gpt-4-vision-preview",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        vision=True,
    ),
    "moonshot": ModelConfig(
        model="moonshot-v1-8k",
        api_key_env="MOONSHOT_API_KEY",
        base_url="https://api.moonshot.cn/v1",
    ),
    "zhipu": ModelConfig(
        model="glm-4",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
    ),
    "doubao": ModelConfig(
        model="doubao-pro-32k",
        api_key_env="DOUBAO_API_KEY",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    ),
}


def _create_client(
    config: ModelConfig,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> OpenAIChatCompletionClient:
    """内部方法：创建单个客户端"""
    final_api_key = api_key or os.getenv(config.api_key_env)
    if not final_api_key:
        raise ValueError(f"缺少 API Key，请设置环境变量 {config.api_key_env}")
    
    return OpenAIChatCompletionClient(
        model=model or config.model,
        api_key=final_api_key,
        base_url=base_url or config.base_url,
        model_info={
            "vision": config.vision,
            "function_calling": config.function_calling,
            "json_output": config.json_output,
            "family": config.family,
        },
    )


@overload
def get_model(*types: str, **kwargs) -> OpenAIChatCompletionClient: ...
@overload
def get_model(*types: str, **kwargs) -> List[OpenAIChatCompletionClient]: ...


def get_model(
    *types: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Union[OpenAIChatCompletionClient, List[OpenAIChatCompletionClient]]:
    """
    获取模型客户端（支持单个或多个）
    
    Args:
        *types: 模型类型，支持传入多个
        model: 覆盖默认模型名
        api_key: 覆盖默认 API Key
        base_url: 覆盖默认 Base URL
    
    Returns:
        单个类型返回单个客户端，多个类型返回客户端列表
    
    Example:
        >>> # 获取单个
        >>> client = get_model("deepseek")
        
        >>> # 获取多个
        >>> deepseek, openai = get_model("deepseek", "openai")
        
        >>> # 自定义参数
        >>> client = get_model("openai", model="gpt-4-turbo")
    """
    if not types:
        types = ("deepseek",)  # 默认
    
    clients = []
    for t in types:
        t_lower = t.lower()
        if t_lower not in MODELS:
            raise ValueError(f"不支持的模型: {t}，可用: {list(MODELS.keys())}")
        
        client = _create_client(MODELS[t_lower], model, api_key, base_url)
        logger.info(f"✅ 创建 {t} 客户端")
        clients.append(client)
    
    return clients[0] if len(clients) == 1 else clients


def register_model(name: str, **kwargs) -> None:
    """注册新模型配置"""
    MODELS[name.lower()] = ModelConfig(**kwargs)
    logger.info(f"注册模型: {name}")


def list_models() -> List[str]:
    """列出所有可用模型"""
    return list(MODELS.keys())
