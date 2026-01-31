"""
知识图谱探索服务

职责：
- 管理探索会话
- 记录页面跳转关系
- 页面去重（基于 page_signature）
- 构建 App 导航图谱
"""
import hashlib
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger
from sqlalchemy.orm import Session

from ..models import PageAnalysis, PageElement, PageTransition, AppInfo
from ..repositories.page_repository import PageRepository
from ..repositories.element_repository import ElementRepository
from .page_analyzer_service import PageAnalyzerService
from .knowledge_service import KnowledgeService


class ExplorationMode(str, Enum):
    """探索模式"""
    MANUAL = "manual"       # 手动探索：用户操作 -> 记录跳转
    SEMI_AUTO = "semi_auto" # 半自动：AI 建议 -> 用户确认
    FULL_AUTO = "full_auto" # 全自动：AI 自动点击探索


class ExplorationSession:
    """探索会话"""
    def __init__(
        self,
        session_id: str,
        app_id: str,
        device_udid: str,
        mode: ExplorationMode,
        current_page_id: Optional[str] = None
    ):
        self.session_id = session_id
        self.app_id = app_id
        self.device_udid = device_udid
        self.mode = mode
        self.current_page_id = current_page_id
        self.started_at = datetime.utcnow()
        self.transitions_count = 0
        self.pages_discovered = 0


class ExplorationService:
    """知识图谱探索服务"""
    
    # 活跃的探索会话
    _active_sessions: Dict[str, ExplorationSession] = {}
    
    def __init__(self, db: Session):
        self.db = db
        self.page_repo = PageRepository(db)
        self.element_repo = ElementRepository(db)
        self.analyzer_service = PageAnalyzerService()
        self.knowledge_service = KnowledgeService(db)
    
    # ==================== 探索会话管理 ====================
    
    def start_exploration(
        self,
        app_id: str,
        device_udid: str,
        mode: ExplorationMode = ExplorationMode.MANUAL,
        current_page_id: Optional[str] = None
    ) -> ExplorationSession:
        """
        开始探索会话
        
        Args:
            app_id: 应用 ID
            device_udid: 设备 UDID
            mode: 探索模式
            current_page_id: 当前页面 ID（如果已有）
            
        Returns:
            ExplorationSession: 探索会话对象
        """
        session_id = str(uuid.uuid4())
        session = ExplorationSession(
            session_id=session_id,
            app_id=app_id,
            device_udid=device_udid,
            mode=mode,
            current_page_id=current_page_id
        )
        
        self._active_sessions[session_id] = session
        logger.info(f"[探索] 开始探索会话: {session_id}, 应用: {app_id}, 模式: {mode.value}")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ExplorationSession]:
        """获取探索会话"""
        return self._active_sessions.get(session_id)
    
    def end_exploration(self, session_id: str) -> Dict[str, Any]:
        """
        结束探索会话
        
        Returns:
            探索统计信息
        """
        session = self._active_sessions.pop(session_id, None)
        if not session:
            return {"error": "会话不存在"}
        
        duration = (datetime.utcnow() - session.started_at).total_seconds()
        
        stats = {
            "session_id": session_id,
            "app_id": session.app_id,
            "mode": session.mode.value,
            "duration_seconds": duration,
            "transitions_count": session.transitions_count,
            "pages_discovered": session.pages_discovered
        }
        
        logger.info(f"[探索] 结束探索会话: {session_id}, 发现页面: {session.pages_discovered}, 跳转: {session.transitions_count}")
        
        return stats
    
    # ==================== 页面签名 ====================
    
    def generate_page_signature(self, page_data: Dict[str, Any]) -> str:
        """
        生成页面特征签名，用于判断是否是同一个页面
        
        策略：
        1. 页面类型 + 页面名称
        2. 元素的结构特征（类型分布、数量）
        3. 关键元素的文本（如标题、Tab）
        
        Args:
            page_data: 页面分析数据
            
        Returns:
            str: 页面签名（MD5）
        """
        signature_parts = [
            page_data.get("page_type", "unknown"),
            page_data.get("page_name", ""),
        ]
        
        # 元素结构特征
        elements = page_data.get("elements", [])
        type_counts = {}
        key_texts = []
        
        for elem in elements:
            elem_type = elem.get("type") or elem.get("element_type", "unknown")
            type_counts[elem_type] = type_counts.get(elem_type, 0) + 1
            
            # 收集关键文本（导航、Tab、标题）
            if elem_type in ["nav_item", "tab", "title", "back_button"]:
                text = elem.get("text_content") or elem.get("name", "")
                if text:
                    key_texts.append(text)
        
        # 排序确保一致性
        signature_parts.append(json.dumps(sorted(type_counts.items()), ensure_ascii=False))
        signature_parts.append("|".join(sorted(set(key_texts))[:5]))  # 最多取5个关键文本
        
        # 生成 hash
        signature_str = "::".join(signature_parts)
        signature = hashlib.md5(signature_str.encode()).hexdigest()
        
        logger.debug(f"[页面签名] 输入: {signature_str[:100]}... => {signature}")
        
        return signature
    
    # ==================== 跳转记录 ====================
    
    async def record_transition(
        self,
        session_id: str,
        trigger_element: Dict[str, Any],
        action_type: str,
        to_page_screenshot: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        记录一次页面跳转
        
        流程：
        1. 获取会话，验证当前页面
        2. 分析目标页面截图
        3. 生成页面签名，判断是否已存在
        4. 如果是新页面，创建页面节点
        5. 创建跳转边
        6. 更新触发元素的导航信息
        
        Args:
            session_id: 探索会话 ID
            trigger_element: 触发跳转的元素信息
            action_type: 操作类型（click/swipe/input）
            to_page_screenshot: 目标页面截图 (base64)
            model_id: 分析用的模型 ID
            
        Returns:
            跳转记录结果
        """
        # 1. 获取会话
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "error": "探索会话不存在或已过期"}
        
        from_page_id = session.current_page_id
        if not from_page_id:
            return {"success": False, "error": "当前页面未知，请先分析当前页面"}
        
        logger.info(f"[探索] 记录跳转: 从页面 {from_page_id}, 触发元素: {trigger_element.get('name')}")
        
        # 2. 分析目标页面
        try:
            to_page_data = await self._analyze_page(
                session.app_id,
                session.device_udid,
                to_page_screenshot,
                model_id
            )
        except Exception as e:
            logger.error(f"[探索] 分析目标页面失败: {e}")
            return {"success": False, "error": f"分析目标页面失败: {str(e)}"}
        
        # 3. 生成页面签名
        signature = self.generate_page_signature(to_page_data)
        
        # 4. 查找是否已存在该页面
        existing_page = self._find_page_by_signature(session.app_id, signature)
        
        if existing_page:
            # 页面已存在，更新访问次数
            to_page_id = existing_page.id
            to_page_name = existing_page.page_name
            existing_page.visit_count = (existing_page.visit_count or 1) + 1
            self.db.commit()
            is_new_page = False
            logger.info(f"[探索] 目标页面已存在: {to_page_name} (访问次数: {existing_page.visit_count})")
        else:
            # 创建新页面
            from_page = self.page_repo.get_by_id(from_page_id)
            from_depth = from_page.depth if from_page else 0
            
            to_page_data["page_signature"] = signature
            to_page_data["depth"] = from_depth + 1
            
            save_result = await self.knowledge_service.save_analysis_result(
                app_id=session.app_id,
                device_udid=session.device_udid,
                screenshot_hash=hashlib.md5(to_page_screenshot[:1000].encode()).hexdigest(),
                analysis_data=to_page_data,
                processing_time=0
            )
            
            to_page_id = save_result.get("page_id")
            to_page_name = to_page_data.get("page_name", "未知页面")
            is_new_page = True
            session.pages_discovered += 1
            logger.info(f"[探索] 发现新页面: {to_page_name}, depth={from_depth + 1}")
        
        # 5. 创建跳转边
        transition = self._create_transition(
            from_page_id=from_page_id,
            to_page_id=to_page_id,
            to_page_name=to_page_name,
            trigger_element=trigger_element,
            action_type=action_type
        )
        session.transitions_count += 1
        
        # 6. 更新触发元素的导航信息
        self._update_element_navigation(
            element_id=trigger_element.get("id"),
            target_page_id=to_page_id,
            target_page_name=to_page_name
        )
        
        # 7. 更新会话的当前页面
        session.current_page_id = to_page_id
        
        return {
            "success": True,
            "is_new_page": is_new_page,
            "transition_id": transition.id if transition else None,
            "to_page": {
                "id": to_page_id,
                "name": to_page_name,
                "signature": signature,
                "is_new": is_new_page
            },
            "session_stats": {
                "pages_discovered": session.pages_discovered,
                "transitions_count": session.transitions_count
            }
        }
    
    def _find_page_by_signature(self, app_id: str, signature: str) -> Optional[PageAnalysis]:
        """根据签名查找页面"""
        return self.db.query(PageAnalysis).filter(
            PageAnalysis.app_id == app_id,
            PageAnalysis.page_signature == signature
        ).first()
    
    def _create_transition(
        self,
        from_page_id: str,
        to_page_id: str,
        to_page_name: str,
        trigger_element: Dict[str, Any],
        action_type: str
    ) -> Optional[PageTransition]:
        """创建跳转记录"""
        try:
            # 获取起始页面名称
            from_page = self.page_repo.get_by_id(from_page_id)
            from_page_name = from_page.page_name if from_page else "未知页面"
            
            # 检查是否已存在相同的跳转
            existing = self.db.query(PageTransition).filter(
                PageTransition.from_page_id == from_page_id,
                PageTransition.to_page_id == to_page_id,
                PageTransition.trigger_element_name == trigger_element.get("name")
            ).first()
            
            if existing:
                logger.info(f"[探索] 跳转关系已存在: {from_page_name} -> {to_page_name}")
                return existing
            
            transition = PageTransition(
                from_page_id=from_page_id,
                to_page_id=to_page_id,
                from_page_name=from_page_name,
                to_page_name=to_page_name,
                trigger_element_id=trigger_element.get("id"),
                trigger_element_name=trigger_element.get("name"),
                trigger_element_locator=trigger_element.get("midscene_locator") or trigger_element.get("locator"),
                transition_type=action_type,
                transition_description=f"在「{from_page_name}」点击「{trigger_element.get('name')}」，跳转到「{to_page_name}」"
            )
            
            self.db.add(transition)
            self.db.commit()
            
            logger.info(f"[探索] 创建跳转: {from_page_name} --[{trigger_element.get('name')}]--> {to_page_name}")
            
            return transition
            
        except Exception as e:
            logger.error(f"[探索] 创建跳转失败: {e}")
            self.db.rollback()
            return None
    
    def _update_element_navigation(
        self,
        element_id: Optional[str],
        target_page_id: str,
        target_page_name: str
    ):
        """更新元素的导航信息"""
        if not element_id:
            return
        
        try:
            element = self.element_repo.get_by_id(element_id)
            if element:
                element.is_navigation = True
                element.target_page_id = target_page_id
                element.target_page_name = target_page_name
                self.db.commit()
                logger.debug(f"[探索] 更新元素导航: {element.element_name} -> {target_page_name}")
        except Exception as e:
            logger.error(f"[探索] 更新元素导航失败: {e}")
            self.db.rollback()
    
    async def _analyze_page(
        self,
        app_id: str,
        device_udid: str,
        screenshot: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """分析页面截图"""
        result = await self.analyzer_service.analyze_screenshot(
            image_data=screenshot,
            context_hint=None,
            model_id=model_id
        )
        
        if not result.get("success"):
            raise Exception(result.get("error", "分析失败"))
        
        return result.get("data", {})
    
    # ==================== 知识图谱查询 ====================
    
    def get_app_graph(self, app_id: str) -> Dict[str, Any]:
        """
        获取 App 的知识图谱
        
        Returns:
            {
                "pages": [...],
                "transitions": [...],
                "statistics": {...}
            }
        """
        # 获取所有页面
        pages = self.db.query(PageAnalysis).filter(
            PageAnalysis.app_id == app_id
        ).all()
        
        # 获取所有跳转
        page_ids = [p.id for p in pages]
        transitions = self.db.query(PageTransition).filter(
            PageTransition.from_page_id.in_(page_ids)
        ).all()
        
        # 统计
        total_elements = sum(p.elements_count or 0 for p in pages)
        nav_elements = self.db.query(PageElement).filter(
            PageElement.page_id.in_(page_ids),
            PageElement.is_navigation == True
        ).count()
        
        return {
            "pages": [
                {
                    "id": p.id,
                    "name": p.page_name,
                    "type": p.page_type,
                    "depth": p.depth,
                    "visit_count": p.visit_count,
                    "elements_count": p.elements_count
                }
                for p in pages
            ],
            "transitions": [t.to_dict() for t in transitions],
            "statistics": {
                "total_pages": len(pages),
                "total_transitions": len(transitions),
                "total_elements": total_elements,
                "navigation_elements": nav_elements,
                "max_depth": max((p.depth or 0) for p in pages) if pages else 0
            }
        }
    
    def find_path(
        self,
        app_id: str,
        from_page_name: str,
        to_page_name: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        查找从 A 页面到 B 页面的操作路径（BFS）
        
        Returns:
            操作路径列表，每项包含 page、action 信息
        """
        # 查找起始和目标页面
        from_page = self.db.query(PageAnalysis).filter(
            PageAnalysis.app_id == app_id,
            PageAnalysis.page_name.like(f"%{from_page_name}%")
        ).first()
        
        to_page = self.db.query(PageAnalysis).filter(
            PageAnalysis.app_id == app_id,
            PageAnalysis.page_name.like(f"%{to_page_name}%")
        ).first()
        
        if not from_page or not to_page:
            return None
        
        # BFS 搜索
        from collections import deque
        
        queue = deque([(from_page.id, [])])  # (current_page_id, path)
        visited = {from_page.id}
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id == to_page.id:
                # 找到路径
                return path + [{"page": to_page.page_name, "action": None}]
            
            # 获取当前页面的所有跳转
            transitions = self.db.query(PageTransition).filter(
                PageTransition.from_page_id == current_id
            ).all()
            
            for trans in transitions:
                if trans.to_page_id not in visited:
                    visited.add(trans.to_page_id)
                    new_path = path + [{
                        "page": trans.from_page_name,
                        "action": f"点击「{trans.trigger_element_name}」",
                        "locator": trans.trigger_element_locator
                    }]
                    queue.append((trans.to_page_id, new_path))
        
        return None  # 未找到路径
    
    def get_page_transitions(self, page_id: str) -> Dict[str, Any]:
        """获取页面的所有跳转关系"""
        # 出向跳转
        outgoing = self.db.query(PageTransition).filter(
            PageTransition.from_page_id == page_id
        ).all()
        
        # 入向跳转
        incoming = self.db.query(PageTransition).filter(
            PageTransition.to_page_id == page_id
        ).all()
        
        return {
            "outgoing": [t.to_dict() for t in outgoing],
            "incoming": [t.to_dict() for t in incoming]
        }
