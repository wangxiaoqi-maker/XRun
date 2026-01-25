"""
Sonic 平台服务封装
提供设备管理、投屏、远程控制等功能
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
class SonicDevice:
    """Sonic 设备信息"""
    id: int
    udid: str
    name: str
    model: str
    platform: Platform
    version: str
    manufacturer: str
    resolution: str
    status: str  # ONLINE, OFFLINE, TESTING, ERROR
    agent_id: int
    agent_host: str
    agent_port: int
    
    @property
    def is_online(self) -> bool:
        # ONLINE: 在线空闲, DEBUGGING: 调试中, TESTING: 测试中
        return self.status in ("ONLINE", "DEBUGGING", "TESTING")
    
    @property
    def screen_ws_url(self) -> str:
        """获取投屏 WebSocket URL - 连接 Sonic Agent"""
        if self.platform == Platform.ANDROID:
            return f"ws://{self.agent_host}:{self.agent_port}/websockets/android/{self.udid}"
        else:
            return f"ws://{self.agent_host}:{self.agent_port}/websockets/ios/{self.udid}"
    
    @property
    def touch_ws_url(self) -> str:
        """获取触控 WebSocket URL（与 screen_ws_url 相同，Sonic 使用同一连接）"""
        return self.screen_ws_url


class SonicService:
    """Sonic 服务封装"""
    
    def __init__(self):
        self.base_url = settings.SONIC_SERVER_URL
        self.secret_key = settings.SONIC_SECRET_KEY
        self._token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0
            )
        return self._client
    
    async def _get_token(self) -> str:
        """获取访问令牌"""
        if self._token:
            return self._token
        
        client = await self._get_client()
        
        # 使用 Sonic 默认账户登录
        response = await client.post("/server/api/controller/users/login", json={
            "userName": "sonic",
            "password": "sonic"  # Sonic 默认密码
        })
        
        if response.status_code == 200:
            resp_data = response.json()
            if resp_data.get("code") == 2000:
                # data 直接是 token 字符串
                self._token = resp_data.get("data", "")
                return self._token
        
        raise Exception("Sonic 登录失败")

    async def get_token(self) -> str:
        """获取访问令牌（公开方法）"""
        return await self._get_token()
    
    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """发送请求"""
        client = await self._get_client()
        token = await self._get_token()
        
        headers = kwargs.pop("headers", {})
        headers["SonicToken"] = token
        
        response = await client.request(method, path, headers=headers, **kwargs)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 2000:
                return data.get("data", {})
            raise Exception(data.get("message", "请求失败"))
        
        raise Exception(f"HTTP {response.status_code}")
    
    async def get_agents(self) -> List[Dict]:
        """获取所有 Agent"""
        try:
            data = await self._request("GET", "/server/api/controller/agents/list")
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"获取 Agents 失败: {e}")
            return []
    
    async def get_devices(self, platform: Optional[Platform] = None) -> List[SonicDevice]:
        """获取设备列表"""
        try:
            # 先获取所有 agents
            agents = await self.get_agents()
            agent_map = {a["id"]: a for a in agents}
            
            devices = []
            
            # 遍历每个 agent 获取设备
            for agent in agents:
                agent_id = agent.get("id")
                try:
                    data = await self._request(
                        "GET", 
                        "/server/api/controller/devices/listByAgentId",
                        params={"agentId": agent_id}
                    )
                    
                    for item in data if isinstance(data, list) else []:
                        # 过滤平台
                        item_platform = Platform.ANDROID if item.get("platform") == 1 else Platform.IOS
                        if platform and item_platform != platform:
                            continue
                        
                        # 解析分辨率
                        size = item.get("size", "0x0")
                        
                        devices.append(SonicDevice(
                            id=item.get("id", 0),
                            udid=item.get("udId", ""),
                            name=item.get("nickName") or item.get("name") or item.get("model", "Unknown"),
                            model=item.get("model", ""),
                            platform=item_platform,
                            version=item.get("version", ""),
                            manufacturer=item.get("manufacturer", ""),
                            resolution=size,
                            status=item.get("status", "OFFLINE"),
                            agent_id=agent_id,
                            agent_host=agent.get("host", "localhost"),
                            agent_port=agent.get("port", 7777)
                        ))
                except Exception as e:
                    logger.warning(f"获取 Agent {agent_id} 设备失败: {e}")
            
            return devices
            
        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")
            return []
    
    async def get_device(self, udid: str) -> Optional[SonicDevice]:
        """获取单个设备"""
        devices = await self.get_devices()
        for device in devices:
            if device.udid == udid:
                return device
        return None
    
    async def get_online_devices(self) -> List[SonicDevice]:
        """获取在线设备"""
        devices = await self.get_devices()
        return [d for d in devices if d.is_online]
    
    async def occupy_device(self, device_id: int, user_id: int = 1) -> bool:
        """占用设备"""
        try:
            await self._request(
                "GET", 
                f"/server/api/controller/devices/occupy/{device_id}",
                params={"userId": user_id}
            )
            return True
        except Exception as e:
            logger.error(f"占用设备失败: {e}")
            return False
    
    async def release_device(self, device_id: int) -> bool:
        """释放设备"""
        try:
            await self._request("GET", f"/server/api/controller/devices/release/{device_id}")
            return True
        except Exception as e:
            logger.error(f"释放设备失败: {e}")
            return False
    
    async def screenshot(self, udid: str) -> Optional[bytes]:
        """截图"""
        device = await self.get_device(udid)
        if not device:
            return None
        
        try:
            client = await self._get_client()
            token = await self._get_token()
            
            if device.platform == Platform.ANDROID:
                url = f"http://{device.agent_host}:{device.agent_port}/api/android/screenshot/{udid}"
            else:
                url = f"http://{device.agent_host}:{device.agent_port}/api/ios/screenshot/{udid}"
            
            response = await client.get(url, headers={"SonicToken": token})
            
            if response.status_code == 200:
                return response.content
            return None
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    async def tap(self, udid: str, x: int, y: int) -> bool:
        """点击"""
        device = await self.get_device(udid)
        if not device:
            return False
        
        try:
            client = await self._get_client()
            
            if device.platform == Platform.ANDROID:
                url = f"http://{device.agent_host}:{device.agent_port}/api/android/touch/tap/{udid}"
            else:
                url = f"http://{device.agent_host}:{device.agent_port}/api/ios/touch/tap/{udid}"
            
            await client.post(url, json={"x": x, "y": y})
            return True
            
        except Exception as e:
            logger.error(f"点击失败: {e}")
            return False
    
    async def swipe(self, udid: str, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 300) -> bool:
        """滑动"""
        device = await self.get_device(udid)
        if not device:
            return False
        
        try:
            client = await self._get_client()
            
            if device.platform == Platform.ANDROID:
                url = f"http://{device.agent_host}:{device.agent_port}/api/android/touch/swipe/{udid}"
            else:
                url = f"http://{device.agent_host}:{device.agent_port}/api/ios/touch/swipe/{udid}"
            
            await client.post(url, json={
                "startX": start_x,
                "startY": start_y,
                "endX": end_x,
                "endY": end_y,
                "duration": duration
            })
            return True
            
        except Exception as e:
            logger.error(f"滑动失败: {e}")
            return False
    
    async def input_text(self, udid: str, text: str) -> bool:
        """输入文本"""
        device = await self.get_device(udid)
        if not device:
            return False
        
        try:
            client = await self._get_client()
            
            if device.platform == Platform.ANDROID:
                url = f"http://{device.agent_host}:{device.agent_port}/api/android/input/{udid}"
            else:
                url = f"http://{device.agent_host}:{device.agent_port}/api/ios/input/{udid}"
            
            await client.post(url, json={"text": text})
            return True
            
        except Exception as e:
            logger.error(f"输入失败: {e}")
            return False
    
    async def key_event(self, udid: str, key: str) -> bool:
        """按键事件（Android）"""
        device = await self.get_device(udid)
        if not device or device.platform != Platform.ANDROID:
            return False
        
        try:
            client = await self._get_client()
            url = f"http://{device.agent_host}:{device.agent_port}/api/android/key/{udid}"
            
            key_codes = {
                "back": 4,
                "home": 3,
                "menu": 82,
                "power": 26,
                "volume_up": 24,
                "volume_down": 25
            }
            
            await client.post(url, json={"keyCode": key_codes.get(key, 0)})
            return True
            
        except Exception as e:
            logger.error(f"按键失败: {e}")
            return False
    
    async def home(self, udid: str) -> bool:
        """Home 键"""
        device = await self.get_device(udid)
        if not device:
            return False
        
        if device.platform == Platform.ANDROID:
            return await self.key_event(udid, "home")
        else:
            try:
                client = await self._get_client()
                url = f"http://{device.agent_host}:{device.agent_port}/api/ios/home/{udid}"
                await client.get(url)
                return True
            except:
                return False
    
    async def back(self, udid: str) -> bool:
        """返回键"""
        device = await self.get_device(udid)
        if not device:
            return False
        
        if device.platform == Platform.ANDROID:
            return await self.key_event(udid, "back")
        else:
            # iOS 没有返回键，模拟左滑
            return await self.swipe(udid, 10, 400, 300, 400, 200)
    
    async def launch_app(self, udid: str, package: str, activity: str = "") -> bool:
        """启动应用"""
        device = await self.get_device(udid)
        if not device:
            return False
        
        try:
            client = await self._get_client()
            
            if device.platform == Platform.ANDROID:
                url = f"http://{device.agent_host}:{device.agent_port}/api/android/app/launch/{udid}"
                await client.post(url, json={"package": package, "activity": activity})
            else:
                url = f"http://{device.agent_host}:{device.agent_port}/api/ios/app/launch/{udid}"
                await client.post(url, json={"bundleId": package})
            
            return True
            
        except Exception as e:
            logger.error(f"启动应用失败: {e}")
            return False
    
    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None


# 单例
sonic_service = SonicService()

