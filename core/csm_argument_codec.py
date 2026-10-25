# -*- coding: utf-8 -*-
"""
CSM 参数安全编解码器 (Arguments Safe Codec & Serialization)
依据官方 0. Base Concepts/4.1~4.3 Arguments 规范实现
"""

import re
import urllib.parse

class CSMArgumentCodec:
    """
    负责 CSM 参数在纯文本总线上的安全转义、类型标记与错误簇序列化
    """

    # CSM 保留关键字与敏感字符 (如果参数中出现这些字符，必须转义为 %Hex)
    UNSAFE_KEYWORDS = [
        "->|", "->", "-@", "-&", "<-", ">>", ">>>", ">>>>",
        "\r", "\n", "//", ";", ",", "\\", '"', "'", "\t"
    ]

    @classmethod
    def is_unsafe_for_csm(cls, text: str) -> bool:
        """检查参数是否包含可能导致 CSM 解析引擎歧义的敏感符号"""
        if not text:
            return False
        for kw in cls.UNSAFE_KEYWORDS:
            if kw in text:
                return True
        return False

    @classmethod
    def make_string_safe(cls, raw_arg: str, force: bool = False) -> str:
        """
        官方 4.3 规范：将敏感字符转换为 %Hex 格式，并赋予 SAFESTR 标记
        保留原始字符的大小写，仅将转义的 %xx 转换为大写 %XX
        示例：'C:\\Program Files\\data.csv' -> 'SAFESTR:C%3A%5CProgram%20Files%5Cdata.csv'
        """
        if not raw_arg:
            return ""
        if not force and not cls.is_unsafe_for_csm(raw_arg):
            return raw_arg

        quoted = urllib.parse.quote(raw_arg, safe="")
        # 仅将 %xx 转义部分变为大写
        safe_body = re.sub(r'%[0-9a-fA-F]{2}', lambda m: m.group(0).upper(), quoted)
        return f"SAFESTR:{safe_body}"

    @classmethod
    def revert_string_safe(cls, safe_arg: str) -> str:
        """
        官方 4.3 逆规范：将 SAFESTR:%Hex 解码还原为原生文本
        """
        if not safe_arg:
            return ""
        if safe_arg.startswith("SAFESTR:"):
            body = safe_arg[len("SAFESTR:"):]
            return urllib.parse.unquote(body)
        return safe_arg

    @classmethod
    def make_error_argument(cls, code: int, description: str) -> str:
        """
        官方 4.2 规范：将 LabVIEW 错误封装为标准错误参数字符串
        格式：<ErrStr>[Error: <code>] <description>
        """
        safe_desc = cls.make_string_safe(description) if cls.is_unsafe_for_csm(description) else description
        return f"<ErrStr>[Error: {int(code)}] {safe_desc}"

    @classmethod
    def parse_error_argument(cls, err_arg: str) -> dict:
        """
        官方 4.2 逆规范：解析 <ErrStr> 参数，还原结构化错误
        """
        if not err_arg or not err_arg.startswith("<ErrStr>"):
            return {"is_error": False, "code": 0, "message": ""}

        pattern = r'<ErrStr>\[Error:\s*(-?\d+)\]\s*(.*)'
        match = re.match(pattern, err_arg.strip())
        if match:
            code = int(match.group(1))
            desc = match.group(2)
            if desc.startswith("SAFESTR:"):
                desc = cls.revert_string_safe(desc)
            return {
                "is_error": code != 0,
                "code": code,
                "message": desc
            }
        return {"is_error": True, "code": -1, "message": err_arg}

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
