# App 知识图谱设计文档

## 一、目标

1. **支撑 Midscene 脚本生成**：提供精准的元素定位描述
2. **构建 App 导航图谱**：记录页面间的跳转关系
3. **支持智能路径规划**：给定目标，自动规划操作路径

---

## 二、当前字段的局限性

```json
{
  "page_name": "我的_翼支付",
  "elements": [{
    "midscene_locator": "左上角圆形头像",
    "is_navigation": false,
    "target_page": ""  // ❌ 单次截图无法知道跳转目标
  }]
}
```

**问题**：
- 单次分析无法建立跳转关系（需要"操作"来发现）
- 缺少页面唯一标识（page_signature）
- 缺少知识图谱的"边"（Edge）

---

## 三、知识图谱数据模型

### 3.1 页面节点 (Page Node)

```python
class PageNode(Base):
    """页面节点 - 知识图谱的顶点"""
    __tablename__ = "knowledge_pages"
    
    id = Column(String(36), primary_key=True)  # UUID
    app_id = Column(String(100), nullable=False)  # 关联的 App
    
    # 页面标识
    page_name = Column(String(200))  # AI 识别的页面名称
    page_type = Column(String(50))   # home|profile|list|detail|form|settings
    page_signature = Column(String(64))  # 页面特征签名（用于去重）
    
    # 页面内容
    page_description = Column(Text)
    screenshot_hash = Column(String(64))  # 截图的 hash（用于存储）
    
    # 元素数据（JSON）
    elements = Column(JSON)  # 该页面的所有元素
    
    # 元信息
    depth = Column(Integer, default=0)  # 从首页的深度
    visit_count = Column(Integer, default=1)  # 被访问次数
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### 3.2 页面跳转边 (Page Transition Edge)

```python
class PageTransition(Base):
    """页面跳转 - 知识图谱的边"""
    __tablename__ = "knowledge_transitions"
    
    id = Column(String(36), primary_key=True)
    app_id = Column(String(100), nullable=False)
    
    # 跳转关系
    from_page_id = Column(String(36), ForeignKey("knowledge_pages.id"))
    to_page_id = Column(String(36), ForeignKey("knowledge_pages.id"))
    
    # 触发条件
    trigger_element_name = Column(String(200))  # 触发元素的名称
    trigger_element_locator = Column(Text)  # Midscene 定位描述
    action_type = Column(String(50))  # click|swipe|long_press|input
    action_params = Column(JSON)  # 操作参数（如输入的文本）
    
    # 跳转类型
    transition_type = Column(String(50))  # navigate|modal|drawer|back
    is_back_navigation = Column(Boolean, default=False)  # 是否是返回操作
    
    # 统计
    success_count = Column(Integer, default=1)
    fail_count = Column(Integer, default=0)
    avg_response_time_ms = Column(Integer)
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### 3.3 元素详情 (Element Detail)

```python
class ElementDetail(Base):
    """元素详情 - 增强的元素信息"""
    __tablename__ = "knowledge_elements"
    
    id = Column(String(36), primary_key=True)
    page_id = Column(String(36), ForeignKey("knowledge_pages.id"))
    
    # 基础信息
    name = Column(String(200))
    element_type = Column(String(50))
    text_content = Column(String(500))
    description = Column(Text)
    
    # 定位信息（多种定位方式，提高脚本健壮性）
    bbox = Column(JSON)  # [left, top, width, height]
    midscene_locator = Column(Text)  # 自然语言定位
    xpath = Column(Text)  # XPath（如果有 UI Hierarchy）
    accessibility_id = Column(String(200))  # 无障碍 ID
    
    # 交互信息
    is_clickable = Column(Boolean, default=True)
    is_scrollable = Column(Boolean, default=False)
    is_editable = Column(Boolean, default=False)
    
    # 导航信息（通过探索发现）
    leads_to_page_id = Column(String(36))  # 点击后跳转的页面
    leads_to_page_name = Column(String(200))  # 跳转页面名称
    
    # 业务信息
    semantic_role = Column(String(100))  # 语义角色：登录按钮、返回首页、查看余额
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

---

## 四、页面签名算法（去重）

单次 AI 分析可能多次分析同一个页面，需要识别"是否是同一个页面"：

```python
def generate_page_signature(page_data: dict) -> str:
    """
    生成页面特征签名，用于判断是否是同一个页面
    
    策略：
    1. 页面类型 + 页面名称
    2. 元素的结构特征（类型分布、数量）
    3. 关键元素的文本（如标题）
    """
    signature_parts = [
        page_data.get("page_type", ""),
        page_data.get("page_name", ""),
    ]
    
    # 元素结构特征
    elements = page_data.get("elements", [])
    type_counts = {}
    key_texts = []
    
    for elem in elements:
        elem_type = elem.get("type", "unknown")
        type_counts[elem_type] = type_counts.get(elem_type, 0) + 1
        
        # 收集关键文本（标题、Tab 文字）
        if elem_type in ["nav_item", "tab", "title"]:
            if elem.get("text_content"):
                key_texts.append(elem["text_content"])
    
    # 排序确保一致性
    signature_parts.append(json.dumps(sorted(type_counts.items())))
    signature_parts.append("|".join(sorted(key_texts)[:5]))  # 最多取5个关键文本
    
    # 生成 hash
    signature_str = "::".join(signature_parts)
    return hashlib.md5(signature_str.encode()).hexdigest()
```

---

## 五、知识图谱探索服务

### 5.1 探索模式

```python
class ExplorationMode(Enum):
    MANUAL = "manual"      # 手动探索：用户操作 -> 记录跳转
    SEMI_AUTO = "semi_auto"  # 半自动：AI 建议 -> 用户确认
    FULL_AUTO = "full_auto"  # 全自动：AI 自动点击探索
```

### 5.2 探索服务

```python
class KnowledgeGraphExplorationService:
    """知识图谱探索服务"""
    
    async def start_exploration(self, app_id: str, device_udid: str, mode: ExplorationMode):
        """开始探索 App"""
        pass
    
    async def record_transition(
        self,
        from_page_id: str,
        to_page_data: dict,
        trigger_element: dict,
        action: dict
    ) -> PageTransition:
        """
        记录一次页面跳转
        
        流程：
        1. 对 to_page_data 生成签名
        2. 查找是否已存在该页面
        3. 如果不存在，创建新页面节点
        4. 创建/更新跳转边
        5. 更新触发元素的 leads_to_page_id
        """
        # 生成目标页面签名
        to_signature = generate_page_signature(to_page_data)
        
        # 查找已存在的页面
        existing_page = await self.find_page_by_signature(app_id, to_signature)
        
        if existing_page:
            to_page_id = existing_page.id
            # 更新访问次数
            existing_page.visit_count += 1
        else:
            # 创建新页面
            to_page = await self.create_page_node(app_id, to_page_data, to_signature)
            to_page_id = to_page.id
        
        # 创建跳转边
        transition = await self.create_or_update_transition(
            from_page_id=from_page_id,
            to_page_id=to_page_id,
            trigger_element=trigger_element,
            action=action
        )
        
        return transition
    
    async def auto_explore(self, app_id: str, device_udid: str, max_depth: int = 3):
        """
        全自动探索模式
        
        策略：
        1. 从当前页面开始
        2. 识别所有可点击元素
        3. 按优先级排序：未探索的导航元素 > Tab > 按钮 > 列表项
        4. 依次点击，记录跳转
        5. 使用返回键回到上一页
        6. 重复直到所有元素都探索过或达到深度限制
        """
        pass
    
    async def find_path(self, app_id: str, from_page: str, to_page: str) -> List[dict]:
        """
        查找从 A 页面到 B 页面的操作路径
        
        使用 BFS 在知识图谱中搜索最短路径
        """
        pass
```

---

## 六、增强的 AI 分析 Prompt

为了更好地支持知识图谱，需要让 AI 返回更多元素信息：

```python
ENHANCED_MOBILE_UI_ANALYSIS_PROMPT = """
你是移动端 UI 元素识别专家，你的分析结果将用于构建 App 知识图谱和自动化脚本。

## 输出格式
```json
{
  "page_name": "页面名称（如：我的-翼支付）",
  "page_type": "home|profile|list|detail|form|settings|login|search|result",
  "page_description": "页面功能的简短描述",
  
  "page_features": {
    "has_back_button": true,      // 是否有返回按钮
    "has_bottom_tabs": true,      // 是否有底部 Tab 栏
    "is_modal": false,            // 是否是弹窗/浮层
    "is_scrollable": true,        // 是否可滚动
    "title_text": "我的"          // 页面标题文字
  },
  
  "elements": [
    {
      "name": "元素语义名称",
      "type": "button|icon_button|link|tab|card|banner|text_input|switch|nav_item|list_item|back_button",
      "text_content": "元素文字",
      "description": "简短视觉描述",
      "bbox": [100, 200, 80, 40],
      "area": "header|content|footer|floating",
      
      // Midscene 定位（多种描述，提高健壮性）
      "midscene_locator": {
        "primary": "页面顶部的返回箭头图标",
        "alternative": "左上角的 < 按钮",
        "by_text": null,
        "by_position": "顶部导航栏最左侧"
      },
      
      // 交互信息
      "interaction": {
        "is_clickable": true,
        "is_scrollable": false,
        "is_editable": false,
        "likely_action": "navigate_back"  // 可能的操作效果
      },
      
      // 导航信息（基于视觉推断）
      "navigation_hint": {
        "likely_target": "上一页",         // 推测的跳转目标
        "confidence": 0.9,                 // 置信度
        "is_back": true                    // 是否是返回操作
      }
    }
  ]
}
```

## likely_action 枚举值
- navigate_back: 返回上一页
- navigate_to: 跳转到新页面
- open_modal: 打开弹窗
- close_modal: 关闭弹窗
- switch_tab: 切换 Tab
- toggle: 开关切换
- input: 输入文本
- scroll: 滚动
- unknown: 未知
"""
```

---

## 七、API 设计

### 7.1 探索相关 API

```python
# 开始探索会话
POST /api/knowledge/exploration/start
{
  "app_id": "com.example.app",
  "device_udid": "xxx",
  "mode": "manual"  // manual|semi_auto|full_auto
}

# 记录页面跳转（手动模式）
POST /api/knowledge/exploration/record-transition
{
  "session_id": "xxx",
  "from_page_id": "uuid",
  "trigger_element": {
    "name": "用户头像",
    "locator": "左上角圆形头像"
  },
  "action": {
    "type": "click"
  },
  "to_page_screenshot": "base64..."
}

# 查询页面间路径
GET /api/knowledge/path?app_id=xxx&from=首页&to=设置页
Response: {
  "path": [
    {"page": "首页", "action": "点击底部Tab'我的'"},
    {"page": "我的", "action": "点击右上角设置图标"},
    {"page": "设置页", "action": null}
  ],
  "total_steps": 2
}
```

### 7.2 知识图谱查询 API

```python
# 获取 App 知识图谱概览
GET /api/knowledge/graph/{app_id}
Response: {
  "pages": [...],
  "transitions": [...],
  "statistics": {
    "total_pages": 15,
    "total_transitions": 42,
    "coverage": 0.75  // 探索覆盖率
  }
}

# 获取页面详情
GET /api/knowledge/pages/{page_id}

# 获取元素详情
GET /api/knowledge/elements/{element_id}
```

---

## 八、Midscene 脚本生成

基于知识图谱，可以自动生成更健壮的 Midscene 脚本：

```python
async def generate_midscene_script(
    app_id: str,
    target_action: str,  # "打开设置页并关闭通知"
) -> str:
    """
    根据自然语言意图生成 Midscene 脚本
    
    1. 理解用户意图
    2. 查找知识图谱中的路径
    3. 生成操作序列
    """
    # 示例输出
    return '''
    await ai.aiAction('点击底部导航栏中的"我的"Tab');
    await ai.aiWaitFor('页面显示用户头像和余额信息');
    await ai.aiAction('点击右上角的设置图标');
    await ai.aiWaitFor('进入设置页面');
    await ai.aiAction('找到"通知设置"并点击');
    await ai.aiAction('关闭"接收通知"开关');
    '''
```

---

## 九、实施路线

### Phase 1: 基础设施（当前）
- [x] AI 页面分析
- [x] 元素识别和 bbox
- [ ] 页面签名算法
- [ ] 数据库模型

### Phase 2: 手动探索
- [ ] 探索会话管理
- [ ] 跳转记录 API
- [ ] 知识图谱存储

### Phase 3: 半自动探索
- [ ] AI 建议下一步操作
- [ ] 用户确认机制
- [ ] 批量探索

### Phase 4: 全自动探索
- [ ] 自动点击策略
- [ ] 异常处理（弹窗、登录）
- [ ] 探索覆盖率统计

### Phase 5: 智能脚本生成
- [ ] 意图理解
- [ ] 路径规划
- [ ] 脚本生成和优化

---

## 十、总结

当前的 AI 分析字段**不足以**构建完整的知识图谱，需要：

1. **增强元素信息**：添加 `interaction`、`navigation_hint` 等字段
2. **页面签名机制**：识别"同一个页面"
3. **跳转记录机制**：通过"操作 -> 观察"建立边
4. **探索服务**：支持手动/半自动/全自动探索模式
5. **路径查询**：基于图谱进行 BFS 搜索

**核心理念**：单次截图分析只能获得"节点"信息，"边"（跳转关系）必须通过**操作探索**来发现。
