"""
知识库门面服务（Facade Pattern）

提供统一的知识库操作接口，整合：
- 页面分析（PageAnalyzerService）
- 关系型数据库存储（Repository）
- 向量数据库存储（VectorService）
"""
import uuid
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..models import AppInfo, PageAnalysis, PageElement
from ..repositories import AppRepository, PageRepository, ElementRepository
from .page_analyzer_service import PageAnalyzerService
from .vector_service import VectorService


class KnowledgeService:
    """
    知识库服务 - Facade 模式
    
    统一协调各子服务，提供高层 API：
    - 分析页面并存储
    - 语义搜索元素
    - 管理知识库数据
    """
    
    def __init__(self, session: AsyncSession):
        """
        初始化知识库服务
        
        Args:
            session: 数据库会话
        """
        self.session = session
        
        # 初始化 Repository
        self._app_repo = AppRepository(session)
        self._page_repo = PageRepository(session)
        self._element_repo = ElementRepository(session)
        
        # 初始化其他服务（延迟初始化）
        self._analyzer_service: Optional[PageAnalyzerService] = None
        self._vector_service: Optional[VectorService] = None
    
    @property
    def analyzer_service(self) -> PageAnalyzerService:
        """获取分析服务（延迟初始化）"""
        if self._analyzer_service is None:
            self._analyzer_service = PageAnalyzerService()
        return self._analyzer_service
    
    @property
    def vector_service(self) -> VectorService:
        """获取向量服务（延迟初始化）"""
        if self._vector_service is None:
            self._vector_service = VectorService.get_instance()
        return self._vector_service
    
    # ==================== 页面分析相关 ====================
    
    async def analyze_page(
        self,
        image_data: str,
        app_name: str,
        platform: str,
        package_name: Optional[str] = None,
        device_udid: Optional[str] = None,
        device_resolution: Optional[str] = None,
        context_hint: Optional[str] = None,
        skip_duplicate: bool = True,
        provider_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析页面截图并存入知识库
        
        完整流程：
        1. 检查截图是否已分析（去重）
        2. 调用视觉模型分析截图
        3. 存入关系型数据库
        4. 存入向量数据库
        
        Args:
            image_data: Base64 编码的截图
            app_name: 应用名称
            platform: 平台（android/ios）
            package_name: 包名（可选）
            device_udid: 设备 UDID（可选）
            device_resolution: 设备分辨率（可选）
            context_hint: 上下文提示（可选）
            skip_duplicate: 是否跳过重复截图
            provider_id: 供应商 ID（可选，从数据库配置）
            model_id: 模型 ID（可选，从数据库配置）
            
        Returns:
            分析结果，包含 page_id, page_name, elements 等
        """
        # 1. 获取或创建 App
        app, is_new_app = await self._app_repo.get_or_create(
            app_name=app_name,
            platform=platform,
            package_name=package_name
        )
        
        # 2. 检查截图是否已分析
        screenshot_hash = self.analyzer_service.calculate_image_hash(image_data)
        
        if skip_duplicate:
            existing_page = await self._page_repo.get_by_screenshot_hash(
                app_id=app.id,
                screenshot_hash=screenshot_hash
            )
            if existing_page:
                logger.info(f"截图已分析过，返回缓存结果: {existing_page.page_name}")
                elements = await self._element_repo.list_by_page(existing_page.id)
                return {
                    "page_id": existing_page.id,
                    "page_name": existing_page.page_name,
                    "page_type": existing_page.page_type,
                    "page_description": existing_page.page_description,
                    "elements": [e.to_dict() for e in elements],
                    "elements_count": len(elements),
                    "confidence_score": float(existing_page.confidence_score),
                    "is_new_page": False,
                    "is_cached": True,
                    "processing_time": 0.0,
                    "usage": {}  # 缓存结果无新 token 消耗
                }
        
        # 3. 调用视觉模型分析
        analysis_result = await self.analyzer_service.analyze_screenshot(
            image_data=image_data,
            context_hint=context_hint,
            provider_id=provider_id,
            model_id=model_id
        )
        
        # 3.5 记录 LLM 用量到数据库
        if provider_id and model_id and analysis_result.get("usage"):
            try:
                await self._record_llm_usage(
                    provider_id=provider_id,
                    model_id=model_id,
                    usage=analysis_result["usage"],
                    latency_ms=int(analysis_result.get("processing_time", 0) * 1000)
                )
            except Exception as e:
                logger.warning(f"记录 LLM 用量失败: {e}")
        
        # 4. 存入关系型数据库
        page = await self._save_page_analysis(
            app=app,
            analysis_result=analysis_result,
            device_udid=device_udid,
            device_resolution=device_resolution
        )
        
        # 5. 存入向量数据库（可选，失败不影响主流程）
        elements = await self._element_repo.list_by_page(page.id)
        try:
            await self._save_to_vector_db(
                app_name=app_name,
                page=page,
                elements=elements,
                platform=platform
            )
        except Exception as e:
            logger.warning(f"向量数据库保存失败（已跳过）: {e}")
        
        # 6. 提交事务
        await self.session.commit()
        
        return {
            "page_id": page.id,
            "page_name": page.page_name,
            "page_type": page.page_type,
            "page_description": page.page_description,
            "elements": [e.to_dict() for e in elements],
            "elements_count": len(elements),
            "confidence_score": float(page.confidence_score) if page.confidence_score else 0.0,
            "is_new_page": True,
            "is_cached": False,
            "processing_time": float(page.processing_time) if page.processing_time else 0.0,
            "usage": analysis_result.get("usage", {})
        }
    
    async def _save_page_analysis(
        self,
        app: AppInfo,
        analysis_result: Dict[str, Any],
        device_udid: Optional[str],
        device_resolution: Optional[str]
    ) -> PageAnalysis:
        """保存页面分析结果到关系型数据库"""
        # 创建页面记录
        page = PageAnalysis(
            id=str(uuid.uuid4()),
            app_id=app.id,
            page_name=analysis_result.get("page_name", "Unknown"),
            page_type=analysis_result.get("page_type", "unknown"),
            page_description=analysis_result.get("page_description", ""),
            screenshot_hash=analysis_result.get("screenshot_hash", ""),
            device_udid=device_udid,
            device_resolution=device_resolution,
            elements_count=len(analysis_result.get("elements", [])),
            confidence_score=Decimal(str(analysis_result.get("confidence_score", 0.0))),
            raw_response=analysis_result,
            analysis_metadata={
                "model": self.analyzer_service.config.ANALYZER_VISION_MODEL,
            },
            processing_time=Decimal(str(analysis_result.get("processing_time", 0.0)))
        )
        
        await self._page_repo.create(page)
        
        # 创建元素记录
        elements = []
        for elem_data in analysis_result.get("elements", []):
            elem_dict = self.analyzer_service.build_element_model(elem_data, page.id)
            
            element = PageElement(
                id=str(uuid.uuid4()),
                **elem_dict
            )
            elements.append(element)
        
        if elements:
            await self._element_repo.create_many(elements)
        
        # 更新页面元素计数
        page.elements_count = len(elements)
        
        logger.info(f"保存页面分析: {page.page_name} - {len(elements)} 个元素")
        
        return page
    
    async def _save_to_vector_db(
        self,
        app_name: str,
        page: PageAnalysis,
        elements: List[PageElement],
        platform: str
    ) -> int:
        """保存元素到向量数据库"""
        if not elements:
            return 0
        
        # 构建向量数据
        vector_data = []
        for element in elements:
            data = element.to_vector_data(
                app_name=app_name,
                page_name=page.page_name,
                platform=platform
            )
            # 添加额外的过滤字段
            data["metadata"]["page_type"] = page.page_type
            vector_data.append(data)
        
        # 批量写入向量库
        count = await self.vector_service.add_elements_batch(vector_data)
        
        logger.info(f"保存 {count} 个元素到向量库")
        return count
    
    # ==================== 语义搜索相关 ====================
    
    async def search_elements(
        self,
        query: str,
        app_name: Optional[str] = None,
        page_name: Optional[str] = None,
        page_type: Optional[str] = None,
        element_type: Optional[str] = None,
        platform: Optional[str] = None,
        testable_only: bool = True,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        语义搜索元素
        
        Args:
            query: 搜索文本，如"点击登录按钮"
            app_name: 限定 App
            page_name: 限定页面
            page_type: 限定页面类型
            element_type: 限定元素类型
            platform: 限定平台
            testable_only: 只返回可测试元素
            top_k: 返回数量
            
        Returns:
            搜索结果，包含匹配的元素列表
        """
        import time
        start_time = time.time()
        
        # 构建过滤表达式
        filters = []
        if app_name:
            filters.append(f'app_name == "{app_name}"')
        if page_name:
            filters.append(f'page_name == "{page_name}"')
        if page_type:
            filters.append(f'page_type == "{page_type}"')
        if element_type:
            filters.append(f'element_type == "{element_type}"')
        if platform:
            filters.append(f'platform == "{platform}"')
        if testable_only:
            filters.append('is_testable == true')
        
        filter_expr = " and ".join(filters) if filters else None
        
        # 执行搜索
        results = await self.vector_service.search(
            query=query,
            top_k=top_k,
            filter_expr=filter_expr
        )
        
        search_time = round(time.time() - start_time, 3)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "search_time": search_time,
            "filters": {
                "app_name": app_name,
                "page_name": page_name,
                "page_type": page_type,
                "element_type": element_type,
                "platform": platform,
                "testable_only": testable_only
            }
        }
    
    # ==================== 知识库管理相关 ====================
    
    async def get_apps(
        self,
        platform: Optional[str] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取应用列表"""
        if platform:
            apps = await self._app_repo.list_by_platform(platform, offset, limit)
        else:
            apps = await self._app_repo.get_all(offset, limit)
        
        return [app.to_dict() for app in apps]
    
    async def get_pages(
        self,
        app_name: Optional[str] = None,
        platform: Optional[str] = None,
        page_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取页面列表"""
        if app_name:
            pages = await self._page_repo.list_by_app_name(
                app_name=app_name,
                platform=platform,
                page_type=page_type,
                offset=offset,
                limit=limit
            )
        else:
            pages = await self._page_repo.get_all(offset, limit)
        
        return [page.to_dict() for page in pages]
    
    async def get_page_elements(
        self,
        page_id: str,
        element_type: Optional[str] = None,
        testable_only: bool = True
    ) -> List[Dict[str, Any]]:
        """获取页面的元素列表"""
        elements = await self._element_repo.list_by_page(
            page_id=page_id,
            element_type=element_type,
            testable_only=testable_only
        )
        return [e.to_dict() for e in elements]
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        # 关系型数据库统计
        total_apps = await self._app_repo.count()
        total_pages = await self._page_repo.count()
        total_elements = await self._element_repo.count()
        
        # 向量库统计
        vector_stats = await self.vector_service.get_stats()
        
        # 最近分析
        recent_pages = await self._page_repo.get_recent_pages(limit=5)
        
        return {
            "total_apps": total_apps,
            "total_pages": total_pages,
            "total_elements": total_elements,
            "vector_stats": vector_stats,
            "recent_analyses": [
                {
                    "page_id": p.id,
                    "page_name": p.page_name,
                    "elements_count": p.elements_count,
                    "created_at": p.created_at.isoformat() if p.created_at else None
                }
                for p in recent_pages
            ]
        }
    
    async def delete_page(self, page_id: str) -> bool:
        """
        删除页面及其元素
        
        同时删除关系型数据库和向量数据库中的数据
        """
        # 删除向量数据
        await self.vector_service.delete_by_page(page_id)
        
        # 删除关系型数据（元素会级联删除）
        success = await self._page_repo.delete(page_id)
        
        await self.session.commit()
        
        return success
    
    async def delete_app(self, app_id: str) -> bool:
        """
        删除应用及其所有页面和元素
        """
        # 获取应用信息
        app = await self._app_repo.get_by_id(app_id)
        if not app:
            return False
        
        # 删除向量数据
        await self.vector_service.delete_by_app(app.app_name)
        
        # 删除关系型数据（页面和元素会级联删除）
        success = await self._app_repo.delete(app_id)
        
        await self.session.commit()
        
        return success
    
    async def _record_llm_usage(
        self,
        provider_id: str,
        model_id: str,
        usage: Dict[str, int],
        latency_ms: int
    ) -> None:
        """
        记录 LLM 用量到数据库
        
        Args:
            provider_id: 供应商 ID
            model_id: 模型 ID
            usage: token 用量，包含 input_tokens, output_tokens, total_tokens
            latency_ms: 延迟（毫秒）
        """
        from apps.ui_automation.models.llm_config import LLMUsageLog, LLMProvider
        from sqlalchemy import select
        
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
        
        # 创建用量记录
        log = LLMUsageLog(
            provider_id=provider_id,
            model_id=model_id,
            request_type="page_analysis",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            success=True,
            cost=0.0  # TODO: 根据模型价格计算
        )
        self.session.add(log)
        
        # 更新供应商统计
        provider_result = await self.session.execute(
            select(LLMProvider).where(LLMProvider.id == provider_id)
        )
        provider = provider_result.scalar_one_or_none()
        if provider:
            provider.total_requests = (provider.total_requests or 0) + 1
            provider.total_tokens = (provider.total_tokens or 0) + total_tokens
        
        logger.info(f"记录 LLM 用量: provider={provider_id}, tokens={total_tokens}, latency={latency_ms}ms")
