"""
Sonic Agent 直连服务
直接连接到 Sonic Agent，无需 Sonic Server
"""
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from apps.ui_automation.config import settings


class Platform(str, Enum):
    ANDROID = "android"
    IOS = "ios"


@dataclass
class AgentDevice:
    """Agent 设备信息"""
    udid: str
    name: str
    model: str
    platform: Platform
    version: str
    manufacturer: str
    resolution: str
    status: str
    agent_host: str
    agent_port: int
    
    @property
    def is_online(self) -> bool:
        return self.status == "ONLINE"
    
    @property
    def screen_ws_url(self) -> str:
        """投屏 WebSocket URL"""
        if self.platform == Platform.ANDROID:
            return f"ws://{self.agent_host}:{self.agent_port}/websockets/android/screen/{self.udid}"
        else:
            return f"ws://{self.agent_host}:{self.agent_port}/websockets/ios/screen/{self.udid}"
    
    @property
    def touch_ws_url(self) -> str:
        """触控 WebSocket URL"""
        if self.platform == Platform.ANDROID:
            return f"ws://{self.agent_host}:{self.agent_port}/websockets/android/touch/{self.udid}"
        else:
            return f"ws://{self.agent_host}:{self.agent_port}/websockets/ios/touch/{self.udid}"


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    host: str
    port: int = 7912
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class SonicAgentService:
    """Sonic Agent 直连服务"""
    
    def __init__(self):
        self.agents: List[AgentConfig] = []
        self._load_agents()
    
    def _load_agents(self):
        """加载 Agent 配置"""
        # 从环境变量或配置加载
        # 格式: SONIC_AGENTS=name1:host1:port1,name2:host2:port2
        agents_str = getattr(settings, 'SONIC_AGENTS', '')
        
        if agents_str:
            for agent_str in agents_str.split(','):
                parts = agent_str.strip().split(':')
                if len(parts) >= 2:
                    name = parts[0]
                    host = parts[1]
                    port = int(parts[2]) if len(parts) > 2 else 7912
                    self.agents.append(AgentConfig(name=name, host=host, port=port))
        
        # 默认添加本地 Agent
        if not self.agents:
            self.agents.append(AgentConfig(name="本地", host="127.0.0.1", port=7912))
    
    def add_agent(self, name: str, host: str, port: int = 7912):
        """添加 Agent"""
        self.agents.append(AgentConfig(name=name, host=host, port=port))
    
    async def check_agent_health(self, agent: AgentConfig) -> bool:
        """检查 Agent 健康状态"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{agent.base_url}/api/folder/init")
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Agent {agent.name} 不可用: {e}")
            return False
    
    async def get_online_agents(self) -> List[AgentConfig]:
        """获取在线的 Agent"""
        online = []
        for agent in self.agents:
            if await self.check_agent_health(agent):
                online.append(agent)
        return online
    
    async def get_devices_from_agent(self, agent: AgentConfig) -> List[AgentDevice]:
        """从单个 Agent 获取设备列表"""
        devices = []
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # 获取 Android 设备
                try:
                    response = await client.get(f"{agent.base_url}/api/android/devices")
                    if response.status_code == 200:
                        data = response.json()
                        for item in data.get("data", []) if isinstance(data, dict) else data:
                            devices.append(AgentDevice(
                                udid=item.get("udId", item.get("serial", "")),
                                name=item.get("model", "Android Device"),
                                model=item.get("model", ""),
                                platform=Platform.ANDROID,
                                version=item.get("version", ""),
                                manufacturer=item.get("manufacturer", ""),
                                resolution=f"{item.get('screenWidth', 0)}x{item.get('screenHeight', 0)}",
                                status="ONLINE",
                                agent_host=agent.host,
                                agent_port=agent.port
                            ))
                except Exception as e:
                    logger.debug(f"获取 Android 设备失败: {e}")
                
                # 获取 iOS 设备
                try:
                    response = await client.get(f"{agent.base_url}/api/ios/devices")
                    if response.status_code == 200:
                        data = response.json()
                        for item in data.get("data", []) if isinstance(data, dict) else data:
                            devices.append(AgentDevice(
                                udid=item.get("udId", item.get("serialNumber", "")),
                                name=item.get("name", "iOS Device"),
                                model=item.get("model", ""),
                                platform=Platform.IOS,
                                version=item.get("version", ""),
                                manufacturer="Apple",
                                resolution="",
                                status="ONLINE",
                                agent_host=agent.host,
                                agent_port=agent.port
                            ))
                except Exception as e:
                    logger.debug(f"获取 iOS 设备失败: {e}")
                    
        except Exception as e:
            logger.error(f"连接 Agent {agent.name} 失败: {e}")
        
        return devices
    
    async def get_all_devices(self) -> List[AgentDevice]:
        """获取所有 Agent 的设备"""
        all_devices = []
        
        for agent in self.agents:
            devices = await self.get_devices_from_agent(agent)
            all_devices.extend(devices)
        
        return all_devices
    
    async def get_device(self, udid: str) -> Optional[AgentDevice]:
        """根据 udid 获取设备"""
        devices = await self.get_all_devices()
        for device in devices:
            if device.udid == udid:
                return device
        return None
    
    async def screenshot(self, device: AgentDevice) -> Optional[bytes]:
        """截图"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if device.platform == Platform.ANDROID:
                    url = f"http://{device.agent_host}:{device.agent_port}/api/android/screenshot/{device.udid}"
                else:
                    url = f"http://{device.agent_host}:{device.agent_port}/api/ios/screenshot/{device.udid}"
                
                response = await client.get(url)
                if response.status_code == 200:
                    return response.content
        except Exception as e:
            logger.error(f"截图失败: {e}")
        return None
    
    async def tap(self, device: AgentDevice, x: int, y: int) -> bool:
        """点击"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                if device.platform == Platform.ANDROID:
                    url = f"http://{device.agent_host}:{device.agent_port}/api/android/touch/tap"
                    await client.post(url, json={"serial": device.udid, "x": x, "y": y})
                else:
                    url = f"http://{device.agent_host}:{device.agent_port}/api/ios/touch/tap"
                    await client.post(url, json={"udId": device.udid, "x": x, "y": y})
                return True
        except Exception as e:
            logger.error(f"点击失败: {e}")
            return False
    
    async def swipe(self, device: AgentDevice, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 300) -> bool:
        """滑动"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                if device.platform == Platform.ANDROID:
                    url = f"http://{device.agent_host}:{device.agent_port}/api/android/touch/swipe"
                    await client.post(url, json={
                        "serial": device.udid,
                        "startX": start_x, "startY": start_y,
                        "endX": end_x, "endY": end_y,
                        "duration": duration
                    })
                else:
                    url = f"http://{device.agent_host}:{device.agent_port}/api/ios/touch/swipe"
                    await client.post(url, json={
                        "udId": device.udid,
                        "startX": start_x, "startY": start_y,
                        "endX": end_x, "endY": end_y
                    })
                return True
        except Exception as e:
            logger.error(f"滑动失败: {e}")
            return False
    
    async def input_text(self, device: AgentDevice, text: str) -> bool:
        """输入文本"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                if device.platform == Platform.ANDROID:
                    url = f"http://{device.agent_host}:{device.agent_port}/api/android/input"
                    await client.post(url, json={"serial": device.udid, "text": text})
                else:
                    url = f"http://{device.agent_host}:{device.agent_port}/api/ios/input"
                    await client.post(url, json={"udId": device.udid, "text": text})
                return True
        except Exception as e:
            logger.error(f"输入失败: {e}")
            return False
    
    async def key_event(self, device: AgentDevice, key: str) -> bool:
        """按键"""
        if device.platform != Platform.ANDROID:
            return False
        
        key_codes = {
            "back": 4,
            "home": 3,
            "menu": 82,
            "power": 26
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                url = f"http://{device.agent_host}:{device.agent_port}/api/android/key"
                await client.post(url, json={"serial": device.udid, "keyCode": key_codes.get(key, 0)})
                return True
        except Exception as e:
            logger.error(f"按键失败: {e}")
            return False


# 单例
sonic_agent_service = SonicAgentService()








