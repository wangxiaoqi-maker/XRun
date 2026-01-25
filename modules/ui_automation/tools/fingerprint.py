"""
浏览器指纹生成工具
每次生成唯一的浏览器指纹，用于反检测
"""
import random
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BrowserFingerprint:
    """浏览器指纹配置"""
    user_agent: str
    viewport_width: int
    viewport_height: int
    screen_width: int
    screen_height: int
    timezone: str
    language: str
    platform: str
    hardware_concurrency: int
    device_memory: int
    webgl_vendor: str
    webgl_renderer: str
    canvas_noise: float  # Canvas 指纹噪声


# 常见 User-Agent 池（Windows/Mac/Linux）
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# 常见时区
TIMEZONES = [
    "America/New_York",
    "America/Los_Angeles",
    "America/Chicago",
    "Europe/London",
    "Europe/Paris",
    "Asia/Shanghai",
    "Asia/Tokyo",
    "Australia/Sydney",
]

# 常见语言
LANGUAGES = [
    "en-US",
    "en-GB",
    "zh-CN",
    "zh-TW",
    "ja-JP",
    "ko-KR",
    "es-ES",
    "fr-FR",
    "de-DE",
]

# WebGL Vendor/Renderer 组合
WEBGL_VENDORS = [
    "Google Inc. (Intel)",
    "Google Inc. (NVIDIA)",
    "Google Inc. (AMD)",
    "Google Inc. (Apple)",
]

WEBGL_RENDERERS = [
    "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (Apple, Apple M1, OpenGL 4.1)",
]


def generate_fingerprint() -> BrowserFingerprint:
    """
    生成随机浏览器指纹
    
    Returns:
        BrowserFingerprint: 指纹配置对象
    """
    # 随机选择 User-Agent
    user_agent = random.choice(USER_AGENTS)
    
    # 根据 User-Agent 推断平台
    if "Windows" in user_agent:
        platform = "Win32"
        # Windows 常见分辨率
        viewports = [
            (1920, 1080),
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (1280, 720),
        ]
        screens = [
            (1920, 1080),
            (2560, 1440),
            (3840, 2160),
        ]
    elif "Mac" in user_agent:
        platform = "MacIntel"
        viewports = [
            (1440, 900),
            (1680, 1050),
            (1920, 1080),
            (2560, 1440),
        ]
        screens = [
            (2560, 1440),
            (2880, 1800),
            (3840, 2160),
        ]
    else:  # Linux
        platform = "Linux x86_64"
        viewports = [
            (1920, 1080),
            (1366, 768),
            (2560, 1440),
        ]
        screens = [
            (1920, 1080),
            (2560, 1440),
        ]
    
    viewport_w, viewport_h = random.choice(viewports)
    screen_w, screen_h = random.choice(screens)
    
    # 确保屏幕尺寸 >= 视口尺寸
    screen_w = max(screen_w, viewport_w)
    screen_h = max(screen_h, viewport_h)
    
    return BrowserFingerprint(
        user_agent=user_agent,
        viewport_width=viewport_w,
        viewport_height=viewport_h,
        screen_width=screen_w,
        screen_height=screen_h,
        timezone=random.choice(TIMEZONES),
        language=random.choice(LANGUAGES),
        platform=platform,
        hardware_concurrency=random.choice([4, 8, 12, 16]),
        device_memory=random.choice([4, 8, 16]),
        webgl_vendor=random.choice(WEBGL_VENDORS),
        webgl_renderer=random.choice(WEBGL_RENDERERS),
        canvas_noise=random.uniform(0.0001, 0.001),  # Canvas 指纹噪声
    )


def get_fingerprint_js(fingerprint: BrowserFingerprint) -> str:
    """
    生成注入指纹的 JavaScript 代码
    
    Args:
        fingerprint: 指纹配置
        
    Returns:
        str: JavaScript 代码
    """
    return f"""
    // 覆盖 navigator 属性
    Object.defineProperty(navigator, 'userAgent', {{
        get: () => '{fingerprint.user_agent}'
    }});
    
    Object.defineProperty(navigator, 'platform', {{
        get: () => '{fingerprint.platform}'
    }});
    
    Object.defineProperty(navigator, 'language', {{
        get: () => '{fingerprint.language}'
    }});
    
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {fingerprint.hardware_concurrency}
    }});
    
    Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => {fingerprint.device_memory}
    }});
    
    // 覆盖 screen 属性
    Object.defineProperty(screen, 'width', {{
        get: () => {fingerprint.screen_width}
    }});
    
    Object.defineProperty(screen, 'height', {{
        get: () => {fingerprint.screen_height}
    }});
    
    // 覆盖 WebGL
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) {{
            return '{fingerprint.webgl_vendor}';
        }}
        if (parameter === 37446) {{
            return '{fingerprint.webgl_renderer}';
        }}
        return getParameter.call(this, parameter);
    }};
    
    // Canvas 指纹噪声
    const toBlob = HTMLCanvasElement.prototype.toBlob;
    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
    const getImageData = CanvasRenderingContext2D.prototype.getImageData;
    
    HTMLCanvasElement.prototype.toBlob = function(...args) {{
        const ctx = this.getContext('2d');
        if (ctx) {{
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {{
                imageData.data[i] += Math.floor(Math.random() * {fingerprint.canvas_noise * 255});
            }}
            ctx.putImageData(imageData, 0, 0);
        }}
        return toBlob.apply(this, args);
    }};
    
    HTMLCanvasElement.prototype.toDataURL = function(...args) {{
        const ctx = this.getContext('2d');
        if (ctx) {{
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {{
                imageData.data[i] += Math.floor(Math.random() * {fingerprint.canvas_noise * 255});
            }}
            ctx.putImageData(imageData, 0, 0);
        }}
        return toDataURL.apply(this, args);
    }};
    
    // 时区
    Date.prototype.getTimezoneOffset = function() {{
        // 简化处理，实际应该根据 timezone 计算
        return -480; // UTC+8
    }};
    """

