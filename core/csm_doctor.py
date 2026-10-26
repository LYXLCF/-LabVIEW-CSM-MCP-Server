# -*- coding: utf-8 -*-
"""
CSM Doctor 全方位环境自检与诊断中台
涵盖 6 大核心自检维度：
1. Python 运行时与核心依赖 (mcp, pywin32, pydantic)
2. Windows COM 句柄与 LabVIEW.Application 连通性
3. 当前运行态 LabVIEW 主程序版本、位数与进程状态
4. NEVSTOP 官方 CSM 8 大母版与 API Helper 存在性
5. CSM 跳板 VI 与 Agent 中台资源健康度
6. 工作区与 .lvcsm 读写权限体检

执行方式：
- 命令行运行: csm-mcp --doctor 或 python server.py --doctor
- 代码中调用: CSMDoctor().run_diagnostics() -> dict
"""

import os
import sys
import platform
import json
from typing import Dict, Any, List

class CSMDoctor:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def _add_check(self, category: str, name: str, passed: bool, detail: str, suggestion: str = ""):
        self.results.append({
            "category": category,
            "name": name,
            "passed": passed,
            "detail": detail,
            "suggestion": suggestion
        })

    def run_diagnostics(self) -> Dict[str, Any]:
        """运行全部诊断项并返回结构化数据"""
        self.results = []

        # -----------------------------------------------------------------
        # 1. Python 环境与核心依赖检查
        # -----------------------------------------------------------------
        py_ver = sys.version.split()[0]
        py_arch = platform.architecture()[0]
        self._add_check(
            "Python 运行环境",
            "Python 版本与位数",
            sys.version_info >= (3, 10),
            f"Python {py_ver} ({py_arch})",
            "建议使用 Python 3.10 及以上 64 位环境" if sys.version_info < (3, 10) else ""
        )

        # 检查 pywin32
        try:
            import win32com.client
            self._add_check("Python 核心依赖", "pywin32 (COM 引擎)", True, "已正确安装并导入")
        except Exception as e:
            self._add_check("Python 核心依赖", "pywin32 (COM 引擎)", False, f"未安装或损坏: {e}", "执行: pip install pywin32")

        # 检查 mcp SDK
        try:
            import mcp
            from mcp.server.mcpserver import MCPServer
            import importlib.metadata
            mcp_ver = importlib.metadata.version("mcp")
            self._add_check("Python 核心依赖", "官方 MCP SDK (mcp 2.x)", True, f"版本: {mcp_ver}")
        except Exception as e:
            self._add_check("Python 核心依赖", "官方 MCP SDK (mcp 2.x)", False, f"未安装或损坏: {e}", "执行: pip install mcp>=2.3.0")

        # 检查 pydantic
        try:
            import pydantic
            self._add_check("Python 核心依赖", "pydantic (类型校验)", True, f"版本: {pydantic.__version__}")
        except Exception as e:
            self._add_check("Python 核心依赖", "pydantic (类型校验)", False, f"未安装: {e}", "执行: pip install pydantic")

        # -----------------------------------------------------------------
        # 2. LabVIEW COM 句柄与运行态嗅探
        # -----------------------------------------------------------------
        lv_app = None
        try:
            import win32com.client
            lv_app = win32com.client.Dispatch("Labview.Application")
            lv_ver = getattr(lv_app, "Version", "未知")
            app_name = getattr(lv_app, "AppName", "LabVIEW")
            self._add_check(
                "LabVIEW COM 连通性",
                "LabVIEW.Application 自动化句柄",
                True,
                f"已连接活动实例: {app_name} (版本号: {lv_ver})"
            )
        except Exception as e:
            self._add_check(
                "LabVIEW COM 连通性",
                "LabVIEW.Application 自动化句柄",
                False,
                f"COM 派发失败: {e}",
                "请先启动 LabVIEW，并进入「工具 -> 选项 -> VI 服务器」确认勾选了「ActiveX」且允许本地连接"
            )

        # -----------------------------------------------------------------
        # 3. 官方 CSM 8 大母版存在性扫描
        # -----------------------------------------------------------------
        from tools.csm_tools import OFFICIAL_CSM_TEMPLATES
        missing_templates = []
        found_templates = []
        for t_name, t_path in OFFICIAL_CSM_TEMPLATES.items():
            if os.path.exists(t_path):
                found_templates.append(t_name)
            else:
                missing_templates.append(f"{t_name} ({t_path})")

        if not missing_templates:
            self._add_check(
                "官方出厂母版资源",
                "CSM 8 大母版存在性",
                True,
                f"8/8 官方母版全部就绪 ({', '.join(found_templates)})"
            )
        else:
            self._add_check(
                "官方出厂母版资源",
                "CSM 8 大母版存在性",
                False,
                f"发现 {len(missing_templates)} 个母版缺失: {missing_templates[0]} 等",
                "请在 VIPM 中确认安装了最新版 Communicable State Machine(CSM) 工具包"
            )

        # -----------------------------------------------------------------
        # 4. 官方平坦化 Helper VI 检查
        # -----------------------------------------------------------------
        from core.csm_path_resolver import LabVIEWPathResolver
        helpers = LabVIEWPathResolver.get_helper_paths(lv_app)
        helper_v1 = helpers["read_states"]
        helper_v2 = helpers["read_api"]
        helpers_ok = os.path.exists(helper_v1) and os.path.exists(helper_v2)
        self._add_check(
            "官方 Helper API",
            "Read CSM States/API Helper VI",
            helpers_ok,
            "官方 API with lvcsm Support 完整就绪" if helpers_ok else "未找到官方 Helper VI 路径",
            "请确认已安装 NEVSTOP CSM Helper 支持包" if not helpers_ok else ""
        )

        # -----------------------------------------------------------------
        # 5. CSM Agent 跳板 VI 检查
        # -----------------------------------------------------------------
        agent_vi_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "agent_vi", "csm_agent_bridge_add_state.vi")
        )
        agent_vi_ok = os.path.exists(agent_vi_path)
        self._add_check(
            "Agent 核心跳板",
            "csm_agent_bridge_add_state.vi",
            agent_vi_ok,
            f"跳板 VI 就绪: {agent_vi_path}" if agent_vi_ok else f"跳板 VI 丢失: {agent_vi_path}",
            "请检查 csm_mcp/agent_vi 目录文件完整性" if not agent_vi_ok else ""
        )

        # -----------------------------------------------------------------
        # 6. 工作区与备份目录写权限体检
        # -----------------------------------------------------------------
        backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backups"))
        writable = False
        try:
            os.makedirs(backup_dir, exist_ok=True)
            test_file = os.path.join(backup_dir, ".doctor_write_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            writable = True
        except Exception:
            writable = False

        self._add_check(
            "文件系统权限",
            "备份与工作区安全写入",
            writable,
            f"本地安全写权限正常: {backup_dir}" if writable else f"备份目录无写权限: {backup_dir}",
            "请检查目录访问权限" if not writable else ""
        )

        # 汇总统计
        total = len(self.results)
        passed_count = sum(1 for r in self.results if r["passed"])
        failed_count = total - passed_count

        return {
            "total_checks": total,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "all_healthy": failed_count == 0,
            "checks": self.results
        }

    def print_report(self):
        """控制台高可读性格式化输出 (兼容各类终端编码)"""
        res = self.run_diagnostics()
        print("\n" + "=" * 65)
        print("          [CSM Doctor] LabVIEW-CSM-MCP 全栈环境自检报告")
        print("=" * 65)

        current_category = None
        for item in res["checks"]:
            if item["category"] != current_category:
                current_category = item["category"]
                print(f"\n>> [{current_category}]")

            mark = "[PASS]" if item["passed"] else "[FAIL]"
            print(f"  {mark} {item['name']}")
            print(f"         详情: {item['detail']}")
            if not item["passed"] and item["suggestion"]:
                print(f"         [建议]: {item['suggestion']}")

        print("\n" + "-" * 65)
        if res["all_healthy"]:
            print(f"[OK] 全部 {res['total_checks']} 项环境检测 100% 通过，系统处于最佳健康就绪状态！")
        else:
            print(f"[WARN] 共检测 {res['total_checks']} 项，其中 {res['failed_count']} 项未通过。请根据上方建议处理。")
        print("=" * 65 + "\n")
