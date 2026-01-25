"""
iOS 设备监听与管理服务 (本地 tidevice 实现)
用于在 Sonic Agent 不可用时作为 Fallback
"""
import asyncio
import subprocess
import re
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum
import threading
import time

class IOSDeviceStatus(str, Enum):
    """iOS 设备状态"""
    ONLINE = "online"
    READY = "ready" 
    MIRRORING = "mirroring" 
    OFFLINE = "offline"


@dataclass
class IOSDevice:
    """iOS 设备信息"""
    udid: str
    name: str = "iPhone"
    model: str = "iPhone"
    version: str = "unknown"
    status: IOSDeviceStatus = IOSDeviceStatus.OFFLINE
    wda_port: int = 0
    mjpeg_port: int = 0
    conn_type: str = "USB"
    
    def to_dict(self) -> dict:
        return {
            "udid": self.udid,
            "name": self.name,
            "model": self.model,
            "version": self.version,
            "platform": "ios",
            "status": self.status.value,
            "wda_port": self.wda_port,
            "mjpeg_port": self.mjpeg_port,
            "conn_type": self.conn_type
        }


class IOSDeviceService:
    """
    iOS 设备服务 (基于 tidevice CLI)
    """
    
    def __init__(self):
        self.devices: Dict[str, IOSDevice] = {}
        self._wda_processes: Dict[str, subprocess.Popen] = {}
        self._next_port = 8100
        # 初始加载
        self.refresh_devices()
    
    def get_device(self, udid: str) -> Optional[IOSDevice]:
        self.refresh_devices() # 确保最新
        return self.devices.get(udid)
    
    def get_all_devices(self) -> List[IOSDevice]:
        self.refresh_devices()
        return list(self.devices.values())
        
    def refresh_devices(self):
        """调用 tidevice list 刷新设备列表"""
        try:
            # tidevice list 输出示例:
            # UDID                       SerialNumber    NAME      MarketName    ProductVersion    ConnType
            # 00008140-0001791E3E2B001C  KV9Y96393K      iPhone16  -             18.6.2            ConnectionType.USB
            
            result = subprocess.run(['tidevice', 'list'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print(f"tidevice list failed: {result.stderr}")
                return

            lines = result.stdout.strip().split('\n')
            current_devices = {}
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 2 and parts[0] != "UDID": # 跳过标题行
                    udid = parts[0]
                    # 简单解析
                    name = "iPhone"
                    version = "unknown"
                    conn_type = "USB"
                    
                    # 尝试更智能的解析 (列宽不定，parts 数量不定)
                    # 简单策略：parts[0]=UDID, parts[2]=Name
                    if len(parts) >= 3:
                        name = parts[2]
                        
                    # 查找版本号 (通常是第5列，但也可能变)
                    # 查找类似 x.x.x 的 pattern
                    for part in parts:
                        if re.match(r'^\d+(\.\d+)+$', part):
                            version = part
                            
                    # 查找 ConnType
                    if "USB" in line:
                        conn_type = "USB"
                    elif "Network" in line:
                        conn_type = "Network"

                    device = self.devices.get(udid)
                    if not device:
                        device = IOSDevice(udid=udid, status=IOSDeviceStatus.ONLINE)
                    
                    device.name = name
                    device.version = version
                    device.conn_type = conn_type
                    device.status = IOSDeviceStatus.ONLINE # 只要列出来就是 Online
                    
                    current_devices[udid] = device
            
            # 标记已移除的设备为 Offline
            for udid in list(self.devices.keys()):
                if udid not in current_devices:
                    self.devices[udid].status = IOSDeviceStatus.OFFLINE
            
            # 更新列表
            self.devices.update(current_devices)
            
        except Exception as e:
            print(f"刷新 iOS 设备异常: {e}")

    # --- WDA 管理 ---

    async def start_wda(self, udid: str) -> Optional[int]:
        """
        启动 WDA (tidevice wdaproxy)
        """
        if udid in self._wda_processes:
            # 检查是否还在运行
            proc = self._wda_processes[udid]
            if proc.poll() is None:
                return self.devices[udid].wda_port
            else:
                del self._wda_processes[udid]

        port = self._next_port
        self._next_port += 1
        
        # 常见 Bundle IDs
        bundle_ids = [
            "com.facebook.WebDriverAgentRunner.xctrunner",
            "com.facebook.wda.runner",
            "com.appium.WebDriverAgentRunner.xctrunner"
        ]
        
        # 简单尝试第一个 (后续可优化为自动检测或轮询)
        bundle_id = bundle_ids[0]

        print(f"Starting WDA for {udid} on port {port} using {bundle_id}...")
        
        try:
            # tidevice -u <udid> wdaproxy -B <bundle_id> --port <port>
            cmd = ["tidevice", "-u", udid, "wdaproxy", "-B", bundle_id, "--port", str(port)]
            
            # 使用 subprocess.Popen 启动后台进程
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self._wda_processes[udid] = proc
            
            # 简单等待几秒让其启动 (生产环境应解析 stdout)
            await asyncio.sleep(2)
            
            if proc.poll() is not None:
                # 启动失败
                out, err = proc.communicate()
                print(f"WDA Start Failed: {err}")
                return None
                
            # 更新设备信息
            if udid in self.devices:
                self.devices[udid].wda_port = port
                self.devices[udid].status = IOSDeviceStatus.ONLINE
                
            return port
            
        except Exception as e:
            print(f"Start WDA Exception: {e}")
            return None

    # --- 以下为 Stub 方法保持兼容 ---

    def add_callback(self, callback: Callable):
        pass
    
    def remove_callback(self, callback: Callable):
        pass
    
    async def start_mirror(self, udid: str) -> Optional[str]:
        return None
        
    async def stop_mirror(self, udid: str):
        pass
        
    async def tap(self, udid: str, x: int, y: int) -> bool:
        return False
        
    async def swipe(self, udid: str, from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.3) -> bool:
        return False
        
    async def home(self, udid: str) -> bool:
        return False

    async def stop(self):
        self._running = False
        # Terminate WDA processes
        for udid, proc in self._wda_processes.items():
            if proc.poll() is None:
                proc.terminate()
        self._wda_processes.clear()

    async def _scan_devices(self):
        """Async wrapper for refresh_devices"""
        self.refresh_devices()

    async def _watch_devices(self):
        """Watch loop"""
        while getattr(self, '_running', False):
            self.refresh_devices()
            await asyncio.sleep(5)

# 全局单例
ios_device_service = IOSDeviceService()
