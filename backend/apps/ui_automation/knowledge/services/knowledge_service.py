"""
知识库门面服务（Facade Pattern）

提供统一的知识库操作接口，整合：
- 页面分析（PageAnalyzerService）
- 关系型数据库存储（Repository）
- 向量数据库存储（VectorService）

架构说明：
- 页面组织：通过 PageModule（功能模块）管理，如"转账模块"包含多个转账相关页面
- 跳转关系：通过 PageTransition 记录，基于元素的 is_navigation 属性
- 路径查找：find_navigation_path() 用于自动生成用例的前置步骤
"""
import uuid
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from ..models import AppInfo, PageAnalysis, PageElement, PageTransition
from ..repositories import AppRepository, PageRepository, ElementRepository
from .page_analyzer_service import PageAnalyzerService
from .vector_service import VectorService
from .minio_service import get_minio_service


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
        model_id: Optional[str] = None,
        app_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析页面截图并存入知识库
        
        完整流程：
        1. 检查截图是否已分析（去重）
        2. 调用视觉模型分析截图
        3. 存入关系型数据库
        4. 存入向量数据库（可选，默认不保存）
        
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
            分析结果，包含 page_name, elements 等（不保存数据库，需用户手动确认后保存）
        """
        # 1. 检查是否已分析过（去重）
        screenshot_hash = self.analyzer_service.calculate_image_hash(image_data)
        
        if skip_duplicate:
            # 获取或创建 App（仅用于查询缓存）
            app, _ = await self._app_repo.get_or_create(
                app_name=app_name,
                platform=platform,
                package_name=package_name
            )
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
                    "is_saved": True,  # 已保存过
                    "processing_time": 0.0,
                    "usage": {}
                }
        
        # 2. 调用视觉模型分析（不保存数据库）
        analysis_result = await self.analyzer_service.analyze_screenshot(
            image_data=image_data,
            context_hint=context_hint,
            provider_id=provider_id,
            model_id=model_id
        )
        
        # 3. 记录 LLM 用量
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
        
        # 4. 返回分析结果（不保存，用户确认后手动保存）
        # 生成临时元素 ID（保存时会替换为真实 ID）
        elements = analysis_result.get("elements", [])
        for i, elem in enumerate(elements):
            elem["id"] = f"temp_{i}_{screenshot_hash[:8]}"
        
        return {
            "page_id": None,  # 未保存，无 page_id
            "page_name": analysis_result.get("page_name", "Unknown"),
            "page_type": analysis_result.get("page_type", "unknown"),
            "page_description": analysis_result.get("page_description", ""),
            "elements": elements,
            "elements_count": len(elements),
            "confidence_score": analysis_result.get("confidence_score", 0.0),
            "is_new_page": True,
            "is_cached": False,
            "is_saved": False,  # 未保存
            "processing_time": analysis_result.get("processing_time", 0.0),
            "usage": analysis_result.get("usage", {}),
            # 保存时需要的元数据
            "save_meta": {
                "app_id": app_id,  # 应用管理模块的应用 ID
                "app_name": app_name,
                "platform": platform,
                "package_name": package_name,
                "device_udid": device_udid,
                "device_resolution": device_resolution,
                "screenshot_hash": screenshot_hash,
                "screenshot_base64": image_data,  # 保存截图到 MinIO
                "context_hint": context_hint,  # 用户输入的上下文提示
                "raw_result": analysis_result
            }
        }
    
    async def _save_page_analysis(
        self,
        app: AppInfo,
        analysis_result: Dict[str, Any],
        device_udid: Optional[str],
        device_resolution: Optional[str],
        context_hint: Optional[str] = None,
        screenshot_url: Optional[str] = None,
        page_id: Optional[str] = None,
        module_id: Optional[str] = None
    ) -> PageAnalysis:
        """保存页面分析结果到关系型数据库"""
        # 创建页面记录
        page = PageAnalysis(
            id=page_id or str(uuid.uuid4()),
            app_id=app.id,
            module_id=module_id,  # 关联模块
            page_name=analysis_result.get("page_name", "Unknown"),
            page_type=analysis_result.get("page_type", "unknown"),
            page_description=analysis_result.get("page_description", ""),
            user_context=context_hint,  # 保存用户输入的上下文描述
            screenshot_hash=analysis_result.get("screenshot_hash", ""),
            screenshot_url=screenshot_url,  # 保存截图 URL
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
            
            # 如果有用户上下文，追加到描述中增强语义搜索
            if page.user_context:
                data["metadata"]["user_context"] = page.user_context
                # 把用户上下文加入描述，提高搜索准确性
                data["description"] = f"{data['description']} [页面说明: {page.user_context}]"
            
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
    
    async def save_analysis_to_knowledge_base(
        self,
        analysis_result: Dict[str, Any],
        save_to_vector: bool = True
    ) -> Dict[str, Any]:
        """
        保存分析结果到知识库（关系型数据库 + 向量数据库 + MinIO）
        
        用户确认 AI 分析结果后手动触发
        
        Args:
            analysis_result: AI 分析返回的结果（包含 _meta 元数据）
            save_to_vector: 是否同时保存到向量库
            
        Returns:
            保存结果，包含 page_id 和保存的元素数量
        """
        meta = analysis_result.get("save_meta", {})
        if not meta:
            raise ValueError("分析结果缺少元数据，无法保存。请重新进行 AI 分析")
        
        # 1. 获取或创建 App
        app, _ = await self._app_repo.get_or_create(
            app_name=meta["app_name"],
            platform=meta["platform"],
            package_name=meta.get("package_name")
        )
        
        # 2. 上传截图到 MinIO（预先生成 page_id）
        page_id = str(uuid.uuid4())
        screenshot_url = None
        screenshot_base64 = meta.get("screenshot_base64")
        if screenshot_base64:
            try:
                minio_service = get_minio_service()
                screenshot_url = minio_service.upload_screenshot(
                    image_data=screenshot_base64,
                    page_id=page_id
                )
                if screenshot_url:
                    logger.info(f"✅ 截图已上传到 MinIO: {screenshot_url}")
            except Exception as e:
                logger.warning(f"截图上传失败（已跳过）: {e}")
        
        # 3. 保存到关系型数据库
        page = await self._save_page_analysis(
            app=app,
            analysis_result=meta["raw_result"],
            device_udid=meta.get("device_udid"),
            device_resolution=meta.get("device_resolution"),
            context_hint=meta.get("context_hint"),
            screenshot_url=screenshot_url,
            page_id=page_id,
            module_id=meta.get("module_id")  # 从 meta 中获取模块 ID
        )
        
        # 3. 获取保存后的元素
        elements = await self._element_repo.list_by_page(page.id)
        
        # 4. 生成元素切图（从截图中裁剪）
        if screenshot_base64 and elements:
            try:
                from .crop_service import get_crop_service
                crop_service = get_crop_service()
                
                crop_count = 0
                for element in elements:
                    if element.bbox:
                        crop_url = crop_service.crop_element_from_base64(
                            image_data=screenshot_base64,
                            bbox=element.bbox,
                            element_id=element.id
                        )
                        if crop_url:
                            element.crop_image_url = crop_url
                            crop_count += 1
                
                if crop_count > 0:
                    logger.info(f"✅ 已生成 {crop_count} 个元素切图")
            except Exception as e:
                logger.warning(f"生成元素切图失败（已跳过）: {e}")
        
        # 5. 保存到向量数据库
        if save_to_vector and elements:
            try:
                await self._save_to_vector_db(
                    app_name=meta["app_name"],
                    page=page,
                    elements=elements,
                    platform=meta["platform"]
                )
                logger.info(f"✅ 已保存 {len(elements)} 个元素到向量数据库")
            except Exception as e:
                logger.warning(f"向量数据库保存失败（已跳过）: {e}")
        
        # 6. 提交事务
        await self.session.commit()
        
        # 7. 清除相关缓存
        from .cache_service import invalidate_stats_cache, invalidate_pages_cache
        await invalidate_stats_cache()
        await invalidate_pages_cache()
        
        logger.info(f"✅ 已保存页面到知识库: {page.page_name} ({len(elements)} 个元素)")
        
        return {
            "page_id": page.id,
            "page_name": page.page_name,
            "elements_count": len(elements),
            "saved_to_vector": save_to_vector
        }
    
    # ==================== 跳转关系（基于模块结构） ====================
    
    async def get_page_transitions(self, app_id: str) -> Dict[str, Any]:
        """
        获取应用的所有跳转关系（用于知识图谱展示）
        
        Returns:
            {
                "nodes": [页面列表],
                "edges": [跳转关系列表],
                "stats": {统计信息}
            }
        """
        # 获取应用下所有页面
        pages_result = await self.session.execute(
            select(PageAnalysis).where(PageAnalysis.app_id == app_id)
        )
        pages = pages_result.scalars().all()
        
        page_ids = [p.id for p in pages]
        
        # 获取所有跳转关系
        transitions_result = await self.session.execute(
            select(PageTransition).where(
                PageTransition.from_page_id.in_(page_ids)
            )
        )
        transitions = transitions_result.scalars().all()
        
        # 构建节点
        nodes = [
            {
                "id": p.id,
                "name": p.page_name,
                "type": p.page_type,
                "depth": p.depth or 0,
                "elements_count": p.elements_count or 0
            }
            for p in pages
        ]
        
        # 构建边
        edges = [
            {
                "id": t.id,
                "from": t.from_page_id,
                "to": t.to_page_id,
                "from_name": t.from_page_name,
                "to_name": t.to_page_name,
                "trigger": t.trigger_element_name,
                "locator": t.trigger_element_locator,
                "type": t.transition_type
            }
            for t in transitions
        ]
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_pages": len(pages),
                "total_transitions": len(transitions),
                "max_depth": max((p.depth or 0) for p in pages) if pages else 0
            }
        }
    
    async def find_navigation_path(
        self,
        app_id: str,
        from_page_name: str,
        to_page_name: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        查找从页面 A 到页面 B 的导航路径（BFS）
        
        用于自动生成用例时，计算到达目标页面的前置步骤
        
        Returns:
            操作路径列表，每项包含 {page, action, locator}
        """
        from collections import deque
        
        # 查找起始和目标页面
        from_result = await self.session.execute(
            select(PageAnalysis).where(
                PageAnalysis.app_id == app_id,
                PageAnalysis.page_name.like(f"%{from_page_name}%")
            ).limit(1)
        )
        from_page = from_result.scalar_one_or_none()
        
        to_result = await self.session.execute(
            select(PageAnalysis).where(
                PageAnalysis.app_id == app_id,
                PageAnalysis.page_name.like(f"%{to_page_name}%")
            ).limit(1)
        )
        to_page = to_result.scalar_one_or_none()
        
        if not from_page or not to_page:
            return None
        
        # BFS 搜索
        queue = deque([(from_page.id, [])])
        visited = {from_page.id}
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id == to_page.id:
                return path + [{"page": to_page.page_name, "action": None}]
            
            # 获取当前页面的所有出向跳转
            transitions_result = await self.session.execute(
                select(PageTransition).where(
                    PageTransition.from_page_id == current_id
                )
            )
            transitions = transitions_result.scalars().all()
            
            for trans in transitions:
                if trans.to_page_id not in visited:
                    visited.add(trans.to_page_id)
                    new_path = path + [{
                        "page": trans.from_page_name,
                        "action": f"点击「{trans.trigger_element_name}」" if trans.trigger_element_name else "跳转",
                        "locator": trans.trigger_element_locator
                    }]
                    queue.append((trans.to_page_id, new_path))
        
        return None
    
    async def get_apps(
        self,
        platform: Optional[str] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取应用列表
        
        优化：使用缓存减少数据库查询（TTL 60秒）
        """
        from .cache_service import get_cache
        
        cache = get_cache()
        cache_key = f"apps:list:{platform or 'all'}:{offset}:{limit}"
        
        # 尝试获取缓存
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached
        
        # 执行查询
        if platform:
            apps = await self._app_repo.list_by_platform(platform, offset, limit)
        else:
            apps = await self._app_repo.get_all(offset, limit)
        
        result = [app.to_dict() for app in apps]
        
        # 缓存 60 秒
        await cache.set(cache_key, result, ttl=60)
        return result
    
    async def get_pages(
        self,
        app_name: Optional[str] = None,
        platform: Optional[str] = None,
        page_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
        include_failed: bool = False,
        deduplicate: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取页面列表（优化版：SQL 层去重 + 缓存）
        
        Args:
            app_name: 应用名称过滤
            platform: 平台过滤
            page_type: 页面类型过滤
            offset: 偏移量
            limit: 数量限制
            include_failed: 是否包含解析失败的页面（elements_count=0）
            deduplicate: 是否去重（同名页面只保留最新的）
        """
        from .cache_service import get_cache
        
        # 仅对去重查询启用缓存（最常用场景）
        if deduplicate:
            cache = get_cache()
            cache_key = f"pages:unique:{offset}:{limit}:{app_name or 'all'}:{include_failed}"
            
            # 尝试获取缓存
            cached = await cache.get(cache_key)
            if cached is not None:
                return cached
            
            # 使用高效的 SQL 层去重查询
            pages = await self._page_repo.get_unique_pages(
                offset=offset,
                limit=limit,
                app_name=app_name,
                include_failed=include_failed
            )
            result = [page.to_dict() for page in pages]
            
            # 缓存 15 秒（页面数据变化相对频繁）
            await cache.set(cache_key, result, ttl=15)
            return result
        else:
            # 不去重时使用原有逻辑（不缓存）
            from ..models import PageAnalysis
            
            if app_name:
                pages = await self._page_repo.list_by_app_name(
                    app_name=app_name,
                    platform=platform,
                    page_type=page_type,
                    offset=offset,
                    limit=limit
                )
            else:
                pages = await self._page_repo.get_all(
                    offset=offset, 
                    limit=limit, 
                    order_by=PageAnalysis.created_at.desc()
                )
            
            result = []
            for page in pages:
                if not include_failed and page.elements_count == 0:
                    continue
                result.append(page.to_dict())
            
            return result
    
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
        """
        获取知识库统计信息
        
        优化：
        - 使用缓存减少数据库查询（TTL 30秒）
        - 单条 SQL 聚合查询代替多次查询
        """
        from .cache_service import get_cache
        
        cache = get_cache()
        cache_key = "stats:global"
        
        # 尝试获取缓存
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached
        
        # 执行查询
        total_apps = await self._app_repo.count()
        total_elements = await self._element_repo.count()
        total_pages = await self._page_repo.count_unique_pages()
        recent_pages = await self._page_repo.get_recent_valid_pages(limit=5)
        
        result = {
            "total_apps": total_apps,
            "total_pages": total_pages,
            "total_elements": total_elements,
            "vector_stats": {"row_count": 0},
            "recent_analyses": [
                {
                    "page_id": p.id,
                    "page_name": p.page_name,
                    "elements_count": p.elements_count,
                    "created_at": p.created_at.isoformat() if p.created_at else None
                }
                for p in recent_pages if p.elements_count > 0
            ][:5]
        }
        
        # 缓存 30 秒
        await cache.set(cache_key, result, ttl=30)
        return result
    
    async def update_page(self, page_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新页面信息
        
        Args:
            page_id: 页面 ID
            update_data: 要更新的字段
            
        Returns:
            是否更新成功
        """
        page = await self._page_repo.get_by_id(page_id)
        if not page:
            return False
        
        # 更新字段
        for key, value in update_data.items():
            if hasattr(page, key):
                setattr(page, key, value)
        
        await self.session.commit()
        return True
    
    async def delete_page(self, page_id: str) -> bool:
        """
        删除页面及其元素
        
        同时删除关系型数据库、向量数据库和 MinIO 中的数据
        """
        # 删除向量数据
        await self.vector_service.delete_by_page(page_id)
        
        # 删除 MinIO 截图
        try:
            minio_service = get_minio_service()
            minio_service.delete_screenshot(page_id)
        except Exception as e:
            logger.warning(f"删除 MinIO 截图失败（已跳过）: {e}")
        
        # 删除关系型数据（元素会级联删除）
        success = await self._page_repo.delete(page_id)
        
        await self.session.commit()
        
        # 清除缓存
        from .cache_service import invalidate_stats_cache, invalidate_pages_cache
        await invalidate_stats_cache()
        await invalidate_pages_cache()
        
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
        
        # 清除缓存
        from .cache_service import invalidate_stats_cache, invalidate_pages_cache, invalidate_apps_cache
        await invalidate_stats_cache()
        await invalidate_pages_cache()
        await invalidate_apps_cache()
        
        return success
    
    async def update_element(self, element_id: str, update_data: dict) -> bool:
        """
        更新元素信息
        
        Args:
            element_id: 元素 ID
            update_data: 要更新的字段
            
        Returns:
            是否更新成功
        """
        element = await self._element_repo.get_by_id(element_id)
        if not element:
            return False
        
        # 更新字段
        for key, value in update_data.items():
            if hasattr(element, key):
                setattr(element, key, value)
        
        await self.session.commit()
        return True
    
    async def delete_element(self, element_id: str) -> bool:
        """
        删除单个元素
        
        Args:
            element_id: 元素 ID
            
        Returns:
            是否删除成功
        """
        # 删除向量数据
        await self.vector_service.delete_element(element_id)
        
        # 删除关系型数据
        success = await self._element_repo.delete(element_id)
        
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
