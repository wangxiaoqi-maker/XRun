"""
测试用例 Schema
"""
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum

class Platform(str, Enum):
    ANDROID = "android"
    IOS = "ios"

# ===== 用例步骤定义 =====

class StepType(str, Enum):
    """步骤类型"""
    AI_TAP = "aiTap"
    AI_INPUT = "aiInput"
    AI_SWIPE = "aiSwipe"
    AI_ASSERT = "aiAssert"
    AI_WAIT = "aiWait"
    AI_QUERY = "aiQuery"
    TAP = "tap"
    SWIPE = "swipe"
    INPUT = "input"
    BACK = "back"
    HOME = "home"
    LAUNCH = "launch"
    SLEEP = "sleep"
    SCREENSHOT = "screenshot"

class TestStep(BaseModel):
    """测试步骤"""
    type: StepType
    description: Optional[str] = None
    # AI 操作参数
    prompt: Optional[str] = None
    # 坐标操作参数
    x: Optional[int] = None
    y: Optional[int] = None
    startX: Optional[int] = None
    startY: Optional[int] = None
    endX: Optional[int] = None
    endY: Optional[int] = None
    # 其他参数
    text: Optional[str] = None
    duration: Optional[int] = None
    timeout: Optional[int] = None
    package: Optional[str] = None
    activity: Optional[str] = None
    bundleId: Optional[str] = None

class TestCaseYAML(BaseModel):
    """YAML 格式的用例结构"""
    name: str
    description: Optional[str] = None
    platform: Platform
    steps: List[TestStep]
    
# ===== API Schema =====

class TestCaseCreate(BaseModel):
    """创建用例"""
    name: str
    description: Optional[str] = None
    platform: Platform
    yaml_content: str  # YAML 字符串
    tags: Optional[List[str]] = []

class TestCaseUpdate(BaseModel):
    """更新用例"""
    name: Optional[str] = None
    description: Optional[str] = None
    yaml_content: Optional[str] = None
    tags: Optional[List[str]] = None

class TestCaseResponse(BaseModel):
    """用例响应"""
    id: str
    name: str
    description: Optional[str]
    platform: str
    yaml_content: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TestCaseList(BaseModel):
    """用例列表"""
    total: int
    items: List[TestCaseResponse]
