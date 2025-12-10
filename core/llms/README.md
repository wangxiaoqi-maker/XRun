# LLM 模型客户端模块

## 📝 简介

这个模块提供了统一的 LLM 模型客户端接口，支持多种大模型提供商，包括：

- **DeepSeek**
- **QwenVL** (阿里通义千问视觉版)
- **OpenAI** (GPT-4, GPT-3.5等)
- **Azure OpenAI**
- **Moonshot** (月之暗面)
- **Zhipu** (智谱 GLM)
- **Doubao** (字节豆包)
- 支持自定义注册其他模型

## 🎯 设计特点

### 1. **配置驱动**
所有模型配置集中管理，添加新模型只需注册配置，无需修改核心代码。

### 2. **工厂模式**
统一的 `create_model_client()` 方法创建所有类型的客户端，减少重复代码。

### 3. **灵活配置**
支持多种配置方式：
- 环境变量
- Settings 配置
- 直接传参

### 4. **向后兼容**
保留了旧的便捷方法，不影响已有代码。

### 5. **易于扩展**
通过 `register_model()` 可以动态注册新模型。

---

## 🚀 快速开始

### 基础使用

```python
from core.llms.base_llm import create_model_client

# 创建 DeepSeek 客户端
client = create_model_client("deepseek")

# 创建 QwenVL 客户端（带视觉能力）
vision_client = create_model_client("qwenvl")

# 创建 OpenAI 客户端
openai_client = create_model_client("openai")
```

### 自定义模型名称

```python
# 使用 GPT-4 Turbo
client = create_model_client("openai", model_name="gpt-4-turbo")

# 使用 GPT-3.5
client = create_model_client("openai", model_name="gpt-3.5-turbo")
```

### 直接传入凭证

```python
# 不依赖环境变量，直接传入
client = create_model_client(
    "deepseek",
    api_key="sk-your-api-key",
    base_url="https://custom-endpoint.com/v1"
)
```

---

## ⚙️ 环境变量配置

在 `.env` 文件中配置各个模型的凭证：

```bash
# DeepSeek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1  # 可选，有默认值

# QwenVL (阿里云)
QWENVL_API_KEY=sk-your-qwen-key
QWENVL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  # 可选

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选

# Azure OpenAI
AZURE_API_KEY=your-azure-key
AZURE_BASE_URL=https://your-resource.openai.azure.com

# Moonshot (月之暗面)
MOONSHOT_API_KEY=sk-your-moonshot-key
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1  # 可选

# Zhipu (智谱)
ZHIPU_API_KEY=your-zhipu-key
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4  # 可选

# Doubao (字节)
DOUBAO_API_KEY=your-doubao-key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3  # 可选
```

---

## 🔧 高级用法

### 1. 注册自定义模型

```python
from core.llms.base_llm import register_model, create_model_client

# 注册 Claude
register_model(
    name="claude",
    model="claude-3-opus-20240229",
    api_key_attr="CLAUDE_API_KEY",
    base_url_attr="CLAUDE_BASE_URL",
    default_base_url="https://api.anthropic.com/v1",
    vision=True,
    function_calling=True,
)

# 使用新注册的模型
claude_client = create_model_client("claude")
```

### 2. 列出所有可用模型

```python
from core.llms.base_llm import list_available_models

models = list_available_models()
print(models)
# ['deepseek', 'qwenvl', 'openai', 'gpt4v', 'azure', 'moonshot', 'zhipu', 'doubao']
```

### 3. 覆盖模型配置

```python
# 覆盖 model_info 中的配置
client = create_model_client(
    "deepseek",
    vision=True,  # 开启视觉能力（如果模型支持）
    max_tokens=8000,  # 自定义参数
)
```

---

## 📦 在插件中使用

### UI 自动化插件

```python
# plugins/ui_automation/agents/page_analyzer.py

from core.llms.base_llm import create_model_client

class PageAnalyzerAgent:
    def __init__(self):
        # 使用带视觉能力的模型
        self.model_client = create_model_client("qwenvl")
    
    async def analyze_screenshot(self, image_url: str):
        # 使用 vision 模型分析截图
        pass
```

### 接口自动化插件

```python
# plugins/api_automation/agents/testcase_generator.py

from core.llms.base_llm import create_model_client

class TestCaseGeneratorAgent:
    def __init__(self):
        # 使用文本模型即可
        self.model_client = create_model_client("deepseek")
    
    async def generate_test_cases(self, swagger_doc: dict):
        # 生成测试用例
        pass
```

### 用例生成插件

```python
# plugins/testcase_generator/agents/requirement_parser.py

from core.llms.base_llm import create_model_client

class RequirementParserAgent:
    def __init__(self, model_type: str = "openai"):
        # 支持配置不同的模型
        self.model_client = create_model_client(model_type)
    
    async def parse_requirement(self, doc: str):
        # 解析需求文档
        pass
```

---

## 🔄 迁移指南

### 从旧代码迁移

**旧代码：**
```python
from core.llms.base_llm import get_deepseek_model_client

client = get_deepseek_model_client()
```

**新代码（推荐）：**
```python
from core.llms.base_llm import create_model_client

client = create_model_client("deepseek")
```

**或者保持不变（向后兼容）：**
```python
# 旧代码仍然可以工作
from core.llms.base_llm import get_deepseek_model_client

client = get_deepseek_model_client()
```

---

## 📋 内置模型配置

| 模型标识 | 模型名称 | 视觉能力 | 默认 Base URL |
|---------|---------|---------|--------------|
| `deepseek` | deepseek-chat | ❌ | https://api.deepseek.com/v1 |
| `qwenvl` | qwen-vl-plus | ✅ | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| `openai` | gpt-4 | ❌ | https://api.openai.com/v1 |
| `gpt4v` | gpt-4-vision-preview | ✅ | https://api.openai.com/v1 |
| `azure` | gpt-4 | ❌ | https://your-resource.openai.azure.com |
| `moonshot` | moonshot-v1-8k | ❌ | https://api.moonshot.cn/v1 |
| `zhipu` | glm-4 | ❌ | https://open.bigmodel.cn/api/paas/v4 |
| `doubao` | doubao-pro-32k | ❌ | https://ark.cn-beijing.volces.com/api/v3 |

---

## 🛠️ API 参考

### `create_model_client()`

创建模型客户端的工厂方法。

**参数：**
- `model_type` (str): 模型类型标识
- `model_name` (Optional[str]): 覆盖默认的模型名称
- `api_key` (Optional[str]): 直接传入 API Key（优先级最高）
- `base_url` (Optional[str]): 直接传入 Base URL（优先级最高）
- `**extra_config`: 额外的配置参数

**返回：**
- `OpenAIChatCompletionClient` 实例

**异常：**
- `ValueError`: 模型类型不存在或缺少必要配置
- `Exception`: 客户端创建失败

---

### `register_model()`

注册新的模型配置。

**参数：**
- `name` (str): 模型标识名
- `model` (str): 模型名称
- `api_key_attr` (str): API Key 在 settings 中的属性名
- `base_url_attr` (str): Base URL 在 settings 中的属性名
- `default_base_url` (str): 默认的 Base URL
- `**kwargs`: 其他配置参数（vision, function_calling 等）

---

### `list_available_models()`

列出所有已注册的模型类型。

**返回：**
- `list[str]`: 模型标识列表

---

## 🤝 贡献

欢迎提交新的模型配置！

1. 在 `MODEL_CONFIGS` 字典中添加配置
2. 或使用 `register_model()` 动态注册
3. 更新本文档的模型列表

---

## 📄 许可证

MIT License

