# 🤖 UI-TARS-1.5-7B 本地部署指南

## 一、模型概述

**[UI-TARS-1.5-7B](https://huggingface.co/ByteDance-Seed/UI-TARS-1.5-7B)** 是字节跳动开源的多模态 GUI 自动化模型。

| 属性 | 信息 |
|------|------|
| 参数量 | 7B（约 8B 含视觉编码器） |
| 基座模型 | Qwen2.5-VL |
| 用途 | GUI 元素定位、自动化操作 |
| 许可证 | Apache 2.0（可商用） |

### 性能亮点

根据 [Hugging Face 模型页面](https://huggingface.co/ByteDance-Seed/UI-TARS-1.5-7B)：

| 基准测试 | UI-TARS-1.5 | OpenAI CUA | Claude 3.7 |
|----------|-------------|------------|------------|
| OSWorld (计算机操作) | **42.5** | 36.4 | 28.0 |
| ScreenSpot-V2 (定位) | **94.2** | 87.9 | 87.6 |
| Android World | **64.2** | - | - |

---

## 二、硬件要求评估

### macOS（Apple Silicon）

| 配置 | 可行性 | 说明 |
|------|--------|------|
| M1 8GB | ❌ 不推荐 | 内存不足 |
| M1/M2 16GB | ⚠️ 勉强 | 需要 4-bit 量化，速度慢 |
| M2 Pro/M3 24GB | ✅ 可行 | 推荐 4-bit 量化 |
| M2 Max/M3 Max 32GB+ | ✅ 流畅 | 可用 8-bit 量化 |

### Linux（NVIDIA GPU）

| 显卡 | 显存 | 可行性 | 说明 |
|------|------|--------|------|
| RTX 3060 | 12GB | ⚠️ 勉强 | 必须 4-bit 量化 |
| RTX 3080/4070 | 12GB | ⚠️ 勉强 | 必须 4-bit 量化 |
| RTX 3090/4080 | 24GB | ✅ 推荐 | 可用 FP16 |
| RTX 4090 | 24GB | ✅ 最佳 | FP16 流畅运行 |
| A100/H100 | 40GB+ | ✅ 生产级 | 可多并发 |

### 显存需求估算

```
FP32：~28GB（不推荐）
FP16/BF16：~14GB
INT8 量化：~8GB
INT4 量化：~4-5GB
```

---

## 三、部署方案对比

| 方案 | 难度 | 性能 | macOS | Linux | 推荐场景 |
|------|------|------|-------|-------|----------|
| **vLLM** | ⭐⭐ | 最快 | ❌ | ✅ | 生产环境 |
| **Transformers + bitsandbytes** | ⭐⭐ | 中等 | ❌ | ✅ | 开发测试 |
| **llama.cpp (GGUF)** | ⭐⭐⭐ | 中等 | ✅ | ✅ | 低资源设备 |
| **Ollama** | ⭐ | 中等 | ✅ | ✅ | 最简单 |
| **云端 API** | ⭐ | - | ✅ | ✅ | 省心省力 |

---

## 四、方案详解

### 方案1：vLLM 部署（Linux + NVIDIA GPU，推荐）

**优点**：性能最好，兼容 OpenAI API 格式
**要求**：Linux + NVIDIA GPU（24GB 显存推荐）

```bash
# 1. 安装 vLLM
pip install vllm==0.6.6

# 2. 下载模型（约 15GB）
# 方式1：git lfs
git lfs install
git clone https://huggingface.co/ByteDance-Seed/UI-TARS-1.5-7B

# 方式2：huggingface-cli（推荐，支持断点续传）
pip install huggingface-hub
huggingface-cli download ByteDance-Seed/UI-TARS-1.5-7B --local-dir ./UI-TARS-1.5-7B

# 3. 启动服务
python -m vllm.entrypoints.openai.api_server \
    --model ./UI-TARS-1.5-7B \
    --served-model-name ui-tars \
    --limit-mm-per-prompt image=5 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9 \
    --host 0.0.0.0 \
    --port 8000

# 4. 测试 API
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ui-tars",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "描述这个界面"},
          {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
        ]
      }
    ]
  }'
```

---

### 方案2：Transformers 直接加载（开发测试）

**优点**：灵活，易调试
**要求**：NVIDIA GPU 12GB+（量化）或 24GB+（FP16）

```python
# 安装依赖
# pip install transformers accelerate bitsandbytes pillow

from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from PIL import Image
import torch

# 加载模型（4-bit 量化，节省显存）
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "ByteDance-Seed/UI-TARS-1.5-7B",
    torch_dtype=torch.bfloat16,
    load_in_4bit=True,  # 4-bit 量化，约需 6GB 显存
    device_map="auto"
)
processor = AutoProcessor.from_pretrained("ByteDance-Seed/UI-TARS-1.5-7B")

# 加载截图
image = Image.open("screenshot.png")

# 构建输入
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": "找到登录按钮的位置坐标"}
        ]
    }
]

# 推理
inputs = processor.apply_chat_template(messages, return_tensors="pt")
inputs = inputs.to(model.device)

outputs = model.generate(**inputs, max_new_tokens=512)
result = processor.decode(outputs[0], skip_special_tokens=True)
print(result)
```

**显存占用参考**：
- `load_in_4bit=True`：约 6-8GB
- `load_in_8bit=True`：约 10-12GB
- 不量化（FP16）：约 14-16GB

---

### 方案3：llama.cpp + GGUF（macOS 友好）

**优点**：支持 CPU 和 Apple Silicon，无需 NVIDIA GPU
**缺点**：需要转换模型格式，速度较慢

```bash
# 1. 安装 llama.cpp（macOS）
brew install llama.cpp

# 或从源码编译（支持 Metal）
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make LLAMA_METAL=1  # macOS Metal 加速

# 2. 转换模型为 GGUF 格式
# 需要先下载模型，然后转换
python convert-hf-to-gguf.py ./UI-TARS-1.5-7B --outfile ui-tars-7b.gguf

# 3. 量化（降低显存需求）
./quantize ui-tars-7b.gguf ui-tars-7b-q4_k_m.gguf q4_k_m

# 4. 运行（需要支持多模态的 llama.cpp 版本）
./llama-server -m ui-tars-7b-q4_k_m.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    --n-gpu-layers 99  # macOS Metal 加速
```

**注意**：UI-TARS 基于 Qwen2.5-VL，llama.cpp 对视觉模型的支持可能不完整。

---

### 方案4：使用豆包 API（最省心）

如果本地资源有限，直接使用**字节跳动豆包**的云端 API 是最省心的方案。

```bash
# .env 配置
MIDSCENE_MODEL_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
MIDSCENE_MODEL_API_KEY=your-api-key
MIDSCENE_MODEL_NAME=doubao-1-5-ui-tars-250428
MIDSCENE_MODEL_FAMILY=vlm-ui-tars-doubao-1.5
```

**优点**：
- 无需本地 GPU
- 无需下载模型
- 付费按量计费

**缺点**：
- 依赖网络
- 有 API 调用成本

---

## 五、macOS 专属方案

### 方案 A：MLX 框架（Apple Silicon 原生）

MLX 是 Apple 为 Apple Silicon 优化的机器学习框架。

```bash
# 安装 MLX
pip install mlx mlx-lm

# 检查是否有 MLX 版本的 UI-TARS
# 目前 UI-TARS 官方未提供 MLX 版本，可能需要自行转换
```

**现状**：UI-TARS 暂无官方 MLX 版本，转换较复杂。

### 方案 B：Ollama（如果有 GGUF 版本）

```bash
# 安装 Ollama
brew install ollama

# 创建 Modelfile
# 需要先转换为 GGUF 格式
cat > Modelfile << EOF
FROM ./ui-tars-7b-q4_k_m.gguf
TEMPLATE "{{ .System }} {{ .Prompt }}"
EOF

# 创建模型
ollama create ui-tars -f Modelfile

# 运行
ollama run ui-tars
```

**现状**：UI-TARS 官方未提供 GGUF，需自行转换。

---

## 六、部署复杂度评估

| 你的硬件 | 推荐方案 | 复杂度 | 预计耗时 |
|----------|----------|--------|----------|
| **Mac M1/M2 16GB** | 豆包 API | ⭐ | 5分钟 |
| **Mac M2 Pro+ 24GB** | Transformers + 量化 | ⭐⭐⭐ | 2小时 |
| **Linux + RTX 3090/4090** | vLLM | ⭐⭐ | 1小时 |
| **Linux + RTX 3060/4060** | Transformers + 4bit | ⭐⭐ | 1小时 |
| **无 GPU** | 豆包 API | ⭐ | 5分钟 |

---

## 七、我的建议

### 如果你是 macOS 用户

```
1. 内存 < 24GB → 直接用豆包 API，不要折腾本地部署
2. 内存 >= 24GB → 可尝试 Transformers + 4bit 量化
3. 内存 >= 32GB → 可流畅运行
```

### 如果你是 Linux 用户

```
1. 无 GPU → 用豆包 API
2. 显存 12GB → Transformers + 4bit 量化
3. 显存 24GB → vLLM（推荐）
4. 显存 40GB+ → vLLM + 并发
```

### 总结

| 场景 | 推荐 |
|------|------|
| 快速验证 | 豆包 API（无需部署） |
| 开发测试 | Transformers + 量化 |
| 生产环境 | vLLM 或豆包 API |
| 低成本长期使用 | 本地部署 |
| 数据敏感 | 必须本地部署 |

---

## 八、参考资源

- 模型地址：https://huggingface.co/ByteDance-Seed/UI-TARS-1.5-7B
- 官方代码：https://github.com/bytedance/UI-TARS
- 桌面应用：https://github.com/bytedance/UI-TARS-desktop
- 论文：[UI-TARS: Pioneering Automated GUI Interaction with Native Agents](https://arxiv.org/abs/2501.12326)

