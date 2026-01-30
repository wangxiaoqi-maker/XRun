# AI 教学模式 - App 页面知识库构建技术方案

> 版本：v1.0  
> 日期：2026-01-30  
> 作者：AI Assistant

---

## 一、需求概述

| 项目 | 内容 |
|------|------|
| **目标** | 在 UI 用例编辑页面增加「AI 教学模式」，支持截取投屏画面发送给视觉大模型分析，构建 App 页面元素知识库 |
| **核心价值** | 为 MidScene.js 自动化用例生成提供元素定位参考，通过语义匹配实现智能用例生成 |
| **平台支持** | Android + iOS |

---

## 二、技术选型

### 2.1 核心组件选型

| 组件 | 选型 | 理由 |
|------|------|------|
| **Agent 框架** | AutoGen | 复用现有 `llm/client.py` 封装，支持多智能体协作 |
| **视觉模型** | qwen-vl / gpt-4v | 已在 `MODELS` 中预置，支持多模态图像理解 |
| **后端框架** | FastAPI | 异步支持，与现有架构一致 |
| **关系型数据库** | MySQL | 存储结构化元素数据，支持复杂查询 |
| **向量数据库** | Milvus | 高性能向量检索，支持元数据过滤，生产级稳定性 |
| **Embedding 模型** | 可配置（预留入口） | 支持 OpenAI / 通义千问 / BGE 等多种模型 |
| **ORM** | SQLAlchemy Async | 参考项目已验证，支持异步操作 |
| **前端** | Vue 3 + Element Plus | 与现有 `CaseEditorView.vue` 无缝集成 |

### 2.2 Embedding 模型配置（预留入口）

系统支持多种 Embedding 模型，通过配置切换：

| 模型 | 维度 | 优点 | 适用场景 |
|------|------|------|----------|
| `text-embedding-3-small` | 1536 | OpenAI 官方，效果好 | 通用场景 |
| `text-embedding-3-large` | 3072 | 精度更高 | 高精度要求 |
| `text-embedding-ada-002` | 1536 | 成本低 | 成本敏感 |
| `bge-base-zh-v1.5` | 768 | 中文优化，本地部署 | 私有化部署 |
| `text-embedding-v3` | 1024 | 通义千问，国内访问快 | 国内环境 |

**配置示例**：

```python
# config.py
class EmbeddingConfig(BaseSettings):
    EMBEDDING_PROVIDER: str = "openai"           # openai / dashscope / local
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536              # 向量维度，需与模型匹配
    EMBEDDING_API_KEY: Optional[str] = None      # API Key（从环境变量读取）
    EMBEDDING_BASE_URL: Optional[str] = None     # 自定义 API 地址
```

---

## 三、系统架构

### 3.1 整体架构图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                               前端 (Vue 3)                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│  CaseEditorView.vue                                                           │
│  ├── [🎓 教学模式] 开关                                                        │
│  ├── [✨ AI 分析当前页] 按钮 ──────────────────┐                                │
│  ├── DeviceMirror 组件（投屏 + 截图能力）         │                                │
│  └── PageKnowledgePanel（展示已分析元素）         │                                │
└───────────────────────────────────────────────┼──────────────────────────────┘
                                                │ POST /api/ai/analyze-page
                                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              后端 (FastAPI)                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│  api/page_analysis.py                                                         │
│  ├── POST /analyze-page        截图分析入口                                    │
│  ├── POST /search-elements     语义搜索元素 ◄─── 向量检索                       │
│  ├── GET  /pages               获取 App 页面列表                               │
│  └── GET  /app-map             获取 App 页面地图                               │
├──────────────────────────────────────────────────────────────────────────────┤
│  services/page_analyzer_service.py                                            │
│  ├── analyze_screenshot()      调用视觉模型                                    │
│  ├── generate_embeddings()     生成元素向量 ◄─── Embedding 模型                 │
│  └── save_to_knowledge_base()  存入双库                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│  agents/                                                                      │
│  ├── PageAnalyzerAgent         页面分析智能体                                   │
│  └── PageStorageAgent          知识库存储智能体                                 │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│   视觉大模型         │ │   关系型数据库    │ │   向量数据库         │
│   (qwen-vl/gpt-4v)  │ │   (MySQL)        │ │   (Milvus)          │
│                     │ │                  │ │                     │
│ 输入：App 截图       │ │ 存储：           │ │ 存储：               │
│ 输出：元素 JSON      │ │ - App 信息       │ │ - 元素描述向量       │
│                     │ │ - 页面分析结果   │ │ - 元数据过滤         │
│                     │ │ - 页面元素       │ │                     │
└─────────────────────┘ └─────────────────┘ └─────────────────────┘
```

### 3.2 数据流程图

```
用户点击 [AI 分析当前页]
        │
        ▼
┌───────────────────┐
│ 1. 截取投屏画面    │ ──► Canvas.toDataURL() → Base64
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│ 2. 发送到后端      │ ──► POST /api/ai/analyze-page
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│ 3. 调用视觉模型    │ ──► qwen-vl 分析截图
└───────┬───────────┘     返回结构化 JSON
        │
        ▼
┌───────────────────┐
│ 4. 生成 Embedding │ ──► 对每个元素的 description 生成向量
└───────┬───────────┘
        │
        ├─────────────────────┐
        ▼                     ▼
┌───────────────────┐ ┌───────────────────┐
│ 5a. 存入关系型DB   │ │ 5b. 存入向量DB    │
│ (结构化元素数据)   │ │ (元素描述向量)    │
│ + screenshot_hash │ │                   │
└───────────────────┘ └───────────────────┘
        │
        ▼
┌───────────────────┐
│ 6. 返回分析结果    │ ──► 前端展示元素列表
└───────────────────┘
```

### 3.3 语义搜索流程

```
用户输入：「点击登录按钮」
        │
        ▼
┌───────────────────┐
│ 1. 生成查询向量    │ ──► Embedding("点击登录按钮")
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│ 2. 向量相似度搜索  │ ──► Chroma.query(embedding, top_k=5)
└───────┬───────────┘     可选：按 app_name, page_type 过滤
        │
        ▼
┌───────────────────┐
│ 3. 返回匹配元素    │ ──► [
└───────────────────┘       {"name": "登录按钮", "score": 0.95, ...},
                            {"name": "确认登录", "score": 0.87, ...}
                          ]
```

---

## 四、数据模型设计

### 4.1 ER 关系图

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────────┐
│   AppInfo   │ 1───N │   PageAnalysis   │ 1───N │   PageElement   │
│             │       │                  │       │                 │
│ id (PK)     │       │ id (PK)          │       │ id (PK)         │
│ app_name    │       │ app_id (FK)      │       │ page_id (FK)    │
│ package_name│       │ page_name        │       │ element_name    │
│ platform    │       │ page_type        │       │ element_type    │
│ version     │       │ page_description │       │ text_content    │
│ created_at  │       │ screenshot_hash  │       │ description     │ ◄─ 同步到向量库
│ updated_at  │       │ confidence_score │       │ visual_desc     │ ◄─ 详细视觉描述
└─────────────┘       │ raw_response     │       │ position_info   │
                      │ created_at       │       │ relative_pos    │ ◄─ 相对位置关系
                      └──────────────────┘       │ midscene_locator│ ◄─ MidScene 定位器
                               │                 │ target_page_id  │ ◄─ 跳转目标页面
                               │                 │ is_navigation   │
                               │                 └─────────────────┘
                               │                          │
                      ┌────────┴────────┐        ┌────────┴────────┐
                      │ PageTransition  │        │ ElementRelation │
                      │                 │        │                 │
                      │ from_page_id    │        │ source_id (FK)  │
                      │ to_page_id      │        │ target_id (FK)  │
                      │ trigger_element │        │ relation_type   │ ◄─ 右方/左方/上方/下方
                      │ transition_type │        │ description     │
                      └─────────────────┘        └─────────────────┘
```

### 4.2 关系型数据库表结构

#### 表 1: `app_info` - 应用信息

```python
class AppInfo(Base):
    """应用信息表"""
    __tablename__ = 'app_info'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    app_name = Column(String(100), nullable=False, index=True)           # 应用名称
    package_name = Column(String(200), unique=True)                      # 包名
    platform = Column(String(20), nullable=False)                        # android / ios
    version = Column(String(50))                                         # App 版本号
    icon_path = Column(String(500))                                      # 图标路径
    description = Column(Text)                                           # 应用描述
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    pages = relationship("PageAnalysis", back_populates="app", cascade="all, delete-orphan")
```

#### 表 2: `page_analysis` - 页面分析结果

```python
class PageAnalysis(Base):
    """页面分析结果表"""
    __tablename__ = 'page_analysis'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    app_id = Column(String(36), ForeignKey('app_info.id', ondelete='CASCADE'), nullable=False)
    
    # 页面信息
    page_name = Column(String(200), nullable=False, index=True)          # AI 生成的页面名称
    page_type = Column(String(50), default='unknown')                    # login/home/list/detail/form
    page_description = Column(Text)                                      # 页面功能描述
    
    # 截图信息（不存储截图文件，只保留 hash 用于去重）
    screenshot_hash = Column(String(64), index=True)                     # MD5 用于去重判断
    device_udid = Column(String(100))                                    # 设备 UDID
    device_resolution = Column(String(50))                               # 分辨率（仅记录）
    
    # 分析结果
    elements_count = Column(Integer, default=0)
    confidence_score = Column(DECIMAL(5, 2), default=0.0)
    raw_response = Column(JSON)                                          # LLM 原始返回
    analysis_metadata = Column(JSON)
    processing_time = Column(DECIMAL(10, 3))                             # 处理耗时（秒）
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    app = relationship("AppInfo", back_populates="pages")
    elements = relationship("PageElement", back_populates="page", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_page_app_name', 'app_id', 'page_name'),
        Index('idx_page_type', 'page_type'),
        Index('idx_page_hash', 'screenshot_hash'),
    )
```

#### 表 3: `page_element` - 页面元素

```python
class PageElement(Base):
    """页面元素表 - 核心知识库数据"""
    __tablename__ = 'page_element'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String(36), ForeignKey('page_analysis.id', ondelete='CASCADE'), nullable=False)
    
    # ========== 元素基本信息 ==========
    element_name = Column(String(200), nullable=False)                   # 转账、扫一扫、付款码
    element_type = Column(String(50), nullable=False, index=True)        # button/icon/link/input
    text_content = Column(String(500))                                   # 元素上的文字
    
    # ========== 详细视觉描述（核心：用于 MidScene 定位）==========
    # 简短描述（同步到向量库）
    description = Column(Text, nullable=False)                           # "首页底部的转账按钮"
    
    # 详细视觉描述（icon 颜色、字体、形状等）
    visual_description = Column(Text)                                    # "蓝色的手机 icon，下方是黑色「手机充值」文字"
    
    # 完整 MidScene 定位器（组合所有信息生成的最佳定位描述）
    midscene_locator = Column(Text)                                      # "首页九宫格中，蓝色手机图标下方写着「手机充值」的入口"
    
    # ========== 位置关系 ==========
    # 绝对位置
    position_area = Column(String(100))                                  # 顶部/底部/中央/左上/右下
    position_in_container = Column(String(200))                          # 九宫格第二行第一个 / 导航栏最右侧
    
    # 相对位置关系（JSON 数组，存储与其他元素的关系）
    relative_positions = Column(JSON)                                    # [{"target": "付款码", "relation": "右方"}, ...]
    
    # ========== 导航跳转关系 ==========
    is_navigation = Column(Boolean, default=False)                       # 是否是导航元素（可跳转）
    target_page_id = Column(String(36), ForeignKey('page_analysis.id'))  # 跳转目标页面 ID
    target_page_name = Column(String(200))                               # 跳转目标页面名称（冗余，方便查询）
    navigation_description = Column(Text)                                # "点击后跳转到转账页面"
    
    # ========== 视觉特征详情 ==========
    icon_description = Column(Text)                                      # icon 描述：蓝色手机图标 / 绿色扫码图标
    text_style = Column(JSON)                                            # {"color": "黑色", "size": "小", "weight": "normal"}
    background_style = Column(JSON)                                      # {"color": "白色", "shape": "圆形"}
    
    # ========== 测试相关 ==========
    midscene_operations = Column(JSON)                                   # ["aiTap", "aiAssert"]
    test_scenarios = Column(JSON)                                        # ["点击进入转账页面", "验证转账入口存在"]
    functionality = Column(String(500))                                  # 功能说明
    interaction_state = Column(String(50), default='clickable')
    
    # ========== 质量评估 ==========
    confidence_score = Column(DECIMAL(5, 2), default=0.0)
    is_testable = Column(Boolean, default=True)
    test_priority = Column(String(20), default='medium')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    page = relationship("PageAnalysis", back_populates="elements", foreign_keys=[page_id])
    target_page = relationship("PageAnalysis", foreign_keys=[target_page_id])
    
    __table_args__ = (
        Index('idx_element_type', 'element_type'),
        Index('idx_element_testable', 'is_testable'),
        Index('idx_element_navigation', 'is_navigation'),
        Index('idx_element_target_page', 'target_page_id'),
    )
```

#### 表 4: `element_relation` - 元素空间关系

```python
class ElementRelation(Base):
    """元素空间关系表 - 存储元素之间的位置关系"""
    __tablename__ = 'element_relation'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关系双方
    source_element_id = Column(String(36), ForeignKey('page_element.id', ondelete='CASCADE'), nullable=False)
    target_element_id = Column(String(36), ForeignKey('page_element.id', ondelete='CASCADE'), nullable=False)
    
    # 关系类型
    relation_type = Column(String(50), nullable=False)                   # right_of/left_of/above/below/inside/beside
    
    # 关系描述（自然语言）
    relation_description = Column(Text)                                  # "扫一扫在付款码的右方"
    
    # 距离描述
    distance = Column(String(50))                                        # adjacent/near/far
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    source_element = relationship("PageElement", foreign_keys=[source_element_id])
    target_element = relationship("PageElement", foreign_keys=[target_element_id])
    
    __table_args__ = (
        Index('idx_relation_source', 'source_element_id'),
        Index('idx_relation_target', 'target_element_id'),
        Index('idx_relation_type', 'relation_type'),
    )
```

#### 关系类型枚举

```python
class RelationType(str, Enum):
    """元素空间关系类型"""
    RIGHT_OF = "right_of"        # 在...右方
    LEFT_OF = "left_of"          # 在...左方
    ABOVE = "above"              # 在...上方
    BELOW = "below"              # 在...下方
    INSIDE = "inside"            # 在...内部
    BESIDE = "beside"            # 在...旁边
    SAME_ROW = "same_row"        # 同一行
    SAME_COLUMN = "same_column"  # 同一列
```

#### 表 5: `page_transition` - 页面跳转关系

```python
class PageTransition(Base):
    """页面跳转关系表 - 构建 App 导航地图"""
    __tablename__ = 'page_transition'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 页面关系
    from_page_id = Column(String(36), ForeignKey('page_analysis.id'), nullable=False)
    to_page_id = Column(String(36), ForeignKey('page_analysis.id'), nullable=False)
    from_page_name = Column(String(200))                                 # 冗余，方便查询
    to_page_name = Column(String(200))
    
    # 触发元素
    trigger_element_id = Column(String(36), ForeignKey('page_element.id'))
    trigger_element_name = Column(String(200))                           # 转账 / 扫一扫
    trigger_element_locator = Column(Text)                               # MidScene 定位描述
    
    # 跳转类型
    transition_type = Column(String(50))                                 # push/pop/replace/modal/tab
    
    # 跳转描述
    transition_description = Column(Text)                                # "在首页点击转账按钮，跳转到转账页面"
    
    # 验证已确认（用户手动确认跳转关系）
    is_confirmed = Column(Boolean, default=False)
    confirmed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    from_page = relationship("PageAnalysis", foreign_keys=[from_page_id])
    to_page = relationship("PageAnalysis", foreign_keys=[to_page_id])
    trigger_element = relationship("PageElement", foreign_keys=[trigger_element_id])
    
    __table_args__ = (
        Index('idx_transition_from', 'from_page_id'),
        Index('idx_transition_to', 'to_page_id'),
        Index('idx_transition_trigger', 'trigger_element_id'),
        # 唯一约束：同一触发元素只能有一个跳转目标
        UniqueConstraint('trigger_element_id', name='uq_trigger_element'),
    )
```

### 4.3 向量数据库结构（Milvus）

#### Collection Schema 定义

```python
from pymilvus import MilvusClient, DataType

# 创建 Milvus 客户端
client = MilvusClient(
    uri="http://localhost:19530",
    token="root:Milvus"
)

# 创建 Schema
schema = MilvusClient.create_schema(
    auto_id=False,
    enable_dynamic_field=True,  # 支持动态字段扩展
)

# 添加字段
schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=36, is_primary=True)
schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=1536)  # 维度可配置
schema.add_field(field_name="description", datatype=DataType.VARCHAR, max_length=2000)
schema.add_field(field_name="app_name", datatype=DataType.VARCHAR, max_length=100)
schema.add_field(field_name="page_id", datatype=DataType.VARCHAR, max_length=36)
schema.add_field(field_name="page_name", datatype=DataType.VARCHAR, max_length=200)
schema.add_field(field_name="page_type", datatype=DataType.VARCHAR, max_length=50)
schema.add_field(field_name="element_name", datatype=DataType.VARCHAR, max_length=200)
schema.add_field(field_name="element_type", datatype=DataType.VARCHAR, max_length=50)
schema.add_field(field_name="platform", datatype=DataType.VARCHAR, max_length=20)
schema.add_field(field_name="is_testable", datatype=DataType.BOOL)
schema.add_field(field_name="test_priority", datatype=DataType.VARCHAR, max_length=20)

# 创建索引
index_params = client.prepare_index_params()
index_params.add_index(
    field_name="embedding",
    index_type="AUTOINDEX",
    metric_type="COSINE"  # 余弦相似度
)
index_params.add_index(field_name="app_name", index_type="AUTOINDEX")
index_params.add_index(field_name="element_type", index_type="AUTOINDEX")

# 创建 Collection
client.create_collection(
    collection_name="page_elements",
    schema=schema,
    index_params=index_params
)
```

#### 数据结构示例

```python
# 插入数据示例
# 注意：embedding 的文本来源是 midscene_locator（最详细的定位描述）
data = {
    "id": "elem_001",
    "embedding": [0.1, 0.2, ...],              # 1536 维向量（由 midscene_locator 生成）
    
    # 用于向量搜索后返回的信息
    "description": "首页九宫格中第一行第一个，蓝色扫码图标下方写着「扫一扫」的入口",
    "element_name": "扫一扫",
    "element_type": "icon_button",
    "text_content": "扫一扫",
    
    # 视觉描述（用于搜索结果展示和 MidScene 脚本生成）
    "visual_desc": "蓝色的扫码图标，下方有黑色「扫一扫」文字",
    
    # 位置关系（用于上下文理解）
    "position_area": "首页九宫格功能区",
    "relative_positions": "[{\"target\": \"付款码\", \"relation\": \"left_of\"}]",
    
    # 跳转信息
    "target_page_name": "扫码页面",
    "is_navigation": True,
    
    # 过滤条件
    "app_name": "支付宝",
    "page_id": "page_001",
    "page_name": "首页",
    "platform": "android",
    "is_testable": True,
}

client.insert(collection_name="page_elements", data=[data])
```

#### 语义搜索增强

搜索时，可以使用更丰富的上下文来提高匹配精度：

```python
# 示例 1：直接搜索
results = await vector_service.search(
    query="点击扫一扫",
    top_k=5
)

# 示例 2：带上下文搜索（更精确）
results = await vector_service.search(
    query="首页付款码左边的扫一扫入口",
    top_k=5,
    filter_expr='app_name == "支付宝" and page_name == "首页"'
)

# 示例 3：按跳转目标搜索
results = await vector_service.search(
    query="进入转账页面的入口",
    top_k=5,
    filter_expr='target_page_name == "转账页面"'
)
```

### 4.4 元素类型枚举

```python
class ElementType(str, Enum):
    """页面元素类型"""
    # 按钮类
    BUTTON = "button"
    SUBMIT_BUTTON = "submit_button"
    ICON_BUTTON = "icon_button"
    
    # 输入类
    TEXT_INPUT = "text_input"
    PASSWORD_INPUT = "password_input"
    SEARCH_INPUT = "search_input"
    TEXTAREA = "textarea"
    
    # 选择类
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SWITCH = "switch"
    PICKER = "picker"
    
    # 导航类
    LINK = "link"
    TAB = "tab"
    MENU_ITEM = "menu_item"
    LIST_ITEM = "list_item"
    
    # 特殊类
    IMAGE = "image"
    UPLOAD = "upload"
    SLIDER = "slider"
```

---

## 五、API 设计

### 5.1 页面分析 API

```python
# POST /api/ai/analyze-page
@router.post("/analyze-page", response_model=PageAnalyzeResponse)
async def analyze_page(request: PageAnalyzeRequest) -> PageAnalyzeResponse:
    """分析页面截图，提取可测试元素并存入知识库"""
    pass

class PageAnalyzeRequest(BaseModel):
    image_data: str                    # Base64 编码的截图
    app_name: str                      # 应用名称
    package_name: Optional[str]        # 包名（可选）
    platform: str                      # android / ios
    device_udid: Optional[str]         # 设备 UDID
    device_resolution: Optional[str]   # 分辨率
    context_hint: Optional[str]        # 上下文提示

class PageAnalyzeResponse(BaseModel):
    page_id: str                       # 页面 ID
    page_name: str                     # AI 生成的页面名称
    page_type: str                     # 页面类型
    page_description: str              # 页面描述
    elements: List[ElementInfo]        # 元素列表
    elements_count: int                # 元素数量
    confidence_score: float            # 置信度
    is_new_page: bool                  # 是否新页面
    processing_time: float             # 处理耗时
```

### 5.2 语义搜索 API（核心）

```python
# POST /api/ai/search-elements
@router.post("/search-elements", response_model=ElementSearchResponse)
async def search_elements(request: ElementSearchRequest) -> ElementSearchResponse:
    """语义搜索页面元素 - 用于智能用例生成"""
    pass

class ElementSearchRequest(BaseModel):
    query: str                         # 搜索文本，如"点击登录按钮"
    app_name: Optional[str]            # 限定 App
    page_name: Optional[str]           # 限定页面
    element_type: Optional[str]        # 限定元素类型
    testable_only: bool = True         # 只返回可测试元素
    top_k: int = 5                     # 返回数量

class ElementSearchResponse(BaseModel):
    query: str
    results: List[ElementMatchResult]
    total_searched: int                # 搜索的向量总数
    search_time: float                 # 搜索耗时

class ElementMatchResult(BaseModel):
    element_id: str
    element_name: str
    element_type: str
    description: str                   # MidScene 定位描述
    similarity_score: float            # 相似度分数 0-1
    app_name: str
    page_name: str
    midscene_operations: List[str]     # 支持的操作
```

### 5.3 知识库查询 API

```python
# GET /api/ai/pages
@router.get("/pages", response_model=List[PageSummary])
async def get_pages(
    app_name: Optional[str] = None,
    platform: Optional[str] = None,
    page_type: Optional[str] = None,
    limit: int = 50
) -> List[PageSummary]:
    """获取页面列表"""
    pass

# GET /api/ai/pages/{page_id}/elements
@router.get("/pages/{page_id}/elements", response_model=List[ElementInfo])
async def get_page_elements(
    page_id: str,
    element_type: Optional[str] = None,
    testable_only: bool = True
) -> List[ElementInfo]:
    """获取页面的所有元素"""
    pass

# GET /api/ai/app-map
@router.get("/app-map", response_model=AppMapResponse)
async def get_app_map(app_name: str) -> AppMapResponse:
    """获取 App 页面地图（页面关系图）"""
    pass

# GET /api/ai/stats
@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_stats() -> KnowledgeBaseStats:
    """获取知识库统计信息"""
    pass

class KnowledgeBaseStats(BaseModel):
    total_apps: int
    total_pages: int
    total_elements: int
    elements_by_type: Dict[str, int]
    recent_analyses: List[RecentAnalysis]
```

---

## 六、AutoGen 智能体设计

### 6.1 智能体架构

```python
# agents/page_analyzer_agent.py
from autogen_core import RoutedAgent, type_subscription, message_handler
from llm.client import get_model

@type_subscription(topic_type="page_analyzer")
class PageAnalyzerAgent(RoutedAgent):
    """页面分析智能体 - 使用视觉模型分析 App 截图"""
    
    def __init__(self):
        super().__init__("page_analyzer")
        self.vision_client = get_model("qwenvl")
    
    @message_handler
    async def handle_analyze_request(self, message: PageAnalyzeRequest, ctx) -> None:
        # 1. 构建多模态 Prompt
        prompt = self._build_analysis_prompt(message)
        
        # 2. 调用视觉模型
        response = await self._call_vision_model(message.image_data, prompt)
        
        # 3. 解析 JSON 结果
        page_info, elements = self._parse_response(response)
        
        # 4. 发送到存储智能体
        await self.publish_message(
            PageStorageRequest(page_info=page_info, elements=elements),
            topic_id=TopicId(type="page_storage", source=self.id.key)
        )


@type_subscription(topic_type="page_storage")
class PageStorageAgent(RoutedAgent):
    """知识库存储智能体 - 同时写入 MySQL 和 Milvus"""
    
    def __init__(self):
        super().__init__("page_storage")
        from services.embedding_service import VectorService
        self.vector_service = VectorService()
    
    @message_handler
    async def handle_storage_request(self, message: PageStorageRequest, ctx) -> None:
        # 1. 存入 MySQL（关系型数据）
        page_id = await self._save_to_mysql(message.page_info, message.elements)
        
        # 2. 批量存入 Milvus（向量数据）
        elements_for_vector = [
            {
                "id": element.id,
                "description": element.description,
                "metadata": {
                    "app_name": message.page_info.app_name,
                    "page_id": page_id,
                    "page_name": message.page_info.page_name,
                    "element_name": element.name,
                    "element_type": element.type,
                    "platform": message.page_info.platform,
                    "is_testable": element.is_testable
                }
            }
            for element in message.elements
        ]
        await self.vector_service.add_elements_batch(elements_for_vector)
        
        # 3. 发送完成消息
        await self.send_response(f"存储完成：{len(message.elements)} 个元素")
```

### 6.2 视觉模型 Prompt

```python
MOBILE_UI_ANALYSIS_PROMPT = """
你是移动端 UI 元素识别专家，分析 App 界面截图。
你的任务是提取所有可交互元素，并详细描述它们的视觉特征、位置关系和跳转关系。
分析结果将用于 MidScene.js 自动化测试框架，因此描述必须足够详细以便精确定位。

## 核心任务
1. 识别页面名称和类型
2. 提取所有可交互元素
3. **详细描述每个元素的视觉特征**（icon 颜色、字体、形状）
4. **描述元素之间的空间位置关系**（A 在 B 的右方）
5. **识别可能的页面跳转关系**（点击 A 跳转到 B 页面）

## 识别的元素类型
1. **入口类**：九宫格入口、功能入口（如：扫一扫、付款码、转账、充值）
2. **按钮类**：提交、确认、取消、登录、搜索按钮
3. **输入类**：搜索框、文本输入框
4. **导航类**：Tab、底部导航、返回按钮、菜单项
5. **列表项**：可点击的列表 cell
6. **开关类**：开关、复选框

## 输出格式（严格 JSON）

```json
{
  "page_name": "支付宝首页",
  "page_type": "home",
  "page_description": "支付宝主页，包含扫一扫、付款码、转账等核心功能入口",
  
  "elements": [
    {
      "id": "elem_001",
      "name": "扫一扫",
      "type": "icon_button",
      "text_content": "扫一扫",
      
      "visual_description": {
        "icon": "蓝色的扫码图标，四角有扫描框样式",
        "text": "图标下方有黑色「扫一扫」文字",
        "background": "白色圆形背景",
        "size": "中等大小"
      },
      
      "position": {
        "area": "页面上方",
        "container": "首页九宫格功能区",
        "position_in_container": "第一行第一个"
      },
      
      "relative_positions": [
        {"target_name": "付款码", "relation": "left_of", "description": "在付款码的左边"},
        {"target_name": "出行", "relation": "above", "description": "在出行的上方"}
      ],
      
      "navigation": {
        "is_navigation": true,
        "target_page": "扫码页面",
        "description": "点击后进入扫码页面，可扫描二维码或条形码"
      },
      
      "midscene_locator": "首页九宫格中第一行第一个，蓝色扫码图标下方写着「扫一扫」的入口",
      
      "midscene_operations": ["aiTap", "aiAssert"],
      "test_scenarios": ["点击进入扫码页面", "验证扫一扫入口存在"],
      "confidence_score": 0.98,
      "test_priority": "high"
    },
    {
      "id": "elem_002",
      "name": "付款码",
      "type": "icon_button",
      "text_content": "付款码",
      
      "visual_description": {
        "icon": "蓝色的条形码图标",
        "text": "图标下方有黑色「付款码」文字",
        "background": "白色圆形背景",
        "size": "中等大小"
      },
      
      "position": {
        "area": "页面上方",
        "container": "首页九宫格功能区",
        "position_in_container": "第一行第二个"
      },
      
      "relative_positions": [
        {"target_name": "扫一扫", "relation": "right_of", "description": "在扫一扫的右边"},
        {"target_name": "出行", "relation": "above", "description": "在出行的上方"}
      ],
      
      "navigation": {
        "is_navigation": true,
        "target_page": "付款码页面",
        "description": "点击后显示付款二维码和条形码"
      },
      
      "midscene_locator": "首页九宫格中扫一扫右边，蓝色条形码图标下方写着「付款码」的入口",
      
      "midscene_operations": ["aiTap", "aiAssert"],
      "test_scenarios": ["点击显示付款码", "验证付款码入口存在"],
      "confidence_score": 0.98,
      "test_priority": "high"
    },
    {
      "id": "elem_003",
      "name": "手机充值",
      "type": "icon_button",
      "text_content": "手机充值",
      
      "visual_description": {
        "icon": "蓝色的手机图标，屏幕上有信号标志",
        "text": "图标下方有黑色「手机充值」文字",
        "background": "白色圆形背景",
        "size": "中等大小"
      },
      
      "position": {
        "area": "页面中部",
        "container": "首页九宫格功能区",
        "position_in_container": "第二行第三个"
      },
      
      "relative_positions": [
        {"target_name": "转账", "relation": "right_of", "description": "在转账的右边"},
        {"target_name": "生活缴费", "relation": "left_of", "description": "在生活缴费的左边"}
      ],
      
      "navigation": {
        "is_navigation": true,
        "target_page": "手机充值页面",
        "description": "点击后进入手机充值页面"
      },
      
      "midscene_locator": "首页九宫格中，蓝色手机图标下方写着「手机充值」的入口",
      
      "midscene_operations": ["aiTap"],
      "test_scenarios": ["点击进入充值页面"],
      "confidence_score": 0.95,
      "test_priority": "medium"
    }
  ],
  
  "element_relations": [
    {"source": "扫一扫", "target": "付款码", "relation": "left_of", "description": "扫一扫在付款码的左边"},
    {"source": "付款码", "target": "扫一扫", "relation": "right_of", "description": "付款码在扫一扫的右边"},
    {"source": "转账", "target": "手机充值", "relation": "left_of", "description": "转账在手机充值的左边"}
  ],
  
  "page_transitions": [
    {"trigger": "扫一扫", "target_page": "扫码页面", "description": "点击扫一扫进入扫码页面"},
    {"trigger": "付款码", "target_page": "付款码页面", "description": "点击付款码显示付款二维码"},
    {"trigger": "转账", "target_page": "转账页面", "description": "点击转账进入转账页面"},
    {"trigger": "手机充值", "target_page": "手机充值页面", "description": "点击手机充值进入充值页面"}
  ]
}
```

## MidScene 定位器撰写规则（重要）

生成的 `midscene_locator` 应该：
1. **包含容器信息**：在哪个区域/模块里
2. **包含位置信息**：第几行第几个、左边/右边
3. **包含视觉特征**：颜色、图标形状
4. **包含文字内容**：图标下方的文字

示例：
- ✅ "首页九宫格中第一行第一个，蓝色扫码图标下方写着「扫一扫」的入口"
- ✅ "转账按钮右边，蓝色手机图标下方写着「手机充值」的入口"
- ❌ "手机充值按钮"（太简单，无法精确定位）

## 元素关系描述规则

必须描述元素之间的空间关系：
- A 在 B 的 **左边/右边/上方/下方**
- A 和 B 在 **同一行**
- A 在 B **旁边**

开始分析：
"""
```

---

## 七、向量服务实现

### 7.1 配置类

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class EmbeddingConfig(BaseSettings):
    """Embedding 模型配置 - 预留多种模型入口"""
    
    # Embedding 提供商：openai / dashscope / local
    EMBEDDING_PROVIDER: str = "openai"
    
    # 模型名称
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # 向量维度（需与模型匹配）
    EMBEDDING_DIMENSION: int = 1536
    
    # API 配置（从环境变量读取）
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None
    
    class Config:
        env_prefix = ""
        env_file = ".env"


class MilvusConfig(BaseSettings):
    """Milvus 向量数据库配置"""
    
    MILVUS_URI: str = "http://localhost:19530"
    MILVUS_TOKEN: str = "root:Milvus"
    MILVUS_DATABASE: str = "xrun_knowledge"
    MILVUS_COLLECTION: str = "page_elements"
    
    class Config:
        env_prefix = ""
        env_file = ".env"
```

### 7.2 Embedding 服务（多模型支持）

```python
# services/embedding_service.py
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from pymilvus import MilvusClient
from loguru import logger

from .config import EmbeddingConfig, MilvusConfig


class BaseEmbeddingProvider(ABC):
    """Embedding 提供商基类"""
    
    @abstractmethod
    async def generate(self, text: str) -> List[float]:
        """生成文本向量"""
        pass
    
    @abstractmethod
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成向量"""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI Embedding 提供商"""
    
    def __init__(self, config: EmbeddingConfig):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=config.EMBEDDING_API_KEY,
            base_url=config.EMBEDDING_BASE_URL
        )
        self.model = config.EMBEDDING_MODEL
    
    async def generate(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]


class DashScopeEmbeddingProvider(BaseEmbeddingProvider):
    """通义千问 Embedding 提供商"""
    
    def __init__(self, config: EmbeddingConfig):
        import dashscope
        dashscope.api_key = config.EMBEDDING_API_KEY
        self.model = config.EMBEDDING_MODEL or "text-embedding-v3"
    
    async def generate(self, text: str) -> List[float]:
        import dashscope
        from dashscope import TextEmbedding
        response = TextEmbedding.call(
            model=self.model,
            input=text
        )
        return response.output['embeddings'][0]['embedding']
    
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        import dashscope
        from dashscope import TextEmbedding
        response = TextEmbedding.call(
            model=self.model,
            input=texts
        )
        return [item['embedding'] for item in response.output['embeddings']]


def get_embedding_provider(config: EmbeddingConfig) -> BaseEmbeddingProvider:
    """工厂方法：根据配置获取 Embedding 提供商"""
    providers = {
        "openai": OpenAIEmbeddingProvider,
        "dashscope": DashScopeEmbeddingProvider,
    }
    provider_class = providers.get(config.EMBEDDING_PROVIDER)
    if not provider_class:
        raise ValueError(f"不支持的 Embedding 提供商: {config.EMBEDDING_PROVIDER}")
    return provider_class(config)


class VectorService:
    """向量服务 - 基于 Milvus"""
    
    def __init__(self):
        self.embedding_config = EmbeddingConfig()
        self.milvus_config = MilvusConfig()
        
        # 初始化 Embedding 提供商
        self.embedding_provider = get_embedding_provider(self.embedding_config)
        
        # 初始化 Milvus 客户端
        self.client = MilvusClient(
            uri=self.milvus_config.MILVUS_URI,
            token=self.milvus_config.MILVUS_TOKEN
        )
        
        # 确保 Collection 存在
        self._ensure_collection()
    
    def _ensure_collection(self):
        """确保 Collection 存在"""
        from pymilvus import DataType
        
        collection_name = self.milvus_config.MILVUS_COLLECTION
        
        if self.client.has_collection(collection_name):
            return
        
        # 创建 Schema
        schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=True)
        schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=36, is_primary=True)
        schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, 
                        dim=self.embedding_config.EMBEDDING_DIMENSION)
        schema.add_field(field_name="description", datatype=DataType.VARCHAR, max_length=2000)
        schema.add_field(field_name="app_name", datatype=DataType.VARCHAR, max_length=100)
        schema.add_field(field_name="page_id", datatype=DataType.VARCHAR, max_length=36)
        schema.add_field(field_name="page_name", datatype=DataType.VARCHAR, max_length=200)
        schema.add_field(field_name="element_name", datatype=DataType.VARCHAR, max_length=200)
        schema.add_field(field_name="element_type", datatype=DataType.VARCHAR, max_length=50)
        schema.add_field(field_name="platform", datatype=DataType.VARCHAR, max_length=20)
        schema.add_field(field_name="is_testable", datatype=DataType.BOOL)
        
        # 创建索引
        index_params = self.client.prepare_index_params()
        index_params.add_index(field_name="embedding", index_type="AUTOINDEX", metric_type="COSINE")
        index_params.add_index(field_name="app_name", index_type="AUTOINDEX")
        index_params.add_index(field_name="element_type", index_type="AUTOINDEX")
        
        # 创建 Collection
        self.client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params
        )
        logger.info(f"创建 Milvus Collection: {collection_name}")
    
    async def add_element(self, element_id: str, description: str, metadata: Dict[str, Any]):
        """添加元素到向量库"""
        embedding = await self.embedding_provider.generate(description)
        
        data = {
            "id": element_id,
            "embedding": embedding,
            "description": description,
            **metadata
        }
        
        self.client.insert(
            collection_name=self.milvus_config.MILVUS_COLLECTION,
            data=[data]
        )
        logger.debug(f"添加元素到向量库: {element_id}")
    
    async def add_elements_batch(self, elements: List[Dict[str, Any]]):
        """批量添加元素"""
        descriptions = [e["description"] for e in elements]
        embeddings = await self.embedding_provider.generate_batch(descriptions)
        
        data = []
        for i, element in enumerate(elements):
            data.append({
                "id": element["id"],
                "embedding": embeddings[i],
                "description": element["description"],
                **element.get("metadata", {})
            })
        
        self.client.insert(
            collection_name=self.milvus_config.MILVUS_COLLECTION,
            data=data
        )
        logger.info(f"批量添加 {len(data)} 个元素到向量库")
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        语义搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filter_expr: 过滤表达式，如 'app_name == "微信" and element_type == "button"'
        
        Returns:
            匹配结果列表
        """
        query_embedding = await self.embedding_provider.generate(query)
        
        results = self.client.search(
            collection_name=self.milvus_config.MILVUS_COLLECTION,
            data=[query_embedding],
            limit=top_k,
            filter=filter_expr,
            output_fields=["id", "description", "app_name", "page_name", 
                          "element_name", "element_type", "platform", "is_testable"]
        )
        
        matches = []
        for hit in results[0]:
            matches.append({
                "id": hit["id"],
                "description": hit["entity"]["description"],
                "similarity_score": hit["distance"],  # COSINE 返回的是相似度
                "app_name": hit["entity"]["app_name"],
                "page_name": hit["entity"]["page_name"],
                "element_name": hit["entity"]["element_name"],
                "element_type": hit["entity"]["element_type"],
                "platform": hit["entity"]["platform"],
                "is_testable": hit["entity"]["is_testable"]
            })
        
        return matches
    
    async def delete_by_page(self, page_id: str):
        """删除页面的所有元素向量"""
        self.client.delete(
            collection_name=self.milvus_config.MILVUS_COLLECTION,
            filter=f'page_id == "{page_id}"'
        )
        logger.info(f"删除页面向量: {page_id}")
    
    async def delete_by_ids(self, ids: List[str]):
        """按 ID 删除元素"""
        self.client.delete(
            collection_name=self.milvus_config.MILVUS_COLLECTION,
            ids=ids
        )
```

### 7.3 使用示例

```python
# 初始化服务
vector_service = VectorService()

# 添加元素
await vector_service.add_element(
    element_id="elem_001",
    description="页面底部的蓝色登录按钮",
    metadata={
        "app_name": "微信",
        "page_id": "page_001",
        "page_name": "登录页",
        "element_name": "登录按钮",
        "element_type": "button",
        "platform": "android",
        "is_testable": True
    }
)

# 语义搜索（带过滤）
results = await vector_service.search(
    query="点击登录",
    top_k=5,
    filter_expr='app_name == "微信" and element_type == "button"'
)

# 结果示例
[
    {
        "id": "elem_001",
        "description": "页面底部的蓝色登录按钮",
        "similarity_score": 0.92,
        "app_name": "微信",
        "page_name": "登录页",
        "element_name": "登录按钮",
        "element_type": "button",
        ...
    }
]
```

---

## 八、前端实现

### 8.1 CaseEditorView.vue 改动

```vue
<template>
  <!-- 教学模式开关 -->
  <div class="teaching-mode-bar" v-if="mirrorRef?.connected">
    <el-switch 
      v-model="isTeachingMode" 
      active-text="教学模式"
      inactive-text=""
      @change="onTeachingModeChange"
    />
    
    <!-- 教学模式工具栏 -->
    <div v-if="isTeachingMode" class="teaching-toolbar">
      <el-button 
        type="primary" 
        :loading="analyzing"
        @click="analyzeCurrentPage"
      >
        <el-icon><MagicStick /></el-icon>
        AI 分析当前页
      </el-button>
      
      <el-button @click="showKnowledgeBase">
        <el-icon><Collection /></el-icon>
        页面知识库
      </el-button>
      
      <el-button @click="showSemanticSearch">
        <el-icon><Search /></el-icon>
        智能搜索
      </el-button>
    </div>
  </div>
  
  <!-- 分析结果抽屉 -->
  <el-drawer 
    v-model="showAnalysisDrawer" 
    title="页面元素分析" 
    size="45%"
    direction="rtl"
  >
    <PageElementsPanel 
      :page="currentAnalysis"
      :elements="analyzedElements"
      @use-element="insertElementToStep"
    />
  </el-drawer>
  
  <!-- 语义搜索弹窗 -->
  <el-dialog v-model="showSearchDialog" title="智能元素搜索" width="600px">
    <el-input 
      v-model="searchQuery"
      placeholder="输入自然语言描述，如：点击登录按钮"
      @keyup.enter="doSemanticSearch"
    >
      <template #append>
        <el-button @click="doSemanticSearch" :loading="searching">
          搜索
        </el-button>
      </template>
    </el-input>
    
    <div class="search-results" v-if="searchResults.length">
      <div 
        v-for="result in searchResults" 
        :key="result.element_id"
        class="result-item"
        @click="insertElementToStep(result)"
      >
        <div class="result-header">
          <span class="element-name">{{ result.element_name }}</span>
          <el-tag size="small">{{ result.element_type }}</el-tag>
          <span class="score">{{ (result.similarity_score * 100).toFixed(0) }}%</span>
        </div>
        <div class="result-desc">{{ result.description }}</div>
        <div class="result-meta">
          {{ result.app_name }} / {{ result.page_name }}
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
const isTeachingMode = ref(false)
const analyzing = ref(false)
const analyzedElements = ref([])
const searchQuery = ref('')
const searchResults = ref([])

async function analyzeCurrentPage() {
  analyzing.value = true
  try {
    const imageData = await mirrorRef.value.captureScreenshot()
    
    const result = await api.post('/ai/analyze-page', {
      image_data: imageData,
      app_name: currentApp.value,
      platform: selectedDevice.value.platform,
      device_udid: selectedDevice.value.udId
    })
    
    analyzedElements.value = result.data.elements
    showAnalysisDrawer.value = true
    
    ElMessage.success(`识别到 ${result.data.elements.length} 个可测试元素`)
  } finally {
    analyzing.value = false
  }
}

async function doSemanticSearch() {
  searching.value = true
  try {
    const result = await api.post('/ai/search-elements', {
      query: searchQuery.value,
      app_name: currentApp.value,
      top_k: 10
    })
    searchResults.value = result.data.results
  } finally {
    searching.value = false
  }
}

function insertElementToStep(element) {
  const step = {
    type: element.midscene_operations?.[0] || 'aiTap',
    target: element.description,
    description: `操作${element.element_name}`
  }
  caseForm.steps.push(step)
  ElMessage.success('已添加步骤')
}
</script>
```

### 8.2 DeviceMirror 截图能力

```typescript
// 在 DeviceMirror.vue 中新增
async function captureScreenshot(): Promise<string> {
  const canvas = document.createElement('canvas')
  const img = screenRef.value  // <img> 元素
  
  canvas.width = img.naturalWidth
  canvas.height = img.naturalHeight
  
  const ctx = canvas.getContext('2d')
  ctx.drawImage(img, 0, 0)
  
  return canvas.toDataURL('image/png')
}

defineExpose({ captureScreenshot, ... })
```

---

## 九、目录结构

```
backend/apps/ui_automation/
├── agents/                      # AutoGen 智能体
│   ├── __init__.py
│   ├── base.py                  # 智能体基类
│   ├── page_analyzer_agent.py   # 页面分析智能体
│   └── page_storage_agent.py    # 知识库存储智能体
│
├── api/
│   ├── ...
│   └── page_analysis.py         # 页面分析 API
│
├── models/
│   ├── ...
│   └── page_knowledge.py        # 知识库数据模型
│
├── repositories/                # 数据访问层
│   ├── __init__.py
│   ├── base.py
│   └── page_analysis_repo.py
│
├── schemas/
│   ├── ...
│   └── page_analysis.py         # 请求/响应模型
│
└── services/
    ├── ...
    ├── page_analyzer_service.py # 分析服务
    └── embedding_service.py     # 向量服务

# 数据存储说明：
# - MySQL: 关系型数据（App 信息、页面分析、元素结构化数据）
# - Milvus: 向量数据（元素描述 Embedding，支持语义检索）
# - 两者通过 element_id 关联，保持数据一致性
```

---

## 十、MidScene 脚本生成示例

### 10.1 无知识库 vs 有知识库对比

#### 用户需求
> "打开支付宝，点击手机充值，充值100元"

#### 无知识库生成（模糊）

```yaml
- aiTap: "手机充值"        # 可能找不到，描述太简单
- aiInput: "100"
- aiTap: "确认充值"
```

#### 有知识库生成（精确）

```yaml
# 从知识库检索到的元素信息：
# - midscene_locator: "首页九宫格中，蓝色手机图标下方写着「手机充值」的入口"
# - position: "转账右边"
# - target_page: "手机充值页面"

- aiTap: "首页九宫格中，蓝色手机图标下方写着「手机充值」的入口"
- aiWait: 1000
- aiInput("充值金额输入框"): "100"
- aiTap: "页面底部的蓝色确认充值按钮"
```

### 10.2 知识库辅助生成流程

```
用户输入测试需求
        │
        ▼
┌───────────────────┐
│ 1. 解析测试步骤    │ ──► ["打开支付宝", "点击手机充值", "充值100元"]
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│ 2. 语义搜索知识库  │ ──► 搜索 "手机充值" 相关元素
└───────┬───────────┘
        │
        ▼
┌───────────────────┐     返回匹配结果：
│ 3. 获取元素详情    │ ──► {
└───────┬───────────┘       "element_name": "手机充值",
        │                    "midscene_locator": "首页九宫格中，蓝色手机图标...",
        │                    "relative_positions": [{"target": "转账", "relation": "right_of"}],
        │                    "target_page": "手机充值页面"
        │                  }
        ▼
┌───────────────────┐
│ 4. 生成 MidScene  │ ──► 使用 midscene_locator 作为定位描述
│    脚本           │
└───────────────────┘
```

### 10.3 生成 Prompt 示例

```python
def build_midscene_generation_prompt(test_requirement: str, matched_elements: List[dict]) -> str:
    """构建 MidScene 脚本生成 Prompt"""
    
    # 将知识库匹配的元素信息注入 Prompt
    elements_context = "\n".join([
        f"""
元素: {elem['element_name']}
精确定位: {elem['midscene_locator']}
视觉描述: {elem['visual_desc']}
位置关系: {elem['relative_positions']}
跳转页面: {elem.get('target_page_name', '无')}
支持操作: {elem['midscene_operations']}
"""
        for elem in matched_elements
    ])
    
    return f"""
你是一个 MidScene.js 自动化测试脚本生成专家。

## 测试需求
{test_requirement}

## 可用元素（来自知识库，请使用精确定位描述）
{elements_context}

## 生成规则
1. 使用知识库中的 `精确定位` 作为 aiTap/aiInput 的参数
2. 如果知识库中没有匹配的元素，使用合理的自然语言描述
3. 在页面跳转后添加适当的等待时间
4. 添加必要的断言验证

## 输出格式（YAML）
请生成可直接执行的 MidScene YAML 脚本。
"""
```

---

## 十一、技术依赖

### 11.1 新增 Python 依赖

```txt
# requirements.txt 新增
pymilvus>=2.4.0              # Milvus Python SDK
openai>=1.0.0                # OpenAI Embedding API
dashscope>=1.14.0            # 通义千问 Embedding API（可选）
Pillow>=10.0.0               # 图像处理
aiomysql>=0.2.0              # MySQL 异步驱动
```

### 11.2 环境变量

```bash
# .env 新增

# ========== Embedding 配置 ==========
EMBEDDING_PROVIDER=openai                # 提供商：openai / dashscope / local
EMBEDDING_MODEL=text-embedding-3-small   # 模型名称
EMBEDDING_DIMENSION=1536                 # 向量维度
EMBEDDING_API_KEY=sk-xxx                 # API Key

# ========== Milvus 配置 ==========
MILVUS_URI=http://localhost:19530        # Milvus 地址
MILVUS_TOKEN=root:Milvus                 # 认证 Token
MILVUS_DATABASE=xrun_knowledge           # 数据库名
MILVUS_COLLECTION=page_elements          # Collection 名

# ========== MySQL 配置 ==========
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=xrun
```

---

## 十二、后续扩展规划

| 阶段 | 功能 | 描述 | 优先级 |
|------|------|------|--------|
| **Phase 1** | 页面分析 + 双库存储 | 截图分析、元素识别、关系库+向量库 | P0 |
| **Phase 2** | 语义搜索 + 步骤插入 | 自然语言搜索元素，一键插入用例步骤 | P0 |
| **Phase 3** | 页面跳转关系 | 记录页面间跳转，构建导航地图 | P1 |
| **Phase 4** | 智能用例生成 | 基于知识库 + LLM 自动生成完整用例 | P1 |
| **Phase 5** | 元素变更检测 | 对比历史分析，发现 UI 变更并告警 | P2 |
| **Phase 6** | 跨版本追踪 | 追踪元素在不同 App 版本的变化 | P2 |
| **Phase 7** | 多 App 知识融合 | 跨 App 相似元素识别，复用测试模式 | P3 |

---

## 十三、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 视觉模型识别不准 | 元素遗漏或错误 | 人工校验 + 置信度阈值 + 多次分析取最佳 |
| 向量检索效果差 | 匹配不到正确元素 | 优化 Prompt、增加备选描述、调整 Embedding 模型 |
| 截图重复分析 | 浪费资源 | 基于 screenshot_hash 去重 |
| 数据库膨胀 | 存储压力 | 定期清理低置信度数据 |

---

## 十四、验收标准

- [ ] 教学模式开关正常工作
- [ ] 截图分析成功率 > 90%
- [ ] 元素识别准确率 > 85%
- [ ] 语义搜索 Top-5 命中率 > 80%
- [ ] 单次分析耗时 < 10 秒
- [ ] 语义搜索耗时 < 500ms

---

**文档结束**
