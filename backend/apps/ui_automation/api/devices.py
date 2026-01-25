"""
设备管理 API - Sonic + ADB 混合模式
解决 Android 15 兼容性问题
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import Response
from typing import List, Optional, TYPE_CHECKING, Any
import asyncio
import base64
import subprocess
import json

from apps.ui_automation.config import settings
from apps.ui_automation.schemas.device import DeviceInfo, DeviceList

# 延迟导入服务
sonic_service = None
Platform = None

if settings.SONIC_ENABLED:
    try:
        from apps.ui_automation.services.sonic_service import sonic_service as _sonic_service, Platform as _Platform
        sonic_service = _sonic_service
        Platform = _Platform
    except ImportError:
        pass

router = APIRouter()

def sonic_device_to_info(device: Any) -> DeviceInfo:
    """转换 Sonic 设备为 DeviceInfo"""
    return DeviceInfo(
        id=str(device.id),
        udid=device.udid,
        name=device.name,
        platform=device.platform.value,
        model=device.model,
        os_version=device.version,
        resolution=device.resolution,
        status="connected" if device.is_online else "offline",
        manufacturer=device.manufacturer,
        agent_id=device.agent_id,
        agent_host=device.agent_host,
        agent_port=device.agent_port,
        screen_ws_url=device.screen_ws_url if device.is_online else None,
        touch_ws_url=device.touch_ws_url if device.is_online else None
    )

@router.get("/", response_model=DeviceList)
async def list_devices():
    """获取所有设备"""
    if settings.SONIC_ENABLED:
        try:
            devices = await sonic_service.get_devices()
            android_devices = [sonic_device_to_info(d) for d in devices if d.platform == Platform.ANDROID]
            ios_devices = [sonic_device_to_info(d) for d in devices if d.platform == Platform.IOS]
            return DeviceList(android=android_devices, ios=ios_devices, source="sonic-server")
        except Exception as e:
            print(f"Sonic Server 获取设备失败: {e}")
            raise HTTPException(status_code=500, detail=f"Sonic Server 获取设备失败: {e}")
    raise HTTPException(status_code=500, detail="Sonic 服务未启用")

@router.get("/android", response_model=List[DeviceInfo])
async def list_android_devices():
    """获取 Android 设备"""
    if settings.SONIC_ENABLED:
        try:
            devices = await sonic_service.get_devices(Platform.ANDROID)
            return [sonic_device_to_info(d) for d in devices]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取 Android 设备失败: {e}")
    raise HTTPException(status_code=500, detail="Sonic 服务未启用")

@router.get("/ios", response_model=List[DeviceInfo])
async def list_ios_devices():
    """获取 iOS 设备"""
    if settings.SONIC_ENABLED:
        try:
            devices = await sonic_service.get_devices(Platform.IOS)
            return [sonic_device_to_info(d) for d in devices]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取 iOS 设备失败: {e}")
    raise HTTPException(status_code=500, detail="Sonic 服务未启用")


# ===== iOS 原生设备服务 API（必须在 /{udid} 之前定义）=====

# 延迟导入 iOS 服务
_ios_device_service = None

def get_ios_service():
    """获取 iOS 设备服务实例"""
    global _ios_device_service
    if _ios_device_service is None:
        try:
            from apps.ui_automation.services.ios_device_service import ios_device_service
            _ios_device_service = ios_device_service
        except ImportError as e:
            print(f"iOS 服务导入失败: {e}")
    return _ios_device_service


@router.get("/ios/native")
async def list_ios_native_devices():
    """获取原生 iOS 设备列表（本地 tidevice 检测）"""
    service = get_ios_service()
    if not service:
        return {"devices": [], "source": "tidevice", "error": "iOS 服务未启动"}
    
    devices = service.get_all_devices()
    return {
        "devices": [d.to_dict() for d in devices],
        "source": "tidevice"
    }


@router.post("/ios/native/{udid}/start-wda")
async def start_ios_wda(udid: str):
    """为 iOS 设备启动 WDA"""
    service = get_ios_service()
    if not service:
        raise HTTPException(status_code=500, detail="iOS 服务未初始化")
    
    device = service.get_device(udid)
    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")
    
    return {
        "udid": udid,
        "status": device.status.value,
        "wda_port": device.wda_port,
        "mjpeg_port": device.mjpeg_port
    }


@router.get("/ios/native/{udid}/mjpeg")
async def ios_mjpeg_proxy_early(udid: str):
    """代理 iOS MJPEG 流"""
    from fastapi.responses import StreamingResponse
    import httpx
    
    service = get_ios_service()
    if not service:
        raise HTTPException(status_code=500, detail="iOS 服务未初始化")
    
    device = service.get_device(udid)
    if not device or device.mjpeg_port == 0:
        raise HTTPException(status_code=404, detail="设备未就绪或 WDA 未启动")
    
    mjpeg_url = f"http://localhost:{device.mjpeg_port}"
    
    async def stream_mjpeg():
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", mjpeg_url, timeout=None) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
    
    return StreamingResponse(
        stream_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=--BoundaryString"
    )

@router.get("/{udid}", response_model=DeviceInfo)
async def get_device(udid: str):
    """获取单个设备"""
    if settings.SONIC_ENABLED:
        device = await sonic_service.get_device(udid)
        if device:
            return sonic_device_to_info(device)
    raise HTTPException(status_code=404, detail="设备未找到")


# ===== ADB 直接操作（解决 Android 15 投屏兼容性问题）=====

def adb_screenshot(udid: str) -> bytes:
    """使用 ADB 截图"""
    try:
        result = subprocess.run(
            ["adb", "-s", udid, "exec-out", "screencap", "-p"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except Exception as e:
        print(f"ADB 截图失败: {e}")
    return None

def adb_tap(udid: str, x: int, y: int) -> bool:
    """使用 ADB 点击"""
    try:
        result = subprocess.run(
            ["adb", "-s", udid, "shell", "input", "tap", str(x), str(y)],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"ADB 点击失败: {e}")
    return False

def adb_swipe(udid: str, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
    """使用 ADB 滑动"""
    try:
        result = subprocess.run(
            ["adb", "-s", udid, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"ADB 滑动失败: {e}")
    return False

def adb_input_text(udid: str, text: str) -> bool:
    """使用 ADB 输入文本"""
    try:
        # 替换空格为 %s
        escaped_text = text.replace(" ", "%s")
        result = subprocess.run(
            ["adb", "-s", udid, "shell", "input", "text", escaped_text],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"ADB 输入失败: {e}")
    return False

def adb_keyevent(udid: str, keycode: int) -> bool:
    """使用 ADB 发送按键"""
    try:
        result = subprocess.run(
            ["adb", "-s", udid, "shell", "input", "keyevent", str(keycode)],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"ADB 按键失败: {e}")
    return False# ===== Sonic Agent Proxy (WebSockets) =====

async def proxy_websocket(client_ws: WebSocket, agent_ws_url: str):
    """WebSocket Proxy Logic"""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(agent_ws_url) as agent_ws:
            # 双向转发
            async def forward_client_to_agent():
                try:
                    while True:
                        data = await client_ws.receive_text()
                        await agent_ws.send_str(data)
                except Exception:
                    pass

            async def forward_agent_to_client():
                try:
                    async for msg in agent_ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await client_ws.send_text(msg.data)
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            await client_ws.send_bytes(msg.data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                except Exception:
                    pass

            # 并发执行
            print(f"[Proxy] Connected to Agent: {agent_ws_url}")
            await asyncio.gather(
                forward_client_to_agent(),
                forward_agent_to_client(),
                return_exceptions=True
            )
            print(f"[Proxy] Connection closed")

@router.websocket("/{udid}/agent/terminal")
async def agent_terminal_ws(websocket: WebSocket, udid: str):
    """Proxy for Sonic Agent Terminal WebSocket (Apps, Logcat, Terminal)"""
    await websocket.accept()
    
    if not settings.SONIC_ENABLED:
        await websocket.close(reason="Sonic disabled")
        return

    try:
        device = await sonic_service.get_device(udid)
        if not device:
            await websocket.close(reason="Device not found")
            return
            
        token = await sonic_service.get_token()
        token = await sonic_service.get_token()
        # Use Agent Key if available, otherwise fallback to Secret Key (but Agent likely needs its own key)
        key = settings.SONIC_AGENT_KEY or settings.SONIC_SECRET_KEY
        
        # Agent URL: /websockets/android/terminal/{key}/{udId}/{token}
        agent_url = f"ws://{device.agent_host}:{device.agent_port}/websockets/android/terminal/{key}/{udid}/{token}"
        print(f"[Terminal WS] Connecting to: {agent_url}")
        
        await proxy_websocket(websocket, agent_url)
        
    except Exception as e:
        print(f"Terminal Proxy Error: {e}")
        try:
            await websocket.close()
        except:
            pass

@router.websocket("/{udid}/agent/general")
async def agent_general_ws(websocket: WebSocket, udid: str):
    """Proxy for Sonic Agent General WebSocket (Uninstall, etc.)"""
    await websocket.accept()
    
    if not settings.SONIC_ENABLED:
        await websocket.close(reason="Sonic disabled")
        return

    try:
        device = await sonic_service.get_device(udid)
        if not device:
            await websocket.close(reason="Device not found")
            return
            
        token = await sonic_service.get_token()
        token = await sonic_service.get_token()
        # Use Agent Key if available, otherwise fallback to Secret Key (but Agent likely needs its own key)
        key = settings.SONIC_AGENT_KEY or settings.SONIC_SECRET_KEY
        
        # Agent URL: /websockets/android/{key}/{udId}/{token}
        agent_url = f"ws://{device.agent_host}:{device.agent_port}/websockets/android/{key}/{udid}/{token}"
        
        await proxy_websocket(websocket, agent_url)
        
    except Exception as e:
        print(f"General Proxy Error: {e}")
        try:
            await websocket.close()
        except:
            pass



@router.get("/{udid}/screenshot")
async def screenshot(udid: str, platform: str = "android"):
    """截图（使用 ADB）"""
    if platform == "android":
        image_data = adb_screenshot(udid)
        if image_data:
            return Response(content=image_data, media_type="image/png")
    raise HTTPException(status_code=500, detail="截图失败")

@router.get("/{udid}/screenshot-base64")
async def screenshot_base64(udid: str, platform: str = "android"):
    """获取截图 Base64"""
    if platform == "android":
        image_data = adb_screenshot(udid)
        if image_data:
            b64 = base64.b64encode(image_data).decode()
            return {"image": f"data:image/png;base64,{b64}"}
    raise HTTPException(status_code=500, detail="截图失败")

@router.post("/{udid}/tap")
async def tap(udid: str, x: int, y: int, platform: str = "android"):
    """点击"""
    if platform == "android":
        if adb_tap(udid, x, y):
            return {"status": "success"}
    raise HTTPException(status_code=500, detail="点击失败")

@router.post("/{udid}/swipe")
async def swipe(
    udid: str, 
    start_x: int, 
    start_y: int, 
    end_x: int, 
    end_y: int, 
    duration: int = 300,
    platform: str = "android"
):
    """滑动"""
    if platform == "android":
        if adb_swipe(udid, start_x, start_y, end_x, end_y, duration):
            return {"status": "success"}
    raise HTTPException(status_code=500, detail="滑动失败")

@router.post("/{udid}/input")
async def input_text(udid: str, text: str, platform: str = "android"):
    """输入文本"""
    if platform == "android":
        if adb_input_text(udid, text):
            return {"status": "success"}
    raise HTTPException(status_code=500, detail="输入失败")

@router.post("/{udid}/back")
async def back(udid: str, platform: str = "android"):
    """返回键"""
    if platform == "android":
        if adb_keyevent(udid, 4):  # KEYCODE_BACK
            return {"status": "success"}
    raise HTTPException(status_code=500, detail="操作失败")

@router.post("/{udid}/home")
async def home(udid: str, platform: str = "android"):
    """Home 键"""
    if platform == "android":
        if adb_keyevent(udid, 3):  # KEYCODE_HOME
            return {"status": "success"}
    raise HTTPException(status_code=500, detail="操作失败")


# ===== WebSocket 投屏（使用 ADB 截图轮询）=====

@router.websocket("/{udid}/mirror")
async def mirror_websocket(
    websocket: WebSocket,
    udid: str,
    platform: str = Query("android"),
    fps: int = Query(10)
):
    """
    WebSocket 投屏 - 使用 ADB 截图轮询
    解决 Android 15 scrcpy 兼容性问题
    """
    await websocket.accept()
    
    interval = 1.0 / min(fps, 15)  # 最大 15 FPS
    
    try:
        while True:
            if platform == "android":
                image_data = adb_screenshot(udid)
                if image_data:
                    # 压缩并发送 JPEG
                    try:
                        from PIL import Image
                        import io
                        
                        img = Image.open(io.BytesIO(image_data))
                        # 缩放到合适大小
                        max_width = 540
                        if img.width > max_width:
                            ratio = max_width / img.width
                            new_size = (max_width, int(img.height * ratio))
                            img = img.resize(new_size, Image.LANCZOS)
                        
                        # 转换为 JPEG
                        buffer = io.BytesIO()
                        img.convert('RGB').save(buffer, format='JPEG', quality=70)
                        jpeg_data = buffer.getvalue()
                        
                        # 发送 base64 图像
                        b64 = base64.b64encode(jpeg_data).decode()
                        await websocket.send_json({
                            "type": "frame",
                            "data": f"data:image/jpeg;base64,{b64}"
                        })
                    except ImportError:
                        # 如果没有 Pillow，直接发送 PNG
                        b64 = base64.b64encode(image_data).decode()
                        await websocket.send_json({
                            "type": "frame",
                            "data": f"data:image/png;base64,{b64}"
                        })
            
            await asyncio.sleep(interval)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket 错误: {e}")


# ===== iOS 原生设备服务 API =====

# 延迟导入 iOS 服务
ios_device_service = None

def get_ios_service():
    """获取 iOS 设备服务实例"""
    global ios_device_service
    if ios_device_service is None:
        try:
            from apps.ui_automation.services.ios_device_service import ios_device_service as _ios_service
            ios_device_service = _ios_service
        except ImportError as e:
            print(f"iOS 服务导入失败: {e}")
    return ios_device_service


@router.get("/ios/native")
async def list_ios_native_devices():
    """获取原生 iOS 设备列表（本地 tidevice 检测）"""
    service = get_ios_service()
    if not service:
        raise HTTPException(status_code=500, detail="iOS 服务未初始化")
    
    devices = service.get_all_devices()
    return {
        "devices": [d.to_dict() for d in devices],
        "source": "tidevice"
    }


@router.post("/ios/native/{udid}/start-wda")
async def start_ios_wda(udid: str):
    """为 iOS 设备启动 WDA"""
    service = get_ios_service()
    if not service:
        raise HTTPException(status_code=500, detail="iOS 服务未初始化")
    
    device = service.get_device(udid)
    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")
    
    # WDA 启动在设备连接时会自动进行
    # 这里返回当前状态
    return {
        "udid": udid,
        "status": device.status.value,
        "wda_port": device.wda_port,
        "mjpeg_port": device.mjpeg_port
    }


@router.get("/ios/native/{udid}/mjpeg")
async def ios_mjpeg_proxy(udid: str):
    """代理 iOS MJPEG 流"""
    from fastapi.responses import StreamingResponse
    import httpx
    
    service = get_ios_service()
    if not service:
        raise HTTPException(status_code=500, detail="iOS 服务未初始化")
    
    device = service.get_device(udid)
    if not device or device.mjpeg_port == 0:
        raise HTTPException(status_code=404, detail="设备未就绪或 WDA 未启动")
    
    mjpeg_url = f"http://localhost:{device.mjpeg_port}"
    
    async def stream_mjpeg():
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", mjpeg_url, timeout=None) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
    
    return StreamingResponse(
        stream_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=--BoundaryString"
    )


@router.websocket("/ios/native/{udid}/mirror")
async def ios_native_mirror_ws(websocket: WebSocket, udid: str):
    """
    iOS 原生投屏 WebSocket
    从 MJPEG 流提取帧并通过 WebSocket 发送给前端
    """
    await websocket.accept()
    
    service = get_ios_service()
    if not service:
        await websocket.close(code=1011, reason="iOS 服务未初始化")
        return
    
    device = service.get_device(udid)
    if not device:
        await websocket.close(code=1008, reason="设备未找到")
        return
    
    # 确保 WDA 已启动
    if device.mjpeg_port == 0:
        mjpeg_url = await service.start_mirror(udid)
        if not mjpeg_url:
            await websocket.close(code=1011, reason="WDA 启动失败")
            return
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET", 
                f"http://localhost:{device.mjpeg_port}",
                timeout=None
            ) as response:
                
                # MJPEG 流是由多个 JPEG 帧组成，以 boundary 分隔
                buffer = b""
                
                async for chunk in response.aiter_bytes():
                    buffer += chunk
                    
                    # 查找 JPEG 帧的开始和结束
                    while True:
                        # JPEG 开始标记
                        start = buffer.find(b'\xff\xd8')
                        if start == -1:
                            break
                        
                        # JPEG 结束标记
                        end = buffer.find(b'\xff\xd9', start)
                        if end == -1:
                            break
                        
                        # 提取完整的 JPEG 帧
                        jpeg_data = buffer[start:end + 2]
                        buffer = buffer[end + 2:]
                        
                        # 发送给前端
                        b64 = base64.b64encode(jpeg_data).decode()
                        try:
                            await websocket.send_json({
                                "type": "frame",
                                "data": f"data:image/jpeg;base64,{b64}"
                            })
                        except Exception:
                            return
                        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"iOS 投屏 WebSocket 错误: {e}")
    finally:
        await service.stop_mirror(udid)


@router.post("/ios/native/{udid}/tap")
async def ios_native_tap(udid: str, x: int, y: int):
    """iOS 原生点击"""
    service = get_ios_service()
    if not service:
        raise HTTPException(status_code=500, detail="iOS 服务未初始化")
    
    success = await service.tap(udid, x, y)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="点击失败")


@router.post("/ios/native/{udid}/swipe")
async def ios_native_swipe(
    udid: str,
    from_x: int,
    from_y: int,
    to_x: int,
    to_y: int,
    duration: float = 0.3
):
    """iOS 原生滑动"""
    service = get_ios_service()
    if not service:
        raise HTTPException(status_code=500, detail="iOS 服务未初始化")
    
    success = await service.swipe(udid, from_x, from_y, to_x, to_y, duration)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="滑动失败")


@router.post("/ios/native/{udid}/home")
async def ios_native_home(udid: str):
    """iOS 原生 Home 键"""
    service = get_ios_service()
    if not service:
        raise HTTPException(status_code=500, detail="iOS 服务未初始化")
    
    success = await service.home(udid)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Home 失败")


@router.post("/ios/native/scheme-jump")
async def ios_scheme_jump(url: str, wda_url: str = "http://localhost:8100"):
    """
    iOS Scheme 跳转 (通过 WDA)
    :param url: 跳转链接 (如 myapp://page)
    :param wda_url: WDA 地址 (默认 http://localhost:8100)
    """
    try:
        from apps.ui_automation.services.ios_scheme_service import ios_scheme_service
        # 更新 WDA 地址 (如果需要)
        ios_scheme_service.base_url = wda_url.rstrip('/')
        
        success, msg = ios_scheme_service.jump(url)
        if success:
            return {"status": "success", "message": f"已跳转到 {url}"}
        else:
            raise HTTPException(status_code=500, detail=f"跳转失败: {msg}")
            
    except ImportError:
        raise HTTPException(status_code=500, detail="iOS Scheme 服务模块缺失")
    except Exception as e:
        print(f"Scheme 跳转异常: {e}")
        raise HTTPException(status_code=500, detail=f"跳转异常: {e}")



@router.websocket("/ws/ios-events")
async def ios_device_events_ws(websocket: WebSocket):
    """
    iOS 设备事件 WebSocket
    实时推送设备上下线事件给前端
    """
    await websocket.accept()
    
    service = get_ios_service()
    if not service:
        await websocket.close(code=1011, reason="iOS 服务未初始化")
        return
    
    # 事件队列
    event_queue = asyncio.Queue()
    
    def on_device_event(event: str, device):
        asyncio.create_task(event_queue.put({
            "type": event,
            "device": device.to_dict()
        }))
    
    # 注册回调
    service.add_callback(on_device_event)
    
    try:
        # 首先发送当前所有设备
        for device in service.get_all_devices():
            await websocket.send_json({
                "type": "device_list",
                "device": device.to_dict()
            })
        
        # 然后等待新事件
        while True:
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=30)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                # 发送心跳
                await websocket.send_json({"type": "ping"})
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"iOS 事件 WebSocket 错误: {e}")
    finally:
        service.remove_callback(on_device_event)

