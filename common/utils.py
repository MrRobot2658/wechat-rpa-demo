"""
通用工具函数
"""
import time
import random
import logging
import sys
from datetime import datetime


def human_delay(delay_range: list[float] | tuple[float, float]) -> None:
    """
    模拟人类操作的随机延迟，避免被风控检测为机器人。

    Args:
        delay_range: [最小延迟, 最大延迟]，单位秒
    """
    delay = random.uniform(delay_range[0], delay_range[1])
    time.sleep(delay)


def setup_logger(name: str, level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    配置日志记录器。

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-12s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def timestamp_str() -> str:
    """返回当前时间戳字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
