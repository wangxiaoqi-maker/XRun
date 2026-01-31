"""
页面分析 API Schema

定义请求和响应的数据结构
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== 通用模型 ====================

class ElementInfo(BaseModel):
    """元素信息"""
    id: str = Field(..., description="元素 ID")
    element_name: str = Field(..., description="元素名称")
    element_type: str = Field(..., description="元素类型")
    text_content: Optional[str] = Field(None, description="元素文字内容")
    description: str = Field(..., description="元素描述")
    visual_description: Optional[str] = Field(None, description="视觉描述")
    midscene_locator: Optional[str] = Field(None, description="MidScene 定位描述")
    position_area: Optional[str] = Field(None, description="位置区域")
    position_in_container: Optional[str] = Field(None, description="容器内位置")
    bbox: Optional[List[float]] = Field(None, description="元素位置坐标 [left%, top%, width%, height%]")
    relative_positions: Optional[List[Dict[str, Any]]] = Field(None, description="相对位置关系")
    is_navigation: bool = Field(False, description="是否是导航元素")
    target_page_name: Optional[str] = Field(None, description="跳转目标页面")
    midscene_operations: Optional[List[str]] = Field(None, description="支持的 MidScene 操作")
    test_scenarios: Optional[List[str]] = Field(None, description="测试场景")
    confidence_score: float = Field(0.0, description="置信度分数")
    test_priority: str = Field("medium", description="测试优先级")
    is_testable: bool = Field(True, description="是否可测试")
    
    class Config:
        from_attributes = True


class PageSummary(BaseModel):
    """页面摘要"""
    id: str = Field(..., description="页面 ID")
    app_id: str = Field(..., description="应用 ID")
    page_name: str = Field(..., description="页面名称")
    page_type: str = Field(..., description="页面类型")
    page_description: Optional[str] = Field(None, description="页面描述")
    elements_count: int = Field(0, description="元素数量")
    confidence_score: float = Field(0.0, description="置信度分数")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    
    class Config:
        from_attributes = True


class AppSummary(BaseModel):
    """应用摘要"""
    id: str = Field(..., description="应用 ID")
    app_name: str = Field(..., description="应用名称")
    package_name: Optional[str] = Field(None, description="包名")
    platform: str = Field(..., description="平台")
    version: Optional[str] = Field(None, description="版本")
    pages_count: int = Field(0, description="页面数量")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    
    class Config:
        from_attributes = True


# ==================== 页面分析 ====================

class PageAnalyzeRequest(BaseModel):
    """页面分析请求"""
    image_data: str = Field(
        ..., 
        description="Base64 编码的截图数据",
        min_length=100
    )
    app_name: str = Field(
        ..., 
        description="应用名称",
        min_length=1,
        max_length=100
    )
    platform: str = Field(
        ..., 
        description="平台（android/ios）",
        pattern="^(android|ios)$"
    )
    package_name: Optional[str] = Field(
        None, 
        description="包名（Android）或 Bundle ID（iOS）",
        max_length=200
    )
    device_udid: Optional[str] = Field(
        None, 
        description="设备 UDID",
        max_length=100
    )
    device_resolution: Optional[str] = Field(
        None, 
        description="设备分辨率",
        max_length=50
    )
    context_hint: Optional[str] = Field(
        None, 
        description="上下文提示，如'这是登录页面'",
        max_length=500
    )
    skip_duplicate: bool = Field(
        True,
        description="是否跳过重复截图"
    )
    # 模型配置（从前端选择）
    provider_id: Optional[str] = Field(
        None,
        description="供应商 ID（从数据库配置）"
    )
    model_id: Optional[str] = Field(
        None,
        description="模型 ID（从数据库配置）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_data": "data:image/png;base64,iVBORw0KGgoAAAANS...",
                "app_name": "支付宝",
                "platform": "android",
                "package_name": "com.eg.android.AlipayGphone",
                "context_hint": "这是支付宝首页",
                "provider_id": "xxx-xxx",
                "model_id": "xxx-xxx"
            }
        }


class UsageInfo(BaseModel):
    """Token 用量信息"""
    input_tokens: int = Field(0, description="输入 token 数")
    output_tokens: int = Field(0, description="输出 token 数")
    total_tokens: int = Field(0, description="总 token 数")


class PageAnalyzeResponse(BaseModel):
    """页面分析响应"""
    page_id: str = Field(..., description="页面 ID")
    page_name: str = Field(..., description="AI 生成的页面名称")
    page_type: str = Field(..., description="页面类型")
    page_description: Optional[str] = Field(None, description="页面描述")
    elements: List[ElementInfo] = Field(default_factory=list, description="元素列表")
    elements_count: int = Field(0, description="元素数量")
    confidence_score: float = Field(0.0, description="置信度分数")
    is_new_page: bool = Field(True, description="是否是新页面")
    is_cached: bool = Field(False, description="是否使用缓存")
    processing_time: float = Field(0.0, description="处理耗时（秒）")
    usage: Optional[UsageInfo] = Field(None, description="Token 用量")


# ==================== 语义搜索 ====================

class ElementSearchRequest(BaseModel):
    """元素搜索请求"""
    query: str = Field(
        ..., 
        description="搜索文本，如'点击登录按钮'",
        min_length=1,
        max_length=500
    )
    app_name: Optional[str] = Field(
        None, 
        description="限定 App 名称",
        max_length=100
    )
    page_name: Optional[str] = Field(
        None, 
        description="限定页面名称",
        max_length=200
    )
    page_type: Optional[str] = Field(
        None,
        description="限定页面类型"
    )
    element_type: Optional[str] = Field(
        None, 
        description="限定元素类型"
    )
    platform: Optional[str] = Field(
        None,
        description="限定平台（android/ios）"
    )
    testable_only: bool = Field(
        True, 
        description="只返回可测试元素"
    )
    top_k: int = Field(
        5, 
        description="返回数量",
        ge=1,
        le=50
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "点击登录按钮",
                "app_name": "微信",
                "testable_only": True,
                "top_k": 5
            }
        }


class ElementMatchResult(BaseModel):
    """元素匹配结果"""
    id: str = Field(..., description="元素 ID")
    element_name: str = Field(..., description="元素名称")
    element_type: str = Field(..., description="元素类型")
    description: str = Field(..., description="元素描述")
    similarity_score: float = Field(..., description="相似度分数 0-1")
    app_name: str = Field(..., description="应用名称")
    page_name: str = Field(..., description="页面名称")
    page_type: Optional[str] = Field(None, description="页面类型")
    platform: str = Field(..., description="平台")
    is_testable: bool = Field(True, description="是否可测试")
    test_priority: Optional[str] = Field(None, description="测试优先级")


class ElementSearchResponse(BaseModel):
    """元素搜索响应"""
    query: str = Field(..., description="搜索文本")
    results: List[ElementMatchResult] = Field(default_factory=list, description="匹配结果")
    total_results: int = Field(0, description="结果数量")
    search_time: float = Field(0.0, description="搜索耗时（秒）")
    filters: Dict[str, Any] = Field(default_factory=dict, description="使用的过滤条件")


# ==================== 知识库统计 ====================

class KnowledgeBaseStats(BaseModel):
    """知识库统计信息"""
    total_apps: int = Field(0, description="应用总数")
    total_pages: int = Field(0, description="页面总数")
    total_elements: int = Field(0, description="元素总数")
    vector_stats: Dict[str, Any] = Field(default_factory=dict, description="向量库统计")
    recent_analyses: List[Dict[str, Any]] = Field(default_factory=list, description="最近分析记录")


# ==================== 其他 ====================

class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")
