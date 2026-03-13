"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用
    APP_NAME: str = "UI Automation Platform"
    DEBUG: bool = True
    SQL_ECHO: bool = False
    
    # 数据库（支持 MySQL: mysql+aiomysql://user:pass@host:3306/db）
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"  # 默认使用 SQLite
    
    # Sonic 配置
    SONIC_ENABLED: bool = True
    SONIC_SERVER_URL: str = "http://113.249.104.59:3000"  # 云端 Sonic Server
    SONIC_SECRET_KEY: str = "f63cbbfd-da49-4c86-8ae7-b5820382c768"  # 从 Sonic 后台获取
    SONIC_USERNAME: Optional[str] = None
    SONIC_PASSWORD: Optional[str] = None
    SONIC_AGENT_KEY: Optional[str] = None
    SONIC_AGENT_HOST: Optional[str] = "localhost"  # 本地 Agent Host（覆盖 Sonic Server 返回的地址）
    SONIC_AGENT_PORT: Optional[str] = "7777"
    SONIC_USE_LOCAL_AGENT: bool = True  # 是否使用本地 Agent（忽略 Sonic Server 返回的 IP）
    
    # AI 模型配置（可通过前端配置）
    AI_MODEL_BASE_URL: Optional[str] = None
    AI_MODEL_API_KEY: Optional[str] = None
    AI_MODEL_NAME: Optional[str] = None
    AI_MODEL_FAMILY: Optional[str] = None
    
    # OpenAI/Midscene 配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    MIDSCENE_MODEL_NAME: Optional[str] = None
    
    # Midscene 执行器路径
    EXECUTOR_PATH: str = "../executor"
    
    # 文件存储
    UPLOAD_DIR: str = "static/uploads"
    SCREENSHOT_DIR: str = "static/screenshots"
    REPORT_DIR: str = "static/reports"
    
    # Redis 配置（多进程数据共享）
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略 .env 中未定义的额外字段

settings = Settings()
