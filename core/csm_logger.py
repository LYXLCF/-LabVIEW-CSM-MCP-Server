# -*- coding: utf-8 -*-
"""
CSM MCP 运行时轻量安全日志模块 (Logger)
特点：
1. 不向 stdout/stderr 输出任何杂质，绝对不污染 MCP stdio 的 JSON-RPC 通信流；
2. 写入独立的滚动日志文件 (例如 logs/csm_mcp.log)；
3. 支持 DEBUG, INFO, WARNING, ERROR 等级记录，带高精度时间戳；
4. 发生异常时静默失败，绝不中断主业务逻辑。
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

def get_csm_logger(name: str = "csm_mcp") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # 杜绝向 root logger 传播导致打印到控制台 stdout

    try:
        # 日志目录定位在 csm_mcp/logs 目录下
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "csm_mcp.log")

        # 限制 5MB，保留 3 个滚动备份
        handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except Exception:
        # 如果由于权限无法创建日志文件，使用 NullHandler 兜底
        logger.addHandler(logging.NullHandler())

    return logger

# 全局默认单例
logger = get_csm_logger()
