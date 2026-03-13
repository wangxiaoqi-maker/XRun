"""TCG 模块统一日志 — 基于 loguru"""
import sys
from loguru import logger as _root_logger

_root_logger.remove()

_root_logger.add(
    sys.stderr,
    format=(
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level:<7}</level> | "
        "<cyan>{extra[module]:<20}</cyan> | "
        "{message}"
    ),
    level="INFO",
    filter=lambda record: "module" in record["extra"],
)

_root_logger.add(
    "data/logs/tcg_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level:<7} | "
        "{extra[module]:<20} | "
        "{message}"
    ),
    filter=lambda record: "module" in record["extra"],
)


def get_logger(module: str):
    """获取带模块上下文的 logger"""
    return _root_logger.bind(module=module)
