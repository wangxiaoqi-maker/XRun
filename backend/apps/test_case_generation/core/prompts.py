"""Prompt 模板 - 测试方法差异化驱动"""

# testcase-generator skill 定义的测试类型枚举（12种）
TEST_TYPE_ENUM = [
    "功能", "兼容性", "易用性", "性能", "稳定性", "安全性",
    "可靠性", "效果(AI类、资源类)", "效果(硬件器件类)", "可维护性", "可移植性", "埋点",
]

# 优先级定义
PRIORITY_ENUM = ["P0", "P1", "P2", "P3", "P4", "P5"]

# Few-shot 示例：高质量用例示例（省 token 的关键）
FEW_SHOT_EXAMPLES = [
    {
        "name": "验证有效用户名和密码登录成功",
        "test_type": "功能",
        "priority": "P0",
        "preconditions": "已注册用户 test_user，密码 Test1234",
        "steps": "1. 输入用户名 test_user，输入密码 Test1234，点击登录。2. 验证跳转到首页并显示用户名",
        "expected": "1. 登录请求成功。2. 跳转到 /home 页面，顶部显示'欢迎，test_user'",
    },
    {
        "name": "验证用户名为空时登录失败",
        "test_type": "功能",
        "priority": "P2",
        "preconditions": "进入登录页",
        "steps": "1. 不输入用户名，输入密码 Test1234，点击登录。2. 验证提示'用户名不能为空'",
        "expected": "1. 登录请求被拒绝。2. 停留在登录页，用户名输入框下方显示红色提示'用户名不能为空'",
    },
    {
        "name": "验证密码长度边界值（8位）",
        "test_type": "功能",
        "priority": "P3",
        "preconditions": "已注册用户 test_user，密码 Test1234",
        "steps": "1. 输入用户名 test_user，输入8位密码 Test1234，点击登录。2. 验证登录成功",
        "expected": "1. 登录请求成功。2. 跳转到 /home 页面",
    },
]

def build_test_point_system_prompt() -> str:
    return """你是资深测试工程师，擅长从需求文档中提取测试点。

# 核心职责
1. 理解需求内容（包括文本和图片分析），分析功能和测试范围
2. 基于指定的测试方法提取测试点
3. 确保覆盖正常流程、异常流程、边界条件
4. 设置合理的优先级（P0 核心功能 / P1 重要功能 / P2 次要功能）

# 图片分析内容
文档中的图片（流程图、架构图、UI 截图、数据表结构等）已由视觉模型分析并转为文字描述，
标记为"## 图片内容分析"。你必须仔细阅读这些图片描述，从中提取额外的测试点：
- 流程图 → 提取流程分支、异常路径的测试点
- 架构图 → 提取接口交互、数据流转的测试点
- UI 截图 → 提取界面元素、交互逻辑的测试点
- 数据表/ER图 → 提取数据完整性、关联关系的测试点

# 测试场景矩阵
每个功能模块应覆盖：
- 正常流程：主要业务路径
- 异常流程：错误输入、权限不足、数据缺失
- 边界条件：极值、空值、最大长度
- 特殊场景：并发、超时、数据一致性"""


def build_test_point_user_prompt(
    parsed_content: str,
    rag_context: str = "",
    user_prompt: str = "",
    existing_coverage: dict = None,
    skill_prompt_block: str = "",
) -> str:
    coverage_info = ""
    if existing_coverage:
        total = existing_coverage.get("total_cases", 0)
        missing = existing_coverage.get("missing_scenarios", [])
        coverage_info = f"""
## 现有覆盖情况
已有 {total} 条用例。缺失场景：{', '.join(missing) if missing else '无'}
请重点补充缺失场景的测试点。
"""

    has_images = "图片内容分析" in parsed_content
    image_hint = """
注意：需求内容中包含"## 图片内容分析"，是文档中流程图、架构图等的文字描述。
图片中可能包含文本未提及的流程分支、异常路径、数据流转等信息，请一并纳入分析。
""" if has_images else ""

    return f"""请**严格基于以下需求内容**提取测试点。**禁止**添加需求文档中未提及的功能或场景。
{image_hint}
## 需求内容
{parsed_content}

{skill_prompt_block}

{f"## 知识库上下文{chr(10)}{rag_context}" if rag_context else ""}

{f"## 用户补充说明{chr(10)}{user_prompt}" if user_prompt else ""}

{coverage_info}

## 提取要求
- **只提取上述需求内容中明确提到或可直接推导的测试点**
- 不要凭空添加需求文档中不存在的功能模块
- 相同场景合并为一个测试点，不同场景各自独立
- 每个功能模块应覆盖正常、异常、边界场景

## 输出格式（严格 JSON）
{{
    "test_points": [
        {{
            "id": "TP-001",
            "title": "测试点标题",
            "description": "详细描述",
            "test_type": "functional|boundary|exception",
            "priority": "P0|P1|P2",
            "module": "所属模块",
            "source_ref": {{"page": 1, "section": "xxx"}}
        }}
    ]
}}"""


def build_test_case_system_prompt() -> str:
    return """你是资深测试用例编写工程师。根据测试点生成高质量测试用例。

核心要求：
1. 测试数据必须具体，不用占位符（如：test_user, 13800138000, 99.99）
2. 预期结果必须明确可验证（如：显示"欢迎，test_user"，而非"登录成功"）
3. 步骤与预期结果数量必须一致
4. 每个测试点生成 2-3 条用例即可，追求质量而非数量
5. 步骤描述简洁，每步一句话，不要冗长"""


def build_test_case_user_prompt(
    confirmed_points: list[dict],
    skill_prompt_block: str = "",
    requirement_context: str = "",
    all_points: list[dict] = None,
    rag_context: str = "",
) -> str:
    few_shot_block = "\n## 用例示例（严格按此风格生成）\n"
    for i, ex in enumerate(FEW_SHOT_EXAMPLES, 1):
        few_shot_block += f"""示例 {i}: [{ex['priority']}][{ex['test_type']}] {ex['name']}
[前置条件] {ex['preconditions']}
[测试步骤] {ex['steps']}
[预期结果] {ex['expected']}

"""

    points_block = ""
    for i, p in enumerate(confirmed_points, 1):
        tp_id = p.get('id', f'TP-{i:03d}')
        points_block += f"""
### 测试点 {tp_id}
- 标题: {p.get('title', '')}
- 优先级: {p.get('priority', 'P1')}
- 描述: {p.get('description', '')}
- 所属模块: {p.get('module', '未分类')}
"""

    req_block = ""
    if requirement_context:
        req_block = f"""
## 原始需求文档（参考上下文，用于理解业务细节）
{requirement_context}
"""

    all_points_block = ""
    if all_points and len(all_points) > len(confirmed_points):
        other_titles = [
            f"- {p.get('id', '')}: {p.get('title', '')}"
            for p in all_points
            if p.get('id') not in {cp.get('id') for cp in confirmed_points}
        ]
        if other_titles:
            all_points_block = f"""
## 其他批次的测试点（仅供去重参考，不要为这些生成用例）
{chr(10).join(other_titles[:20])}
"""

    return f"""请**严格根据以下测试点**生成测试用例。**禁止**生成测试点中未提及的功能或场景。

⚠️ 关键约束：
- 每个测试点生成 2-3 条用例，覆盖正向、反向、边界
- 只基于测试点描述和需求文档中明确提到的内容生成
- 不要凭空添加需求中不存在的业务逻辑
{req_block}
## 本批测试点（为这些生成用例）
{points_block}
{all_points_block}
{skill_prompt_block}

{f"## 知识库参考{chr(10)}{rag_context}" if rag_context else ""}

{few_shot_block}

## 输出格式（严格 JSON，不要输出其他内容）
{{
    "test_cases": [
        {{
            "case_no": "TC-001",
            "name": "用例名称",
            "test_type": "功能|兼容性|易用性|性能|稳定性|安全性|可靠性|效果(AI类、资源类)|效果(硬件器件类)|可维护性|可移植性|埋点",
            "priority": "P0|P1|P2|P3|P4|P5",
            "preconditions": "具体的前置条件",
            "module": "所属模块名称",
            "steps": [
                {{"step": 1, "action": "具体操作（含测试数据）", "expected": "明确可验证的预期结果"}}
            ],
            "tags": ["标签1"],
            "test_point_id": "TP-001"
        }}
    ]
}}"""


def build_test_point_supplement_system_prompt() -> str:
    return """你是资深测试工程师。根据用户反馈，针对被驳回的测试点进行替换和补充。
保持与已通过测试点一致的粒度和风格，避免与已通过的测试点重复。"""


def build_test_point_supplement_user_prompt(
    feedback: str,
    approved_points: list[dict],
    rejected_points: list[dict],
    original_requirement: str = "",
    skill_prompt_block: str = "",
    rag_context: str = "",
) -> str:
    approved_block = ""
    if approved_points:
        approved_block = "\n## 已通过测试点（不要重复）\n"
        for p in approved_points:
            approved_block += f"- {p.get('id', '')}: {p.get('title', '')} — {p.get('description', '')}\n"

    rejected_block = ""
    if rejected_points:
        rejected_block = "\n## 被驳回测试点（需替换或补充）\n"
        for p in rejected_points:
            rejected_block += f"- {p.get('id', '')}: {p.get('title', '')} — {p.get('description', '')}\n"

    return f"""用户对当前测试点有补充反馈，请生成替代/补充的测试点。

## 用户反馈
{feedback}
{approved_block}
{rejected_block}
{f"## 原始需求\n{original_requirement[:2000]}" if original_requirement else ""}
{skill_prompt_block}
{f"## 知识库上下文\n{rag_context}" if rag_context else ""}

## 输出格式（严格 JSON）
{{
    "test_points": [
        {{
            "id": "TP-xxx",
            "title": "测试点标题",
            "description": "测试点描述",
            "priority": "P0|P1|P2",
            "test_type": "功能|兼容性|...",
            "source": "supplement"
        }}
    ]
}}"""


def build_modify_cases_system_prompt() -> str:
    return """你是资深测试用例编写工程师。根据用户反馈、已通过/驳回的用例，补充生成新的测试用例。
风格与已通过用例保持一致，避免驳回用例中的问题。"""


def build_modify_cases_user_prompt(
    feedback: str,
    approved_cases: list[dict],
    rejected_cases: list[dict],
    confirmed_points: list[dict],
    skill_block: str = "",
    rag_context: str = "",
) -> str:
    approved_block = ""
    if approved_cases:
        approved_block = "\n## 已通过用例（参考风格）\n"
        for c in approved_cases[:10]:
            approved_block += f"- [{c.get('priority', 'P1')}] {c.get('name', '')}: {c.get('preconditions', '')}\n"

    rejected_block = ""
    if rejected_cases:
        rejected_block = "\n## 已驳回用例（避免类似问题）\n"
        for c in rejected_cases[:5]:
            rejected_block += f"- {c.get('name', '')}: {c.get('preconditions', '')}\n"

    points_block = ""
    for i, p in enumerate(confirmed_points, 1):
        tp_id = p.get("id", f"TP-{i:03d}")
        points_block += f"\n### 测试点 {tp_id}\n- 标题: {p.get('title', '')}\n- 描述: {p.get('description', '')}\n"

    return f"""用户对当前用例有补充反馈，请根据反馈生成新的补充用例。

## 用户反馈
{feedback}
{approved_block}
{rejected_block}

## 需补充的测试点
{points_block or "（根据反馈自行判断需补充的场景）"}
{skill_block}
{f"## 知识库上下文\n{rag_context}" if rag_context else ""}

## 输出格式（严格 JSON）
{{
    "test_cases": [
        {{
            "case_no": "TC-xxx",
            "name": "用例名称",
            "test_type": "功能|兼容性|易用性|...",
            "priority": "P0|P1|P2|...",
            "preconditions": "前置条件",
            "module": "所属模块",
            "steps": [{{"step": 1, "action": "操作", "expected": "预期结果"}}],
            "test_point_id": "TP-001"
        }}
    ]
}}"""
