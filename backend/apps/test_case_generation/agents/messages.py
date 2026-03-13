"""autogen-core 消息类型定义 — 所有 Agent 间通信的数据契约"""
from dataclasses import dataclass, field


@dataclass
class UserRequest:
    """API → Coordinator 的统一入口"""
    intent: str
    content: str
    conv_id: str = ""
    file_ids: list[str] = field(default_factory=list)
    image_file_ids: list[str] = field(default_factory=list)
    confirmed_points: list[dict] = field(default_factory=list)
    rejected_ids: list[str] = field(default_factory=list)
    feedback: str = ""
    project_id: str = ""
    module_name: str = ""
    text_model_id: str = ""
    vision_model_id: str = ""


@dataclass
class AgentResponse:
    """所有 Agent 的统一返回"""
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""


@dataclass
class ParseDocumentRequest:
    """Coordinator → DocumentParserAgent"""
    file_ids: list[str]
    vision_model_id: str = ""


@dataclass
class LoadSkillsRequest:
    """Coordinator → SkillLoaderAgent"""
    categories: list[str]
    selected_keys: list[str] = field(default_factory=list)


@dataclass
class LoadSkillsResponse:
    """SkillLoaderAgent → Coordinator"""
    skill_block: str
    skill_names: list[str] = field(default_factory=list)


@dataclass
class KnowledgeSearchRequest:
    """Coordinator → KnowledgeSearchAgent"""
    query: str
    project_id: str = ""
    top_k: int = 5


@dataclass
class KnowledgeSearchResponse:
    """KnowledgeSearchAgent → Coordinator"""
    context: str
    chunks: list[dict] = field(default_factory=list)


@dataclass
class ExtractTestPointsRequest:
    """Coordinator → TestPointExtractorAgent（首次提取）"""
    requirement_text: str = ""
    parsed_documents: list[dict] = field(default_factory=list)
    user_prompt: str = ""
    skill_block: str = ""
    rag_context: str = ""


@dataclass
class ModifyTestPointsRequest:
    """Coordinator → TestPointExtractorAgent（增量补充）"""
    feedback: str
    rejected_point_ids: list[str] = field(default_factory=list)
    approved_points: list[dict] = field(default_factory=list)
    rejected_points: list[dict] = field(default_factory=list)
    original_requirement: str = ""
    skill_block: str = ""
    rag_context: str = ""


@dataclass
class GenerateCasesRequest:
    """Coordinator → TestCaseGeneratorAgent（首次生成）"""
    confirmed_points: list[dict]
    all_points: list[dict] = field(default_factory=list)
    requirement_context: str = ""
    project_id: str = ""
    module_name: str = ""
    skill_block: str = ""
    rag_context: str = ""


@dataclass
class ModifyCasesRequest:
    """Coordinator → TestCaseGeneratorAgent（增量补充）"""
    feedback: str
    rejected_case_ids: list[str] = field(default_factory=list)
    approved_cases: list[dict] = field(default_factory=list)
    rejected_cases: list[dict] = field(default_factory=list)
    confirmed_points: list[dict] = field(default_factory=list)
    skill_block: str = ""
    rag_context: str = ""


@dataclass
class ReviewCasesRequest:
    """Coordinator → QualityReviewerAgent"""
    cases: list[dict]


@dataclass
class ChatRequest:
    """Coordinator → ChatAgent"""
    message: str
    context_summary: str = ""
    history: list[dict] = field(default_factory=list)
    text_model_id: str = ""
    image_urls: list[str] = field(default_factory=list)
    vision_model_id: str = ""
