"""
LLM 模型客户端工厂 - 统一接口封装多种大模型
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from loguru import logger

# 获取项目根目录（向上找到包含 .Env 的目录）
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / '.Env')


# ============== 配置定义 ==============

@dataclass
class ModelConfig:
    """模型配置"""
    model: str  # 模型名称
    api_key_env: str  # API Key 环境变量名
    base_url: str  # API 地址
    vision: bool = False  # 是否支持视觉


# 预置模型配置
MODELS: dict[str, ModelConfig] = {
    "deepseek": ModelConfig("deepseek-chat", "DEEPSEEK_API_KEY", "https://api.deepseek.com/v1"),
    "qwenvl": ModelConfig("qwen-vl-max", "QWENVL_API_KEY", "https://dashscope.aliyuncs.com/compatible-mode/v1",
                          vision=True),
    "openai": ModelConfig("gpt-4", "OPENAI_API_KEY", "https://api.openai.com/v1"),
    "gpt4v": ModelConfig("gpt-4-vision-preview", "OPENAI_API_KEY", "https://api.openai.com/v1", vision=True),
    "moonshot": ModelConfig("moonshot-v1-8k", "MOONSHOT_API_KEY", "https://api.moonshot.cn/v1"),
    "zhipu": ModelConfig("glm-4", "ZHIPU_API_KEY", "https://open.bigmodel.cn/api/paas/v4"),
    "doubao": ModelConfig("doubao-pro-32k", "DOUBAO_API_KEY", "https://ark.cn-beijing.volces.com/api/v3"),
}


# ============== 核心方法 ==============

def get_model(
        name: str = "deepseek",
        *,  # 强制后面的参数必须用关键字传递，更清晰
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
) -> OpenAIChatCompletionClient:
    """
    获取单个模型客户端
    
    Args:
        name: 模型类型 (deepseek/openai/qwenvl/gpt4v/moonshot/zhipu/doubao)
        model: 自定义模型名（可选）
        api_key: 自定义 API Key（可选，默认从环境变量读取）
        base_url: 自定义 API 地址（可选）

    """
    name = name.lower()
    if name not in MODELS:
        raise ValueError(f"不支持: {name}，可选: {list(MODELS.keys())}")

    cfg = MODELS[name]
    key = api_key or os.getenv(cfg.api_key_env)
    if not key:
        raise ValueError(f"请设置环境变量 {cfg.api_key_env}")

    client = OpenAIChatCompletionClient(
        model=model or cfg.model,
        api_key=key,
        base_url=base_url or cfg.base_url,
        model_info={"vision": cfg.vision,
                    "function_calling": True,
                    "json_output": True,
                    "structured_output": True,
                    "multiple_system_messages": True,
                    "family": "Unknown"},
    )
    logger.info(f"✅ 创建 {name} 客户端")
    return client


def get_models(*names: str) -> list[OpenAIChatCompletionClient]:
    """
    批量获取多个模型客户端

    """
    return [get_model(name) for name in names]


def register_model(name: str, model: str, api_key_env: str, base_url: str, vision: bool = False):
    """注册自定义模型"""
    MODELS[name.lower()] = ModelConfig(model, api_key_env, base_url, vision)
    logger.info(f"注册模型: {name}")


def list_models() -> list[str]:
    """列出所有可用模型"""
    return list(MODELS.keys())


if __name__ == '__main__':
    client = get_model("deepseek",
                       model=os.getenv("DEEPSEEK_MODEL_NAME", "deepseek"),
                       api_key=os.getenv("DEEPSEEK_API_KEY"))
    print(client)
