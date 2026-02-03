"""
页面分析服务 - 调用视觉大模型分析 App 截图

职责：
- 构建多模态 Prompt
- 调用视觉大模型（qwen-vl / gpt-4v）
- 解析 LLM 返回的 JSON
- 生成结构化的页面分析结果
"""
import base64
import hashlib
import json
import time
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger

from ..config import AnalyzerConfig, get_analyzer_config


# ============== Prompt 模板 ==============

MOBILE_UI_ANALYSIS_PROMPT = """
你是一个专业的 **移动端 UI 元素检测引擎**，为 Midscene 自动化测试框架提供元素识别。

# 核心任务
精确识别截图中所有可交互元素，生成可用于 Midscene aiTap/aiInput 等方法的定位器。

# bbox 坐标规则 [极其重要]
格式：**[left%, top%, width%, height%]**，值为 **0-100 的百分比**

计算公式（图片尺寸 W x H 像素）：
- left% = 元素左边缘 ÷ W × 100
- top% = 元素上边缘 ÷ H × 100
- width% = 元素宽度 ÷ W × 100
- height% = 元素高度 ÷ H × 100

质量要求：
- 所有值在 0-100 范围内
- left% + width% ≤ 100，top% + height% ≤ 100
- bbox 紧密包裹元素，不包含多余空白

# midscene_locator 定位器规则 [核心]
定位器用于 Midscene 的 aiTap('定位器') 等方法，必须是**清晰、唯一、中文**的自然语言描述。

**定位器构成**（按优先级组合）：
1. **位置** + **文字内容**：`底部导航栏的"首页"Tab`、`顶部的"返回"按钮`
2. **位置** + **视觉特征**：`左上角的红色返回箭头`、`右上角的蓝色设置图标`
3. **位置** + **功能描述**：`搜索框右侧的搜索按钮`、`用户头像下方的编辑按钮`
4. **相对位置**：`"余额"文字右侧的刷新图标`、`列表第一项的"去完成"按钮`

**好的定位器示例**：
- `页面底部导航栏的"我的"Tab图标` ✓
- `顶部导航栏左侧的返回箭头按钮` ✓
- `九宫格区域中的"转账"功能入口` ✓
- `搜索输入框` ✓
- `"余额"数值右侧的眼睛图标` ✓
- `红色的"立即购买"按钮` ✓

**差的定位器示例**：
- `button_1` ✗ (无意义的英文编号)
- `首页` ✗ (太模糊，不知道是Tab还是其他)
- `icon` ✗ (没有任何描述)

# 扫描策略
从上到下、从左到右扫描：
1. **顶部导航栏**：返回按钮、标题、搜索图标、设置图标、更多按钮
2. **中部内容区**：
   - 九宫格/金刚区：每个图标+文字是**独立**元素
   - 卡片/Banner：可点击的整个卡片区域
   - 列表项：每行的按钮、链接、右侧箭头
   - 输入框、开关、选择器
3. **底部 Tab 栏**：每个 Tab 是**独立**元素（图标+文字）

# 输出格式（严格 JSON）
```json
{
  "page_name": "页面中文名称",
  "page_type": "home|list|detail|form|settings|profile|unknown",
  "page_description": "一句话描述页面功能",
  "confidence_score": 0.85,
  "elements": [
    {
      "name": "元素语义名称",
      "type": "button|icon_button|tab|card|text_input|link|switch|list_item|banner",
      "text_content": "元素上的可见文字",
      "description": "视觉描述：颜色、形状、图标特征",
      "bbox": [10.5, 2.3, 8.2, 4.1],
      "area": "顶部|中部|底部",
      "midscene_locator": "页面底部导航栏的"首页"Tab图标",
      "confidence_score": 0.9,
      "is_navigation": true,
      "target_page": "首页"
    }
  ]
}
```

# 置信度说明
- **页面 confidence_score**：整体识别质量（0-1），基于元素识别完整度
- **元素 confidence_score**：单个元素识别准确度（0-1）
  - 0.9+ 高置信度：文字清晰、边界明确
  - 0.7-0.9 中置信度：部分模糊但可识别
  - <0.7 低置信度：猜测性识别

# 导航元素标记
设置 `is_navigation: true` + `target_page` 的情况：
- 底部 Tab → `target_page: "首页/我的/发现..."`
- 返回按钮 → `target_page: "上一页"`
- 九宫格入口 → `target_page: "转账页/充值页/..."`
- "查看更多"/"去完成" → `target_page: "详情页"`

# 必须遵守
1. bbox 使用百分比（0-100），精确到小数点后1位
2. midscene_locator 必须是**中文**自然语言描述
3. 每个独立可点击区域都是一个元素，不要合并
4. 只输出 JSON，不要任何其他文字
"""


class PageAnalyzerService:
    """
    页面分析服务
    
    调用视觉大模型分析 App 截图，提取可测试元素
    """
    
    # 最大重试次数
    MAX_RETRIES = 2
    
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        self.config = config or get_analyzer_config()
        self._vision_client = None
        self._initialized = False
        self._current_provider_id = None
        self._current_model_id = None
        # 用于记录 token 用量
        self._last_usage = None
        # 用于 bbox 坐标转换的图片尺寸
        self._image_width = None
        self._image_height = None
    
    async def initialize(self, provider_id: Optional[str] = None, model_id: Optional[str] = None) -> None:
        """
        初始化视觉模型客户端
        
        Args:
            provider_id: 供应商 ID（从数据库配置）
            model_id: 模型 ID（从数据库配置）
        """
        # 如果指定了新的模型配置，需要重新初始化
        if provider_id and model_id:
            if provider_id != self._current_provider_id or model_id != self._current_model_id:
                self._initialized = False
                self._current_provider_id = provider_id
                self._current_model_id = model_id
        
        if self._initialized:
            return
        
        try:
            # 如果指定了 provider_id 和 model_id，从数据库加载配置
            if provider_id and model_id:
                self._vision_client = await self._create_client_from_db(provider_id, model_id)
                logger.info(f"✅ PageAnalyzerService 初始化成功 (DB配置): provider={provider_id}")
            else:
                # 使用默认配置
                from llm.client import get_model
                self._vision_client = get_model(self.config.ANALYZER_VISION_MODEL)
                logger.info(f"✅ PageAnalyzerService 初始化成功: {self.config.ANALYZER_VISION_MODEL}")
            
            self._initialized = True
        except Exception as e:
            logger.error(f"❌ PageAnalyzerService 初始化失败: {e}")
            raise
    
    async def _create_client_from_db(self, provider_id: str, model_id: str):
        """从数据库配置创建客户端"""
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        from apps.ui_automation.database import get_session
        from apps.ui_automation.models.llm_config import LLMProvider, LLMModel
        from sqlalchemy import select
        
        async with get_session() as session:
            # 获取供应商
            provider_result = await session.execute(
                select(LLMProvider).where(LLMProvider.id == provider_id)
            )
            provider = provider_result.scalar_one_or_none()
            if not provider:
                raise ValueError(f"供应商不存在: {provider_id}")
            
            # 获取模型
            model_result = await session.execute(
                select(LLMModel).where(LLMModel.id == model_id)
            )
            model = model_result.scalar_one_or_none()
            if not model:
                raise ValueError(f"模型不存在: {model_id}")
            
            # 创建客户端
            client = OpenAIChatCompletionClient(
                model=model.model_id,
                api_key=provider.api_key,
                base_url=provider.base_url,
                model_info={
                    "vision": model.supports_vision,
                    "function_calling": model.supports_function_call,
                    "json_output": True,
                    "structured_output": True,
                    "multiple_system_messages": True,
                    "family": "Unknown"
                }
            )
            
            logger.info(f"✅ 从 DB 创建客户端: {provider.name} / {model.name}")
            return client
    
    def calculate_image_hash(self, image_data: str) -> str:
        """
        计算图片 MD5 哈希（用于去重）
        
        Args:
            image_data: Base64 编码的图片数据
            
        Returns:
            MD5 哈希字符串
        """
        # 移除 Base64 前缀（如 data:image/png;base64,）
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        
        # 解码并计算 MD5
        image_bytes = base64.b64decode(image_data)
        return hashlib.md5(image_bytes).hexdigest()
    
    async def analyze_screenshot(
        self,
        image_data: str,
        context_hint: Optional[str] = None,
        provider_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析截图，提取页面信息和元素（支持重试）
        
        Args:
            image_data: Base64 编码的截图
            context_hint: 上下文提示（可选，如"这是支付宝首页"）
            provider_id: 供应商 ID（可选，从数据库配置）
            model_id: 模型 ID（可选，从数据库配置）
            
        Returns:
            分析结果字典，包含 page_info 和 elements
        """
        await self.initialize(provider_id=provider_id, model_id=model_id)
        
        start_time = time.time()
        last_error = None
        
        # 先解析图片获取尺寸
        image_size = self._get_image_size(image_data)
        if image_size:
            self._image_width, self._image_height = image_size
            logger.info(f"截图尺寸: {self._image_width}x{self._image_height}")
        
        # 重试循环
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                # 构建 Prompt（包含图片尺寸信息）
                prompt = self._build_prompt(context_hint, image_size, attempt > 0)
                
                # 构建消息（多模态）
                messages = self._build_messages(image_data, prompt)
                
                # 调用视觉模型
                response = await self._call_vision_model(messages)
                
                # 解析响应
                result = self._parse_response(response)
                
                # 验证结果质量
                valid_elements = self._validate_and_filter_elements(result.get("elements", []))
                
                # 如果有效元素太少，且还有重试机会，则重试
                if len(valid_elements) < 5 and attempt < self.MAX_RETRIES:
                    logger.warning(f"第 {attempt + 1} 次分析只识别到 {len(valid_elements)} 个有效元素，尝试重试...")
                    continue
                
                result["elements"] = valid_elements
                
                # 添加处理时间
                result["processing_time"] = round(time.time() - start_time, 3)
                result["screenshot_hash"] = self.calculate_image_hash(image_data)
                result["retry_count"] = attempt
                
                # 添加 token 用量信息
                if self._last_usage:
                    result["usage"] = self._last_usage
                
                logger.info(
                    f"页面分析完成: {result.get('page_name', 'Unknown')} - "
                    f"{len(result.get('elements', []))} 个元素 - "
                    f"{result['processing_time']}s (重试 {attempt} 次)"
                )
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"第 {attempt + 1} 次分析失败: {e}")
                if attempt < self.MAX_RETRIES:
                    logger.info(f"将在 1 秒后重试...")
                    await self._async_sleep(1)
        
        # 所有重试都失败
        logger.error(f"页面分析失败（已重试 {self.MAX_RETRIES} 次）: {last_error}")
        raise last_error
    
    async def _async_sleep(self, seconds: float):
        """异步睡眠"""
        import asyncio
        await asyncio.sleep(seconds)
    
    def _validate_and_filter_elements(self, elements: List[Dict]) -> List[Dict]:
        """验证并过滤元素，移除无效的 bbox"""
        valid_elements = []
        
        for element in elements:
            bbox = element.get("bbox")
            
            # 验证 bbox 格式
            if not bbox or not isinstance(bbox, list) or len(bbox) != 4:
                logger.debug(f"元素 '{element.get('name')}' bbox 格式无效，跳过")
                continue
            
            try:
                left, top, width, height = [float(v) for v in bbox]
                
                # 验证数值范围
                if width <= 0 or height <= 0:
                    logger.debug(f"元素 '{element.get('name')}' bbox 尺寸无效 ({width}x{height})，跳过")
                    continue
                
                # 如果是像素值（>100），需要转换
                if any(v > 100 for v in [left, top]) or left + width > 105 or top + height > 105:
                    # 转换为百分比
                    device_w = self._image_width or 1080
                    device_h = self._image_height or 2400
                    
                    # 判断格式
                    if width > left and height > top:
                        # [left, top, right, bottom] 格式
                        actual_width = width - left
                        actual_height = height - top
                    else:
                        actual_width = width
                        actual_height = height
                    
                    bbox = [
                        round((left / device_w) * 100, 1),
                        round((top / device_h) * 100, 1),
                        round((actual_width / device_w) * 100, 1),
                        round((actual_height / device_h) * 100, 1)
                    ]
                    element["bbox"] = bbox
                    left, top, width, height = bbox
                
                # 最终验证
                if left < 0 or top < 0 or left + width > 105 or top + height > 105:
                    logger.debug(f"元素 '{element.get('name')}' bbox 超出范围，跳过")
                    continue
                
                # 过滤太小的元素（可能是噪声）
                if width < 0.5 or height < 0.5:
                    logger.debug(f"元素 '{element.get('name')}' bbox 太小，跳过")
                    continue
                
                # 过滤太大的元素（可能是整个页面）
                if width > 95 and height > 95:
                    logger.debug(f"元素 '{element.get('name')}' bbox 太大（可能是整页），跳过")
                    continue
                
                valid_elements.append(element)
                
            except (ValueError, TypeError) as e:
                logger.debug(f"元素 '{element.get('name')}' bbox 解析失败: {e}")
                continue
        
        logger.info(f"bbox 验证: {len(elements)} -> {len(valid_elements)} 个有效元素")
        return valid_elements
    
    def _get_image_size(self, image_data: str) -> Optional[Tuple[int, int]]:
        """解析图片获取尺寸"""
        from PIL import Image as PILImage
        import io
        
        try:
            # 提取 base64 数据
            if image_data.startswith("data:"):
                _, base64_data = image_data.split(",", 1)
            else:
                base64_data = image_data
            
            # 解码并获取尺寸
            image_bytes = base64.b64decode(base64_data)
            buffer = io.BytesIO(image_bytes)
            pil_image = PILImage.open(buffer)
            return pil_image.size  # (width, height)
        except Exception as e:
            logger.warning(f"获取图片尺寸失败: {e}")
            return None
    
    def _build_prompt(self, context_hint: Optional[str] = None, image_size: Optional[Tuple[int, int]] = None, is_retry: bool = False) -> str:
        """构建分析 Prompt"""
        prompt = MOBILE_UI_ANALYSIS_PROMPT
        
        # 添加图片尺寸信息
        if image_size:
            width, height = image_size
            prompt += f"""

## 当前图片尺寸
图片尺寸为 **{width} x {height}** 像素。

bbox 计算示例：
- 如果元素在像素位置 (100, 200)，宽 150px，高 80px
- left% = 100 ÷ {width} × 100 = {round(100/width*100, 1)}
- top% = 200 ÷ {height} × 100 = {round(200/height*100, 1)}
- width% = 150 ÷ {width} × 100 = {round(150/width*100, 1)}
- height% = 80 ÷ {height} × 100 = {round(80/height*100, 1)}
- 结果: [{round(100/width*100, 1)}, {round(200/height*100, 1)}, {round(150/width*100, 1)}, {round(80/height*100, 1)}]
"""
        
        # 重试时增加强调
        if is_retry:
            prompt += """

## ⚠️ 重要提醒（上次识别不完整）
请特别注意：
1. **底部 Tab 栏**：必须识别每个 Tab（首页、我的等）
2. **顶部导航**：返回按钮、标题旁的图标
3. **九宫格区域**：每个图标单独识别
4. **bbox 精度**：确保坐标准确，不要估算
"""
        
        if context_hint:
            prompt += f"\n\n## 上下文提示\n{context_hint}\n"
        
        return prompt
    
    def _build_messages(self, image_data: str, prompt: str) -> List[Dict[str, Any]]:
        """构建多模态消息"""
        # 确保 Base64 格式正确
        if not image_data.startswith("data:"):
            image_data = f"data:image/png;base64,{image_data}"
        
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data}
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    
    async def _call_vision_model(self, messages: List[Dict[str, Any]]) -> str:
        """调用视觉模型"""
        from autogen_core.models import UserMessage
        from autogen_core import Image as AutoGenImage
        from PIL import Image as PILImage
        import io
        
        logger.info("开始调用视觉模型...")
        
        # 构建 AutoGen 消息格式
        content = []
        for msg in messages:
            if isinstance(msg.get("content"), list):
                for item in msg["content"]:
                    if item["type"] == "image_url":
                        # 提取 Base64 数据
                        url = item["image_url"]["url"]
                        if url.startswith("data:"):
                            # 解析 data URL，提取 base64 字符串
                            _, base64_data = url.split(",", 1)
                            logger.debug(f"Base64 数据长度: {len(base64_data)}, 前50字符: {base64_data[:50]}")
                            # 解码并通过 PIL 加载，确保格式正确
                            image_bytes = base64.b64decode(base64_data)
                            logger.debug(f"解码后字节数: {len(image_bytes)}, 前20字节: {image_bytes[:20]}")
                            # 检测图片格式
                            buffer = io.BytesIO(image_bytes)
                            try:
                                pil_image = PILImage.open(buffer)
                                pil_image.load()  # 确保图片完全加载
                                # 保存图片尺寸，用于 bbox 坐标转换
                                self._image_width, self._image_height = pil_image.size
                                logger.info(f"PIL 图片格式: {pil_image.format}, 尺寸: {pil_image.size}")
                            except Exception as pil_err:
                                logger.error(f"PIL 加载失败: {pil_err}, 尝试检测格式...")
                                # 尝试检测图片格式
                                buffer.seek(0)
                                header = buffer.read(20)
                                logger.error(f"图片头部字节: {header}")
                                raise
                            content.append(AutoGenImage(pil_image))
                        else:
                            content.append(AutoGenImage.from_uri(url))
                    elif item["type"] == "text":
                        content.append(item["text"])
        
        # 创建用户消息
        user_message = UserMessage(content=content, source="user")
        
        # 调用模型（设置较大的 max_tokens 以获取完整输出）
        logger.info("正在调用 LLM API...")
        try:
            # 使用额外参数设置 max_tokens
            response = await self._vision_client.create(
                [user_message],
                extra_create_args={"max_tokens": 8192}  # 增加输出 token 限制
            )
            logger.info(f"LLM 调用成功，响应类型: {type(response)}")
            logger.info(f"响应内容类型: {type(response.content)}")
            
            # 记录 token 用量
            if hasattr(response, 'usage') and response.usage:
                self._last_usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.prompt_tokens + response.usage.completion_tokens
                }
                logger.info(f"Token 用量: input={self._last_usage['input_tokens']}, output={self._last_usage['output_tokens']}, total={self._last_usage['total_tokens']}")
            else:
                self._last_usage = None
                logger.warning("响应中没有 usage 信息")
            
            # 提取文本响应
            result_text = response.content
            if isinstance(result_text, list):
                # 如果是列表，可能需要拼接
                logger.warning(f"响应内容是列表，长度: {len(result_text)}")
                result_text = "".join(str(item) for item in result_text)
            
            logger.info(f"LLM 返回内容长度: {len(result_text) if result_text else 0}")
            logger.debug(f"LLM 返回内容前500字符: {result_text[:500] if result_text else 'None'}")
            
            return result_text
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}", exc_info=True)
            raise
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析 LLM 响应
        
        Args:
            response: LLM 返回的文本
            
        Returns:
            解析后的字典
        """
        logger.info(f"开始解析 LLM 响应，原始长度: {len(response)}")
        logger.debug(f"原始响应前1000字符: {response[:1000]}")
        
        try:
            # 尝试提取 JSON 块
            json_str = self._extract_json(response)
            logger.info(f"提取的 JSON 长度: {len(json_str)}")
            logger.debug(f"提取的 JSON 前500字符: {json_str[:500]}")
            
            result = json.loads(json_str)
            logger.info(f"JSON 解析成功，元素数量（过滤前）: {len(result.get('elements', []))}")
            
            # 验证和规范化
            result = self._normalize_result(result)
            logger.info(f"规范化后元素数量（过滤后）: {len(result.get('elements', []))}")
            
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 完整解析失败: {e}，尝试部分解析...")
            
            # 尝试部分解析 - 逐个提取元素
            partial_result = self._try_partial_parse(response, str(e))
            if partial_result and partial_result.get("elements"):
                logger.info(f"部分解析成功，提取到 {len(partial_result['elements'])} 个元素")
                return partial_result
            
            logger.error(f"部分解析也失败")
            logger.error(f"原始响应: {response[:1000]}...")
            
            # 返回空结果，但包含详细错误信息
            return {
                "page_name": "解析失败",
                "page_type": "unknown",
                "page_description": f"LLM 返回格式错误: {str(e)}",
                "confidence_score": 0.0,
                "elements": [],
                "element_relations": [],
                "page_transitions": [],
                "raw_response": response[:2000],  # 保存前2000字符用于调试
                "parse_error": str(e)
            }
        except Exception as e:
            logger.error(f"解析过程发生未知错误: {e}", exc_info=True)
            return {
                "page_name": "解析异常",
                "page_type": "unknown",
                "page_description": f"解析异常: {str(e)}",
                "confidence_score": 0.0,
                "elements": [],
                "element_relations": [],
                "page_transitions": [],
                "raw_response": response[:2000] if response else "",
                "parse_error": str(e)
            }
    
    def _try_partial_parse(self, response: str, original_error: str) -> Dict[str, Any]:
        """
        尝试部分解析 - 当完整 JSON 解析失败时，尝试提取有效部分
        """
        import re
        
        result = {
            "page_name": "Unknown",
            "page_type": "unknown",
            "page_description": "",
            "confidence_score": 0.5,
            "elements": [],
            "element_relations": [],
            "page_transitions": [],
            "partial_parse": True,
            "original_error": original_error
        }
        
        try:
            # 提取页面名称
            page_name_match = re.search(r'"page_name"\s*:\s*"([^"]+)"', response)
            if page_name_match:
                result["page_name"] = page_name_match.group(1)
                logger.info(f"提取到页面名称: {result['page_name']}")
            
            # 提取页面类型
            page_type_match = re.search(r'"page_type"\s*:\s*"([^"]+)"', response)
            if page_type_match:
                result["page_type"] = page_type_match.group(1)
            
            # 提取页面描述
            page_desc_match = re.search(r'"page_description"\s*:\s*"([^"]+)"', response)
            if page_desc_match:
                result["page_description"] = page_desc_match.group(1)
            
            # 尝试提取 elements 数组中的每个元素
            # 找到 "elements": [ 的位置
            elements_start = response.find('"elements"')
            if elements_start == -1:
                logger.warning("未找到 elements 字段")
                return result
            
            # 找到数组开始位置
            array_start = response.find('[', elements_start)
            if array_start == -1:
                logger.warning("未找到 elements 数组")
                return result
            
            # 逐个提取元素对象
            elements = []
            pos = array_start + 1
            brace_count = 0
            element_start = -1
            
            while pos < len(response):
                char = response[pos]
                
                if char == '{':
                    if brace_count == 0:
                        element_start = pos
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and element_start != -1:
                        # 找到一个完整的元素
                        element_str = response[element_start:pos + 1]
                        try:
                            element = json.loads(element_str)
                            elements.append(element)
                            logger.debug(f"成功提取元素: {element.get('name', 'unnamed')}")
                        except json.JSONDecodeError:
                            # 单个元素解析失败，继续下一个
                            logger.debug(f"单个元素解析失败，跳过")
                        element_start = -1
                elif char == ']' and brace_count == 0:
                    # 数组结束
                    break
                
                pos += 1
            
            result["elements"] = elements
            logger.info(f"部分解析提取到 {len(elements)} 个元素")
            
            # 规范化结果
            result = self._normalize_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"部分解析过程出错: {e}")
            return result
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON"""
        # 尝试找到 JSON 块
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_str = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_str = text[start:end].strip()
        elif "{" in text:
            # 找到第一个 { 和最后一个 }
            start = text.find("{")
            end = text.rfind("}") + 1
            json_str = text[start:end]
        else:
            json_str = text
        
        # 尝试修复常见的 JSON 格式问题
        json_str = self._try_fix_json(json_str)
        
        return json_str
    
    def _try_fix_json(self, json_str: str) -> str:
        """尝试修复常见的 JSON 格式问题"""
        import re
        
        # 1. 移除可能的注释
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # 2. 修复尾部逗号问题 (trailing comma)
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # 3. 如果 JSON 被截断，尝试修复
        # 检查是否缺少闭合括号
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        if open_braces > close_braces or open_brackets > close_brackets:
            logger.warning(f"检测到 JSON 不完整: {{ {open_braces}/{close_braces}, [ {open_brackets}/{close_brackets}")
            
            # 尝试找到最后一个完整的元素
            # 方法：从后往前找最后一个 "}" 或 "]"，然后截断
            last_complete = max(
                json_str.rfind('}'),
                json_str.rfind(']')
            )
            
            if last_complete > 0:
                # 截取到最后一个完整的结构
                json_str = json_str[:last_complete + 1]
                
                # 重新计算并补齐括号
                open_braces = json_str.count('{')
                close_braces = json_str.count('}')
                open_brackets = json_str.count('[')
                close_brackets = json_str.count(']')
                
                # 补齐缺失的闭合括号
                json_str += ']' * (open_brackets - close_brackets)
                json_str += '}' * (open_braces - close_braces)
                
                logger.info(f"已尝试修复 JSON 结构")
        
        return json_str
    
    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """规范化分析结果"""
        # 确保必要字段存在
        result.setdefault("page_name", "Unknown")
        result.setdefault("page_type", "unknown")
        result.setdefault("page_description", "")
        result.setdefault("elements", [])
        result.setdefault("element_relations", [])
        result.setdefault("page_transitions", [])
        
        # 页面置信度处理
        # 1. 优先使用 AI 返回的置信度
        ai_confidence = result.get("confidence_score")
        if ai_confidence and isinstance(ai_confidence, (int, float)) and 0 < ai_confidence <= 1:
            result["confidence_score"] = float(ai_confidence)
            logger.info(f"使用 AI 返回的页面置信度: {ai_confidence}")
        else:
            # 2. 根据元素数量估算置信度
            element_count = len(result.get("elements", []))
            if element_count >= 20:
                result["confidence_score"] = 0.90
            elif element_count >= 10:
                result["confidence_score"] = 0.85
            elif element_count >= 5:
                result["confidence_score"] = 0.75
            elif element_count > 0:
                result["confidence_score"] = 0.60
            else:
                result["confidence_score"] = 0.0
            logger.info(f"根据元素数量({element_count})估算页面置信度: {result['confidence_score']}")
        
        original_count = len(result["elements"])
        logger.info(f"规范化前元素数量: {original_count}")
        
        # 过滤低置信度元素
        # 注意：如果元素没有 confidence_score，默认给 0.8（比阈值高）
        threshold = self.config.ANALYZER_CONFIDENCE_THRESHOLD
        result["elements"] = [
            e for e in result["elements"]
            if e.get("confidence_score", 0.8) >= threshold  # 默认 0.8，确保有效元素不被过滤
        ]
        
        filtered_count = original_count - len(result["elements"])
        if filtered_count > 0:
            logger.info(f"因置信度阈值({threshold})过滤掉 {filtered_count} 个元素")
        
        # 限制最大元素数
        max_elements = self.config.ANALYZER_MAX_ELEMENTS
        if len(result["elements"]) > max_elements:
            # 按置信度排序，保留最高的
            result["elements"] = sorted(
                result["elements"],
                key=lambda x: x.get("confidence_score", 0.8),
                reverse=True
            )[:max_elements]
            logger.info(f"元素数超过最大值({max_elements})，已截断")
        
        # 规范化每个元素
        for element in result["elements"]:
            element.setdefault("name", "")
            element.setdefault("type", "button")
            element.setdefault("text_content", "")
            element.setdefault("visual_description", {})
            element.setdefault("position", {})
            element.setdefault("relative_positions", [])
            element.setdefault("navigation", {"is_navigation": False})
            element.setdefault("midscene_operations", ["aiTap"])
            element.setdefault("test_scenarios", [])
            element.setdefault("test_priority", "medium")
            
            # 处理元素置信度
            elem_confidence = element.get("confidence_score")
            if not elem_confidence or not isinstance(elem_confidence, (int, float)) or elem_confidence <= 0:
                element["confidence_score"] = 0.85  # 默认置信度
            else:
                element["confidence_score"] = min(float(elem_confidence), 1.0)
            
            # 处理 midscene_locator：确保是中文自然语言描述
            locator = element.get("midscene_locator", "")
            if not locator or self._is_poor_locator(locator):
                # 自动生成一个合理的定位器
                locator = self._generate_locator(element)
            element["midscene_locator"] = locator
        
        logger.info(f"规范化后最终元素数量: {len(result['elements'])}")
        
        return result
    
    def build_element_model(
        self,
        element_data: Dict[str, Any],
        page_id: str
    ) -> Dict[str, Any]:
        """
        将分析结果转换为 PageElement 模型数据
        
        Args:
            element_data: 单个元素的分析数据
            page_id: 所属页面 ID
            
        Returns:
            适合创建 PageElement 的字典
        """
        # 兼容新旧两种格式
        visual = element_data.get("visual_description", {})
        position = element_data.get("position", {})
        navigation = element_data.get("navigation", {})
        
        # 简化格式：直接使用 description 字段
        description = element_data.get("description", "")
        if not description:
            description = self._build_short_description(element_data, position)
        
        # 提取 bbox 坐标（支持新旧格式和字符串格式）
        raw_bbox = element_data.get("bbox") or position.get("bbox", [])
        
        bbox = raw_bbox
        
        # 如果是字符串，尝试解析
        if isinstance(bbox, str):
            try:
                bbox = json.loads(bbox)
            except:
                bbox = None
        
        # 验证 bbox 格式
        if not bbox or not isinstance(bbox, list) or len(bbox) != 4:
            logger.warning(f"无效 bbox 格式: {raw_bbox} -> 设为 None")
            bbox = None
        else:
            # 确保所有值都是数字
            try:
                bbox = [float(v) for v in bbox]
                
                # 判断 bbox 格式并转换为百分比
                # 如果任何值 > 100，说明是像素坐标
                # 注意：有些 LLM 返回的像素值可能刚好 <= 100（如小图标），需要更智能判断
                is_pixel_format = any(v > 100 for v in bbox)
                
                # 额外检查：如果所有值都很小（< 5）且 width+height 占比不合理，也可能是像素
                # 或者：如果 left+width > 100 或 top+height > 100，说明不是有效百分比
                left_v, top_v, w_v, h_v = bbox
                if not is_pixel_format:
                    # 检查百分比合理性：left+width 应该 <= 100，top+height 应该 <= 100
                    if left_v + w_v > 105 or top_v + h_v > 105:  # 容差 5%
                        is_pixel_format = True
                
                if is_pixel_format:
                    # 使用实际截图尺寸（如果有），否则使用默认值
                    device_w = getattr(self, '_image_width', None) or 1080
                    device_h = getattr(self, '_image_height', None) or 2400
                    
                    # 判断是 [left, top, right, bottom] 还是 [left, top, width, height]
                    left, top, v3, v4 = bbox
                    
                    # 如果 v3 > left 且 v4 > top，很可能是 [left, top, right, bottom] 格式
                    if v3 > left and v4 > top:
                        # [left, top, right, bottom] -> [left%, top%, width%, height%]
                        width_px = v3 - left
                        height_px = v4 - top
                    else:
                        # 已经是 [left, top, width, height] 像素格式
                        width_px = v3
                        height_px = v4
                    
                    # 转换为百分比
                    bbox = [
                        round((left / device_w) * 100, 2),
                        round((top / device_h) * 100, 2),
                        round((width_px / device_w) * 100, 2),
                        round((height_px / device_h) * 100, 2)
                    ]
                    logger.debug(f"像素 bbox 转换为百分比: {raw_bbox} -> {bbox}")
                else:
                    logger.debug(f"bbox 已是百分比格式: {bbox}")
                    
            except Exception as e:
                logger.warning(f"bbox 数值解析失败: {raw_bbox}, 错误: {e}")
                bbox = None
        
        # 简化格式：直接使用 midscene_locator
        locator = element_data.get("midscene_locator", description)
        
        # 支持新格式的 area 和 is_navigation 字段
        area = element_data.get("area", "") or position.get("area", "")
        is_nav = element_data.get("is_navigation", False) or (navigation.get("is_navigation", False) if navigation else False)
        target_page = element_data.get("target_page", "") or (navigation.get("target_page", "") if navigation else "")
        
        return {
            "page_id": page_id,
            "element_name": element_data.get("name", ""),
            "element_type": element_data.get("type", "button"),
            "text_content": element_data.get("text_content", ""),
            "description": description,
            "visual_description": self._build_visual_description(visual) if visual else description,
            "midscene_locator": locator,
            "position_area": area,
            "position_in_container": position.get("position_in_container", ""),
            "bbox": bbox,
            "relative_positions": element_data.get("relative_positions", []),
            "is_navigation": is_nav,
            "target_page_name": target_page,
            "navigation_description": navigation.get("description", "") if navigation else "",
            "icon_description": visual.get("icon", "") if visual else "",
            "text_style": {"description": visual.get("text", "")} if visual else {},
            "background_style": {"description": visual.get("background", "")} if visual else {},
            "midscene_operations": element_data.get("midscene_operations", ["aiTap"]),
            "test_scenarios": element_data.get("test_scenarios", []),
            "functionality": element_data.get("name", ""),
            "interaction_state": "clickable",
            "confidence_score": element_data.get("confidence_score", 0.8),
            "is_testable": True,
            "test_priority": element_data.get("test_priority", "medium"),
        }
    
    def _is_poor_locator(self, locator: str) -> bool:
        """检查定位器是否质量较差"""
        if not locator:
            return True
        
        locator_lower = locator.lower().strip()
        
        # 太短的定位器
        if len(locator) < 3:
            return True
        
        # 纯英文编号/ID 类型
        poor_patterns = [
            'button', 'icon', 'text', 'image', 'link', 'input',
            'element', 'item', 'btn', 'img', 'txt'
        ]
        
        # 如果定位器只是纯英文单词（无中文），且在差模式列表中
        if locator_lower in poor_patterns:
            return True
        
        # 带数字后缀的编号（如 button_1, icon_2）
        import re
        if re.match(r'^[a-z_]+[_\d]+$', locator_lower):
            return True
        
        return False
    
    def _generate_locator(self, element: Dict[str, Any]) -> str:
        """为元素生成合理的 Midscene 定位器"""
        parts = []
        
        # 1. 位置信息
        area = element.get("area", "")
        area_map = {
            "顶部": "页面顶部",
            "中部": "页面中部",
            "底部": "页面底部"
        }
        if area and area in area_map:
            parts.append(area_map[area])
        
        # 2. 元素类型描述
        type_desc = {
            "button": "按钮",
            "icon_button": "图标按钮",
            "tab": "Tab",
            "card": "卡片",
            "text_input": "输入框",
            "link": "链接",
            "switch": "开关",
            "list_item": "列表项",
            "banner": "Banner"
        }
        elem_type = element.get("type", "button")
        
        # 3. 文字内容
        text = element.get("text_content", "")
        name = element.get("name", "")
        description = element.get("description", "")
        
        # 组合定位器
        left_quote = "\u201c"  # 中文左引号 "
        right_quote = "\u201d"  # 中文右引号 "
        
        if text:
            # 有文字的元素：使用 "位置 + 文字 + 类型"
            type_name = type_desc.get(elem_type, "元素")
            if parts:
                return f"{parts[0]}的{left_quote}{text}{right_quote}{type_name}"
            else:
                return f"{left_quote}{text}{right_quote}{type_name}"
        elif name:
            # 无文字但有名称：使用 "位置 + 名称"
            if parts:
                return f"{parts[0]}的{name}"
            else:
                return name
        elif description:
            # 使用描述
            if parts:
                return f"{parts[0]}的{description}"
            else:
                return description
        else:
            # 兜底：使用类型 + 位置
            type_name = type_desc.get(elem_type, "元素")
            if parts:
                return f"{parts[0]}的{type_name}"
            else:
                return type_name
    
    def _build_short_description(
        self,
        element: Dict[str, Any],
        position: Dict[str, Any]
    ) -> str:
        """构建简短描述"""
        parts = []
        
        if position.get("container"):
            parts.append(position["container"])
        if position.get("area"):
            parts.append(f"{position['area']}的")
        
        parts.append(element.get("name", "元素"))
        
        if element.get("text_content"):
            parts.append(f"（{element['text_content']}）")
        
        return "".join(parts)
    
    def _build_visual_description(self, visual: Dict[str, Any]) -> str:
        """构建详细视觉描述"""
        parts = []
        
        if visual.get("icon"):
            parts.append(visual["icon"])
        if visual.get("text"):
            parts.append(visual["text"])
        if visual.get("background"):
            parts.append(f"背景：{visual['background']}")
        if visual.get("size"):
            parts.append(f"大小：{visual['size']}")
        
        return "，".join(parts) if parts else ""
