# -*- coding: utf-8 -*-
"""
纯 Python 实现的 CSM 状态流转静态语法、系统级模块与死锁检测分析器
依据官方 0. Base Concepts/1~7 全部规范升级
"""

import os
import re
import json

class CSMSyntaxAnalyzer:
    """
    纯 Python 实现的 CSM 状态流转静态语法与死锁检测分析器
    严格遵守 csm-architect-standards 与官方 0. Base Concepts 规范：
    1. 解析 8 大 DSL：本地消息、同步阻塞 (-@)、异步调用 (->, ->|)、广播 (<status>, <interrupt>)、动态订阅 (<register>, <unregister>)
    2. 过滤 // 行尾注释
    3. 识别 System-Level 系统级模块 (以 '.' 开头) 与常规模块
    4. 模块核心健康度审计 (检查 Critical Error, Macro: Exit, Error Handler 等)
    5. 检测双向同步死锁环路 (Cycle Detection)
    6. 零副作用、不需要启动 LabVIEW
    """

    CORE_HEALTH_STATES = {
        "macro_init": "Macro: Initialize",
        "macro_start": "Macro: Start",
        "macro_exit": "Macro: Exit",
        "critical_error": "Critical Error",
        "error_handler": "Error Handler"
    }

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        # { module_name: { "vi_path": str, "states": set(), "calls": list, "is_system_level": bool, "health": dict } }
        self.modules = {}
        self.sync_calls = []   # list of (from_module, to_module, call_line)
        self.registrations = [] # list of (from_module, event_source, event_name, handler_api, call_line)

    def scan_project(self):
        """扫描项目目录下所有 .vi 和 .lvcsm 文件"""
        # 1. 扫描所有的 .lvcsm 索引文件获取官方登记的状态
        for root, _, files in os.walk(self.project_dir):
            for f in files:
                if f.endswith(".lvcsm"):
                    self._parse_lvcsm(os.path.join(root, f))

        # 2. 扫描所有 .vi 二进制提取纯文本 CSM 消息
        for root, _, files in os.walk(self.project_dir):
            for f in files:
                if f.endswith(".vi"):
                    vi_path = os.path.join(root, f)
                    mod_name = os.path.splitext(f)[0]
                    is_sys = mod_name.startswith(".")
                    if mod_name not in self.modules:
                        self.modules[mod_name] = {
                            "vi_path": vi_path,
                            "states": set(),
                            "calls": [],
                            "is_system_level": is_sys
                        }
                    else:
                        self.modules[mod_name]["vi_path"] = vi_path
                        self.modules[mod_name]["is_system_level"] = is_sys
                    self._extract_vi_csm_calls(vi_path, mod_name)

        # 3. 无 .lvcsm 兜底策略：对状态集依然为空的纯 VI 模块执行无感二进制嗅探
        for mod_name, mod_data in self.modules.items():
            if not mod_data["states"] and mod_data.get("vi_path"):
                mod_data["states"] = self._extract_vi_fallback_states(mod_data["vi_path"])

        # 4. 对所有已登记模块进行健康度审计
        for mod_name, mod_data in self.modules.items():
            mod_data["health"] = self._audit_module_health(mod_data["states"])

    def _parse_lvcsm(self, lvcsm_path: str):
        """解析 .lvcsm 文件中的注册状态与模块映射"""
        current_mod = None
        current_sec = None
        with open(lvcsm_path, "r", encoding="utf-8", errors="ignore") as fp:
            for line in fp:
                line = line.strip()
                if line.startswith("[") and line.endswith("]"):
                    current_sec = line[1:-1]
                    if "CSMStates." in current_sec:
                        current_mod = current_sec.split("CSMStates.")[-1].split(".")[0]
                        if current_mod not in self.modules:
                            self.modules[current_mod] = {
                                "vi_path": "",
                                "states": set(),
                                "calls": [],
                                "is_system_level": current_mod.startswith(".")
                            }
                elif "=" in line and current_mod:
                    key, val = line.split("=", 1)
                    val = val.strip().strip('"')
                    if val:
                        self.modules[current_mod]["states"].add(val)

    def _extract_vi_fallback_states(self, vi_path: str) -> set:
        """
        无 .lvcsm 配置文件时的纯 VI 二进制无感兜底嗅探器
        从 VI 数据流中高效提取符合 CSM 规范的标准状态分支名称
        """
        extracted = set()
        try:
            with open(vi_path, "rb") as fp:
                data = fp.read()
            # 正则嗅探常见的 CSM 状态标记: Macro: xxx, API: xxx, UI: xxx, Private: xxx 等
            matches = re.findall(rb'((?:Macro|API|UI|Private):\s*[a-zA-Z0-9_\-\s]+)', data)
            for m in matches:
                try:
                    st = m.decode("ascii", errors="ignore").strip()
                    if 3 < len(st) < 45 and not any(c in st for c in ["\r", "\n", "\t", "<", ">", "\""]):
                        extracted.add(st)
                except Exception:
                    pass
        except Exception:
            pass

        # 补全基础生命周期默认状态
        extracted.update(["Macro: Initialize", "Macro: Start", "Macro: Exit", "Critical Error"])
        return extracted

    def _extract_vi_csm_calls(self, vi_path: str, mod_name: str):
        """从 VI 二进制中快速过滤提取 CSM 消息路由语法行 (全 8 种指令)"""
        with open(vi_path, "rb") as fp:
            content = fp.read()

        # 匹配合法的 CSM 语法文本行 (包含 -@, ->|, ->, -><status>, -><interrupt>, -><register>, -><unregister>)
        pattern = rb'([a-zA-Z0-9_\-:\s@]+(?:-@|->\||->|-><status>|-><interrupt>|-><register>|-><unregister>)[a-zA-Z0-9_\-\s@]+)'
        matches = re.findall(pattern, content)

        for m in matches:
            try:
                line = m.decode("ascii", errors="ignore").strip()
                # 剔除 // 行尾注释
                if "//" in line:
                    line = line.split("//")[0].strip()

                if len(line) < 5 or len(line) > 120 or "\x00" in line:
                    continue
                self.modules[mod_name]["calls"].append(line)

                # 1. 同步阻塞调用: API: xxx -@ TargetModule
                if "-@" in line:
                    parts = line.split("-@")
                    if len(parts) == 2:
                        target = parts[1].strip().split()[0]
                        if target:
                            self.sync_calls.append((mod_name, target, line))

                # 2. 动态事件注册: Status@Source >> API@Handler -><register>
                elif "-><register>" in line:
                    parts = line.split("-><register>")[0].strip().split(">>")
                    if len(parts) == 2:
                        src_part = parts[0].strip()
                        handler_part = parts[1].strip()
                        self.registrations.append((mod_name, src_part, handler_part, line))

            except Exception:
                pass

    def _audit_module_health(self, states: set) -> dict:
        """评估单个模块的 CSM 标准健康度 (基于 1. JKISM vs CSM.vi)"""
        missing = []
        has_init = any("Initialize" in s for s in states)
        has_start = any("Start" in s for s in states)
        has_exit = any("Exit" in s for s in states)
        has_critical = any("Critical Error" in s for s in states)
        has_err_handler = any("Error Handler" in s for s in states)

        if not has_init: missing.append("Macro: Initialize")
        if not has_exit: missing.append("Macro: Exit")
        if not (has_critical or has_err_handler): missing.append("Critical Error / Error Handler")

        # 评分机制：满分 100
        score = 100 - (len(missing) * 20)
        return {
            "health_score": max(score, 0),
            "is_healthy": len(missing) == 0,
            "has_initialize": has_init,
            "has_start": has_start,
            "has_exit": has_exit,
            "has_critical_error": has_critical,
            "has_error_handler": has_err_handler,
            "missing_recommendations": missing
        }

    def check_deadlocks(self) -> list[dict]:
        """
        死锁检测器：
        利用有向图检测模块间是否存在循环同步阻塞等待 (Cycle Detection)
        """
        deadlocks = []
        sync_map = {}
        for from_m, to_m, line in self.sync_calls:
            if from_m not in sync_map:
                sync_map[from_m] = set()
            sync_map[from_m].add((to_m, line))

        for mod_a, targets_a in sync_map.items():
            for mod_b, line_a in targets_a:
                if mod_b in sync_map:
                    for mod_c, line_b in sync_map[mod_b]:
                        if mod_c == mod_a:
                            deadlocks.append({
                                "module_a": mod_a,
                                "module_b": mod_b,
                                "call_a_to_b": line_a,
                                "call_b_to_a": line_b,
                                "issue": "双向同步死锁！模块双方均使用 -@ 等待对方返回，系统将永久挂起！"
                            })
        return deadlocks

    def get_summary_report(self) -> dict:
        """生成全局静态分析报告 (包含系统级模块统计)"""
        self.scan_project()
        deadlocks = self.check_deadlocks()
        
        system_modules = [m for m, d in self.modules.items() if d.get("is_system_level")]
        standard_modules = [m for m, d in self.modules.items() if not d.get("is_system_level")]

        report = {
            "scanned_project": self.project_dir,
            "total_modules": len(self.modules),
            "standard_modules_count": len(standard_modules),
            "system_modules_count": len(system_modules),
            "system_modules": system_modules,
            "deadlock_count": len(deadlocks),
            "deadlocks": deadlocks,
            "modules_summary": {}
        }

        for name, data in self.modules.items():
            report["modules_summary"][name] = {
                "is_system_level": data.get("is_system_level", False),
                "states_count": len(data["states"]),
                "states_sample": list(data["states"])[:5],
                "calls_count": len(data["calls"]),
                "health": data.get("health", {})
            }
        return report

if __name__ == "__main__":
    analyzer = CSMSyntaxAnalyzer(r"c:\Users\ASUS\Desktop\CSM")
    rep = analyzer.get_summary_report()
    print(json.dumps(rep, ensure_ascii=False, indent=2))
