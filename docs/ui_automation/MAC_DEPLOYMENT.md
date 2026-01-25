# 🍎 UI-TARS-1.5-7B macOS M1 Pro 32GB 部署方案

## 硬件评估

| 项目 | 您的配置 | 需求 | 结论 |
|------|----------|------|------|
| 芯片 | M1 Pro | Apple Silicon | ✅ 支持 |
| 内存 | 32GB | 7B 模型约需 8-16GB | ✅ 充足 |
| 存储 | - | 约 15GB | 需确认 |

**结论**：✅ 可以本地部署，推荐使用量化版本

---

## 方案对比

| 方案 | 复杂度 | 速度 | 推荐度 |
|------|--------|------|--------|
| **MLX（推荐）** | ⭐⭐ | 快 | ⭐⭐⭐⭐⭐ |
| **Transformers** | ⭐⭐ | 中 | ⭐⭐⭐ |
| **llama.cpp** | ⭐⭐⭐ | 中 | ⭐⭐⭐ |
| **豆包 API** | ⭐ | 快 | ⭐⭐⭐⭐ |

---

## 方案1：MLX 部署（Apple Silicon 原生，推荐）

MLX 是 Apple 官方为 Apple Silicon 优化的机器学习框架，性能最佳。

### 步骤1：安装依赖

```bash
# 创建虚拟环境
python3 -m venv ui-tars-env
source ui-tars-env/bin/activate

# 安装 MLX 相关
pip install mlx mlx-lm
pip install transformers pillow

# 安装 huggingface-cli（下载模型）
pip install huggingface-hub
```

### 步骤2：下载并转换模型

```bash
# 下载原始模型（约 15GB，需要一些时间）
huggingface-cli download ByteDance-Seed/UI-TARS-1.5-7B --local-dir ./UI-TARS-1.5-7B

# 转换为 MLX 格式（4-bit 量化，减少内存占用）
python -m mlx_lm.convert \
    --hf-path ./UI-TARS-1.5-7B \
    --mlx-path ./UI-TARS-1.5-7B-mlx \
    --quantize \
    --q-bits 4
```

### 步骤3：运行推理

```python
# test_mlx.py
from mlx_lm import load, generate

model, tokenizer = load("./UI-TARS-1.5-7B-mlx")

prompt = "描述一个登录界面的元素"
response = generate(model, tokenizer, prompt=prompt, max_tokens=200)
print(response)
```

**注意**：MLX 对视觉模型的支持可能不完整，如果遇到问题，使用方案2。

---

## 方案2：Transformers 直接加载（稳定可靠）

### 步骤1：安装依赖

```bash
# 创建虚拟环境
python3 -m venv ui-tars-env
source ui-tars-env/bin/activate

# 安装依赖
pip install torch torchvision
pip install transformers accelerate
pip install pillow
pip install huggingface-hub
```

### 步骤2：下载模型

```bash
# 下载模型（约 15GB）
huggingface-cli download ByteDance-Seed/UI-TARS-1.5-7B --local-dir ./UI-TARS-1.5-7B
```

### 步骤3：运行推理脚本

```python
# ui_tars_mac.py
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from PIL import Image
import base64

print("🚀 加载 UI-TARS-1.5-7B 模型...")
print("   首次加载需要几分钟，请耐心等待...")

# 加载模型（使用 MPS 加速）
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "./UI-TARS-1.5-7B",
    torch_dtype=torch.float16,  # 半精度，节省内存
    device_map="mps",  # 使用 Apple Metal 加速
    low_cpu_mem_usage=True
)

processor = AutoProcessor.from_pretrained("./UI-TARS-1.5-7B")

print("✅ 模型加载完成！")

def analyze_screenshot(image_path: str, prompt: str) -> str:
    """分析截图"""
    image = Image.open(image_path)
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt}
            ]
        }
    ]
    
    # 处理输入
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(
        text=[text],
        images=[image],
        return_tensors="pt"
    )
    
    # 移到 MPS
    inputs = {k: v.to("mps") if torch.is_tensor(v) else v for k, v in inputs.items()}
    
    # 生成
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )
    
    # 解码
    result = processor.decode(outputs[0], skip_special_tokens=True)
    return result

# 测试
if __name__ == "__main__":
    # 先截一张手机屏幕
    import subprocess
    subprocess.run(["adb", "exec-out", "screencap", "-p"], 
                   stdout=open("test_screenshot.png", "wb"))
    
    result = analyze_screenshot(
        "test_screenshot.png",
        "请找到屏幕上所有可点击的按钮，并返回它们的坐标位置"
    )
    print("\n📝 分析结果：")
    print(result)
```

### 预期资源占用

```
内存占用：约 16-20GB（FP16）
推理速度：约 5-10 秒/次（首次较慢）
```

---

## 方案3：启动本地 API 服务

如果想作为服务运行，方便 Midscene 调用：

```python
# ui_tars_server.py
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from PIL import Image
import base64
import io
import uvicorn

app = FastAPI()

# 全局加载模型
print("🚀 加载模型...")
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "./UI-TARS-1.5-7B",
    torch_dtype=torch.float16,
    device_map="mps",
    low_cpu_mem_usage=True
)
processor = AutoProcessor.from_pretrained("./UI-TARS-1.5-7B")
print("✅ 模型加载完成！")

class ChatRequest(BaseModel):
    model: str
    messages: list
    max_tokens: int = 512

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """兼容 OpenAI API 格式"""
    
    # 解析消息
    user_message = request.messages[-1]
    content = user_message.get("content", [])
    
    prompt = ""
    image = None
    
    for item in content:
        if item["type"] == "text":
            prompt = item["text"]
        elif item["type"] == "image_url":
            # 解析 base64 图片
            url = item["image_url"]["url"]
            if url.startswith("data:image"):
                base64_data = url.split(",")[1]
                image_bytes = base64.b64decode(base64_data)
                image = Image.open(io.BytesIO(image_bytes))
    
    if image is None:
        return {"error": "No image provided"}
    
    # 构建输入
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt}
            ]
        }
    ]
    
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image], return_tensors="pt")
    inputs = {k: v.to("mps") if torch.is_tensor(v) else v for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=request.max_tokens, do_sample=False)
    
    result = processor.decode(outputs[0], skip_special_tokens=True)
    
    # 返回 OpenAI 格式
    return {
        "id": "chatcmpl-local",
        "object": "chat.completion",
        "model": "ui-tars-1.5-7b-local",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result
                },
                "finish_reason": "stop"
            }
        ]
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**启动服务**：
```bash
pip install fastapi uvicorn
python ui_tars_server.py
```

**配置 Midscene 使用本地服务**：
```env
OPENAI_API_KEY=local
OPENAI_BASE_URL=http://localhost:8000/v1
MIDSCENE_MODEL_NAME=ui-tars-1.5-7b-local
```

---

## 方案4：直接用豆包 API（最省心）

如果觉得本地部署麻烦，继续用您现有的豆包 API 配置即可：

```env
MIDSCENE_MODEL_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
MIDSCENE_MODEL_API_KEY=your-api-key
MIDSCENE_MODEL_NAME=doubao-1-5-ui-tars-250428
MIDSCENE_MODEL_FAMILY=vlm-ui-tars-doubao-1.5
```

**成本对比**：
| 方案 | 初始成本 | 运行成本 | 速度 |
|------|----------|----------|------|
| 本地部署 | 时间 + 15GB 空间 | 电费 | 5-10秒/次 |
| 豆包 API | 无 | 约 ¥0.01-0.05/次 | 2-3秒/次 |

---

## 快速开始命令汇总

```bash
# 1. 创建环境
cd /Users/wangxiaoqi/Documents/翼支付工作文件/AI相关/ui_automation
python3 -m venv ui-tars-env
source ui-tars-env/bin/activate

# 2. 安装依赖
pip install torch torchvision transformers accelerate pillow huggingface-hub fastapi uvicorn

# 3. 下载模型（约 15GB，需要较长时间）
huggingface-cli download ByteDance-Seed/UI-TARS-1.5-7B --local-dir ./UI-TARS-1.5-7B

# 4. 运行测试脚本
python ui_tars_mac.py
```

---

## 注意事项

1. **首次加载慢**：第一次加载模型需要 2-5 分钟，后续使用会快很多
2. **内存占用**：运行时约占用 16-20GB 内存，留意不要同时运行太多大型应用
3. **网络下载**：模型约 15GB，建议使用稳定网络或开启代理
4. **MPS 兼容性**：部分操作可能不支持 MPS，会自动 fallback 到 CPU

---

## 我的建议

对于 **M1 Pro 32GB**：

| 场景 | 建议 |
|------|------|
| 想快速验证 | 继续用豆包 API |
| 想省 API 费用 | 本地部署（方案2） |
| 数据敏感 | 必须本地部署 |
| 长期使用 | 本地部署更划算 |

**预计效果**：
- 推理速度：5-10 秒/次
- 内存占用：~18GB
- 部署耗时：下载 1-2 小时，配置 30 分钟

