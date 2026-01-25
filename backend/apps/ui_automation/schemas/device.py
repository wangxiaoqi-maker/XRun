"""
设备相关的 Pydantic Schema
"""
from pydantic import BaseModel
from typing import List, Optional

class DeviceInfo(BaseModel):
    """设备信息"""
    id: str
    udid: str
    name: str
    platform: str  # android / ios
    model: Optional[str] = None
    os_version: Optional[str] = None
    resolution: Optional[str] = None
    status: str = "connected"  # connected / offline / testing
    manufacturer: Optional[str] = None
    
    # Sonic 相关
    agent_id: Optional[int] = None
    agent_host: Optional[str] = None
    agent_port: Optional[int] = None
    screen_ws_url: Optional[str] = None  # 投屏 WebSocket URL
    touch_ws_url: Optional[str] = None   # 触控 WebSocket URL

class DeviceList(BaseModel):
    """设备列表"""
    android: List[DeviceInfo] = []
    ios: List[DeviceInfo] = []
    source: str = "local"  # local / sonic
