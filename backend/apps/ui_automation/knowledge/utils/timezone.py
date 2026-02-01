"""
时区工具函数

提供北京时间（UTC+8）支持
"""
from datetime import datetime, timezone, timedelta

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def now_beijing() -> datetime:
    """
    获取当前北京时间
    
    Returns:
        带时区信息的北京时间 datetime
    """
    return datetime.now(BEIJING_TZ)


def utc_to_beijing(dt: datetime) -> datetime:
    """
    UTC 时间转北京时间
    
    Args:
        dt: UTC 时间（可带或不带时区信息）
        
    Returns:
        北京时间
    """
    if dt is None:
        return None
    
    # 如果没有时区信息，假设是 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(BEIJING_TZ)


def beijing_now_naive() -> datetime:
    """
    获取当前北京时间（无时区信息，用于数据库存储）
    
    Returns:
        无时区信息的北京时间 datetime
    """
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)
