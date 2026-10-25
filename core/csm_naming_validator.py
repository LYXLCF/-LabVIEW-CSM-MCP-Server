# -*- coding: utf-8 -*-
"""
CSM 模块名称合规守门人 (Module Naming Validator)
依据官方 0. Base Concepts/2. Module Naming Rules.vi 规范实现
"""

import re

# 非法特殊字符集合 (官方保留字，严禁在常规模块名中出现)
# 允许特殊前缀/后缀模式中的有效符号:
# '.' (仅允许作为开头表示系统级，或内部作为子模块分隔符)
# '#' (允许表示 Worker 模式)
# '$' (仅允许后跟数字表示 Chain 模式)
ILLEGAL_CHARS_PATTERN = r'[~!@%^&*()\[\]{}+=|\\/?\'"<>, \t\r\n]'

class ModuleNamingResult:
    def __init__(self, is_valid: bool, module_name: str, category: str, error_msg: str = "", suggested_fix: str = ""):
        self.is_valid = is_valid
        self.module_name = module_name
        self.category = category  # "standard", "worker", "system_level", "submodule", "chain", "invalid"
        self.error_msg = error_msg
        self.suggested_fix = suggested_fix

    def to_dict(self):
        return {
            "is_valid": self.is_valid,
            "module_name": self.module_name,
            "category": self.category,
            "error_msg": self.error_msg,
            "suggested_fix": self.suggested_fix
        }

class CSMMonitorNamingValidator:
    """CSM 模块命名规范验证器"""

    @staticmethod
    def validate(name: str) -> ModuleNamingResult:
        if not name or not isinstance(name, str) or not name.strip():
            return ModuleNamingResult(
                is_valid=False,
                module_name=name,
                category="invalid",
                error_msg="模块名称不能为空字符串。",
                suggested_fix="请提供具有明确业务语义的模块名称，如 'Power_Supply' 或 'Motion_Controller'。"
            )

        name_clean = name.strip()

        # 检查是否以 '.' 开头 (系统级模块)
        if name_clean.startswith("."):
            body = name_clean[1:]
            if not body:
                return ModuleNamingResult(
                    is_valid=False,
                    module_name=name_clean,
                    category="invalid",
                    error_msg="系统级模块名称不能仅为一个点号 '.'。",
                    suggested_fix="请指定形如 '.TCP_Router' 或 '.Global_Logger' 的系统级模块名称。"
                )
            # 检查系统级模块内部非法字符
            invalid_chars = [c for c in body if c in "~!@%^&*()[]{}+=|\\/?'\"<>, \t\r\n"]
            if invalid_chars:
                return ModuleNamingResult(
                    is_valid=False,
                    module_name=name_clean,
                    category="invalid",
                    error_msg=f"系统级模块名称包含非法保留字符: {set(invalid_chars)}",
                    suggested_fix="请剔除特殊符号，建议仅使用英文、数字、下划线及减号。"
                )
            return ModuleNamingResult(
                is_valid=True,
                module_name=name_clean,
                category="system_level"
            )

        # 检查 Chain 模式 (包含 $ 且之后是数字)
        if "$" in name_clean:
            match = re.search(r'\$(\d+)$', name_clean)
            if match:
                prefix = name_clean[:name_clean.rfind("$")]
                invalid_chars = [c for c in prefix if c in "~!@%^&*()[]{}+=|\\/?'\"<>, \t\r\n"]
                if invalid_chars:
                    return ModuleNamingResult(
                        is_valid=False,
                        module_name=name_clean,
                        category="invalid",
                        error_msg=f"Chain 模块名称前缀包含非法字符: {set(invalid_chars)}",
                        suggested_fix="Chain 模式应形如 'Pipeline$1'、'Step$2'。"
                    )
                return ModuleNamingResult(
                    is_valid=True,
                    module_name=name_clean,
                    category="chain"
                )
            else:
                return ModuleNamingResult(
                    is_valid=False,
                    module_name=name_clean,
                    category="invalid",
                    error_msg="包含 '$' 的名称必须符合 Chain 模式，即 '$' 后必须紧跟数字编号（如 'Pipeline$1'）。",
                    suggested_fix="若要使用 Chain 模式，请在 '$' 后面加上序号；若非 Chain 模式，请剔除 '$' 符号。"
                )

        # 检查 Worker 模式 (包含 #)
        if "#" in name_clean:
            # 官方允许以 # 结尾或有明确序号，如 Motor# 或 Motor#1
            invalid_chars = [c for c in name_clean.replace("#", "") if c in "~!@%^&*()[]{}+=|\\/?'\"<>, \t\r\n"]
            if invalid_chars:
                return ModuleNamingResult(
                    is_valid=False,
                    module_name=name_clean,
                    category="invalid",
                    error_msg=f"Worker 模块名称包含非法字符: {set(invalid_chars)}",
                    suggested_fix="Worker 模式应形如 'Motor#' 或 'Sensor#1'。"
                )
            return ModuleNamingResult(
                is_valid=True,
                module_name=name_clean,
                category="worker"
            )

        # 检查子模块层级模式 (内部有点号分隔符，如 Chamber.Temp)
        if "." in name_clean:
            parts = name_clean.split(".")
            if any(not p.strip() for p in parts):
                return ModuleNamingResult(
                    is_valid=False,
                    module_name=name_clean,
                    category="invalid",
                    error_msg="点号分隔的子模块命名空间不能为空，如 'Chamber..Temp' 是非法的。",
                    suggested_fix="请确保层级点号两侧均有合法名称，如 'Chamber.Temp'。"
                )
            for p in parts:
                invalid_chars = [c for c in p if c in "~!@%^&*()[]{}+=|\\/?'\"<>, \t\r\n"]
                if invalid_chars:
                    return ModuleNamingResult(
                        is_valid=False,
                        module_name=name_clean,
                        category="invalid",
                        error_msg=f"子模块命名包含非法保留字符: {set(invalid_chars)}",
                        suggested_fix="请在各级子模块中使用合法字符，如 'Subsystem.Sensor_1'。"
                    )
            return ModuleNamingResult(
                is_valid=True,
                module_name=name_clean,
                category="submodule"
            )

        # 常规标准模块：允许字母、数字、中文、下划线、减号及常规空格
        # 非法字符检查
        invalid_chars = [c for c in name_clean if c in "~!@%^&*()[]{}+=|\\/?'\"<>, \t\r\n"]
        if invalid_chars:
            return ModuleNamingResult(
                is_valid=False,
                module_name=name_clean,
                category="invalid",
                error_msg=f"模块名称包含官方保留非法字符: {set(invalid_chars)}",
                suggested_fix="请移除特殊保留字符，推荐使用字母、数字、下划线组合，如 'Acquisition_Card'。"
            )

        return ModuleNamingResult(
            is_valid=True,
            module_name=name_clean,
            category="standard"
        )

    @staticmethod
    def suggest_template(module_name: str, intent_prompt: str = "") -> dict:
        """
        基于模块命名规范与自然语言业务意图，智能推断 8 大正统 CSM 出厂母版选型
        """
        combined = f"{module_name} {intent_prompt}".lower()
        
        # 1. 配置管理型母版推断 (+Configuration)
        if any(w in combined for w in ["配置", "ini", "参数存储", "掉电保存", "参数持久化", "config", "settings", "recipe"]):
            if any(w in combined for w in ["界面", "ui", "面板", "屏", "window", "view"]):
                return {
                    "template_type": "ui_config",
                    "reason": "检测到界面与参数持久化(INI/Config)语义，推荐选择带配置管理的界面主控母版"
                }
            return {
                "template_type": "worker_config",
                "reason": "检测到后台硬件/业务且需参数持久化(INI/Config)语义，推荐选择带配置管理的后台工作者母版"
            }
            
        # 2. 复用库型母版推断 (reuse)
        if any(w in combined for w in ["复用", "重用", "标准库", "分包", "通用库", "reuse"]):
            return {
                "template_type": "reuse",
                "reason": "检测到高内聚标准分包或独立可复用库语义，推荐选择官方 1. Create a reuse Module 标准母版"
            }

        # 3. 极简轻量型推断 (Tiny)
        if any(w in combined for w in ["微型", "轻量", "极简", "小", "弹窗", "提示", "tiny", "dialog", "popup"]):
            if any(w in combined for w in ["界面", "ui", "窗口", "弹窗"]):
                return {
                    "template_type": "ui_tiny",
                    "reason": "检测到轻量级/对话框弹窗界面语义，推荐选择极简 UI 模块母版"
                }
            return {
                "template_type": "worker_tiny",
                "reason": "检测到轻量计算/单一驱动后台语义，推荐选择极简 Worker 模块母版"
            }

        # 4. 高级分布式推断 (DQMH Style)
        if any(w in combined for w in ["dqmh", "广播", "多模块总控", "解耦", "分布式", "broadcast"]):
            return {
                "template_type": "dqmh",
                "reason": "检测到多模块强解耦或事件广播通信语义，推荐选择 DQMH 风格高抗阻塞双循环母版"
            }

        # 5. 标准主控界面推断 (UI)
        if any(w in combined for w in ["界面", "ui", "画面", "交互", "按键", "按钮", "面板", "front panel"]):
            return {
                "template_type": "ui",
                "reason": "检测到人机交互与事件结构(Event Loop)诉求，推荐选择标准 CSM User Interface 母版"
            }

        # 6. 默认回退：标准后台 Worker
        return {
            "template_type": "worker",
            "reason": "标准后台无 UI 业务逻辑，推荐选择正统经典 CSM Module Template 母版"
        }
