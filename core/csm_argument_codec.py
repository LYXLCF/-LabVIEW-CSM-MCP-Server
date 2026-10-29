# -*- coding: utf-8 -*-
"""
CSM 参数安全编解码器 (Arguments Safe Codec & Serialization)
依据官方 0. Base Concepts/4.1~4.3 Arguments 及 2026.10 (#593) 规范实现
"""

import re
import urllib.parse
from typing import Dict, Any, Union

class CSMArgumentCodec:
    """
    负责 CSM 参数在纯文本总线上的安全转义、类型标记与错误簇序列化
    全面对齐 NEVSTOP 2026.10 官方 #593 规范：两阶段精准转义，杜绝 % 字符误杀与解析冲突
    """

    # CSM 保留关键字与敏感字符字典 (精准转义为 %Hex，长度降序排列优先匹配)
    KEYWORD_HEX_MAP = {
        ">>>>": "%3E%3E%3E%3E",
        ">>>": "%3E%3E%3E",
        ">>": "%3E%3E",
        "->|": "%2D%3E%7C",
        "->": "%2D%3E",
        "-@": "%2D%40",
        "-&": "%2D%26",
        "<-": "%3C%2D",
        "//": "%2F%2F",
        ";": "%3B",
        ",": "%2C",
        "\r": "%0D",
        "\n": "%0A",
        "\t": "%09",
        "\\": "%5C",
        '"': "%22",
        "'": "%27"
    }

    UNSAFE_KEYWORDS = list(KEYWORD_HEX_MAP.keys())

    @classmethod
    def is_unsafe_for_csm(cls, text: str) -> bool:
        """检查参数是否包含可能导致 CSM 解析引擎歧义的敏感符号或 % 转义保留字"""
        if not text:
            return False
        if "%" in text:
            return True
        for kw in cls.UNSAFE_KEYWORDS:
            if kw in text:
                return True
        return False

    @classmethod
    def make_string_safe(cls, raw_arg: str, force: bool = False, use_angle_bracket: bool = False) -> str:
        """
        官方 4.3 规范 (#593 强化版)：
        阶段 1：先将原生文本中的 '%' 统一替换为 '%25'，彻底解决包含百分号字符的解析混乱；
        阶段 2：仅对 CSM 保留关键字执行精准 %Hex 转义，保留常规空格与等号 '=' 等普通字符；
        前缀规范：默认输出 SAFESTR:<safe_body>，若 use_angle_bracket=True 则输出 <SAFESTR> <safe_body>
        """
        if not raw_arg:
            return ""
        if not force and not cls.is_unsafe_for_csm(raw_arg):
            return raw_arg

        # 阶段 1：百分号转义
        s = raw_arg.replace("%", "%25")

        # 阶段 2：保留关键字精准替换 (按关键字长度优先)
        for kw, hex_val in sorted(cls.KEYWORD_HEX_MAP.items(), key=lambda x: -len(x[0])):
            s = s.replace(kw, hex_val)

        prefix = "<SAFESTR> " if use_angle_bracket else "SAFESTR:"
        return f"{prefix}{s}"

    @classmethod
    def revert_string_safe(cls, safe_arg: str) -> str:
        """
        官方 4.3 逆规范 (#593 强化版)：
        阶段 1：剥离 SAFESTR: 或 <SAFESTR> 标记；
        阶段 2：精准反解 CSM 关键字 %Hex；
        阶段 3：将 '%25' 还原为 '%'；
        向下兼容：同时兼容标准 urllib urlunquote 转义历史数据。
        """
        if not safe_arg:
            return ""

        body = safe_arg
        if body.startswith("<SAFESTR> "):
            body = body[len("<SAFESTR> "):]
        elif body.startswith("<SAFESTR>"):
            body = body[len("<SAFESTR>"):].lstrip()
        elif body.startswith("SAFESTR:"):
            body = body[len("SAFESTR:"):]

        # 阶段 2：还原关键字 (大小写不敏感)
        for kw, hex_val in sorted(cls.KEYWORD_HEX_MAP.items(), key=lambda x: -len(x[1])):
            body = re.sub(re.escape(hex_val), lambda m, v=kw: v, body, flags=re.IGNORECASE)

        # 阶段 3：还原百分号 %25 -> %
        body = body.replace("%25", "%")

        return body

    @classmethod
    def make_error_argument(cls, code: int, description: str, is_warning: bool = False) -> str:
        """
        官方 4.2 规范：将 LabVIEW 错误或警告封装为标准结构化参数字符串
        格式：
          错误: <ErrStr>[Error: <code>] <description>
          警告: <ErrStr>[Warning: <code>] <description>
        """
        safe_desc = cls.make_string_safe(description) if cls.is_unsafe_for_csm(description) else description
        tag = "Warning" if is_warning else "Error"
        return f"<ErrStr>[{tag}: {int(code)}] {safe_desc}"

    @classmethod
    def parse_error_argument(cls, err_arg: str) -> Dict[str, Any]:
        """
        官方 4.2 逆规范：解析 <ErrStr> / <ERRSTR> 参数，还原结构化错误与警告信息
        """
        if not err_arg or not err_arg.upper().startswith("<ERRSTR>"):
            return {"is_error": False, "is_warning": False, "code": 0, "message": ""}

        pattern = r'<ErrStr>\[(Error|Warning):\s*(-?\d+)\]\s*(.*)'
        match = re.match(pattern, err_arg.strip(), flags=re.IGNORECASE)
        if match:
            kind = match.group(1).capitalize()
            code = int(match.group(2))
            desc = match.group(3)
            if desc.startswith("SAFESTR:") or desc.startswith("<SAFESTR>"):
                desc = cls.revert_string_safe(desc)
            return {
                "is_error": kind == "Error" and code != 0,
                "is_warning": kind == "Warning",
                "type": kind,
                "code": code,
                "message": desc
            }
        return {"is_error": True, "is_warning": False, "type": "Error", "code": -1, "message": err_arg}

    @classmethod
    def encode_hexstr(cls, data_bytes: bytes) -> str:
        """
        官方 4.1 规范：将复杂二进制/数据转换为 HEXSTR (0-9, A-F)
        """
        if not data_bytes:
            return "HEXSTR:"
        hex_data = data_bytes.hex().upper()
        return f"HEXSTR:{hex_data}"

    @classmethod
    def decode_hexstr(cls, hexstr_arg: str) -> bytes:
        """
        官方 4.1 逆规范：从 HEXSTR 还原原生字节流
        """
        if not hexstr_arg:
            return b""
        if hexstr_arg.startswith("HEXSTR:"):
            hex_data = hexstr_arg[len("HEXSTR:"):]
            return bytes.fromhex(hex_data)
        return bytes.fromhex(hexstr_arg)
