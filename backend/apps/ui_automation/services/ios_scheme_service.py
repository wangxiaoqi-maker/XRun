import requests
import json
from loguru import logger

class IOSSchemeService:
    """
    iOS Scheme 跳转服务
    基于 WDA
    """
    
    def __init__(self, wda_url: str = "http://localhost:8100"):
        self.base_url = wda_url.rstrip('/')

    def jump(self, jump_url: str) -> bool:
        """
        执行 Scheme 跳转
        :param jump_url: 跳转链接，如 myapp://page/detail
        :return: (is_success, message)
        """
        logger.info(f"[*] 正在尝试跳转: {jump_url}")
        
        # 0. 检查 URL
        if not self.base_url:
            return False, "WDA URL 未配置"

        # 1. 尝试创建一个新的 Session
        # WDA 需要先握手
        try:
            session_resp = requests.post(
                f"{self.base_url}/session",
                json={"capabilities": {}},
                timeout=10
            )
            
            if session_resp.status_code != 200:
                err_msg = f"创建 Session 失败: {session_resp.status_code} {session_resp.text}"
                logger.error(f"[!] {err_msg}")
                return False, err_msg
                
            session_data = session_resp.json()

            # 提取 sessionId
            session_id = session_data.get('sessionId') or session_data.get('value', {}).get('sessionId')

            if not session_id:
                err_msg = f"无法获取 Session ID: {session_resp.text}"
                logger.error(f"[!] {err_msg}")
                return False, err_msg

            logger.info(f"[+] 会话建立成功，Session ID: {session_id}")

        except Exception as e:
            err_msg = f"连接 WDA 失败 ({self.base_url}): {str(e)}"
            logger.error(f"[!] {err_msg}")
            return False, err_msg

        # 2. 使用拿到的 Session ID 发送跳转指令
        try:
            jump_payload = {"url": jump_url}
            jump_resp = requests.post(
                f"{self.base_url}/session/{session_id}/url",
                json=jump_payload,
                timeout=10
            )

            if jump_resp.status_code == 200:
                logger.info("[+] 跳转指令发送成功！")
                return True, "跳转成功"
            else:
                err_msg = f"跳转失败: {jump_resp.status_code} {jump_resp.text}"
                logger.error(f"[-] {err_msg}")
                return False, err_msg

        except Exception as e:
            err_msg = f"发送跳转请求出错: {str(e)}"
            logger.error(f"[-] {err_msg}")
            return False, err_msg

# 单例
ios_scheme_service = IOSSchemeService()
