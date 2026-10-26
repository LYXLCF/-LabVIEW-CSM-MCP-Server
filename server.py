# -*- coding: utf-8 -*-
"""
基于官方 Model Context Protocol Python SDK (mcp 2.x - MCPServer) 彻底重构 server.py
1. 彻底淘汰手写的 JSON-RPC 字符串匹配循环与 tools/list, tools/call 手工解析
2. 完整原生支持官方 MCP 规范生命周期：
   - 协议初始化握手 (initialize / client capabilities 协商)
   - 握手完成通知 (notifications/initialized)
   - 探活心跳 (ping)
   - 工具列表与参数强类型 Schema 自动派发
3. 暴露 7 大核心业务原语 Tool
4. 原生兼容 Claude Desktop, Cursor, Goose, VS Code 等所有标准 MCP 客户端！
"""

import os
import sys
import json
from typing import List, Optional

# 引入官方 MCP 2.x 核心服务基类 (MCPServer)
from mcp.server.mcpserver import MCPServer

# 引入核心业务工具层与日志/自检组件
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "core")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "tools")))
from csm_logger import logger
from csm_doctor import CSMDoctor
from csm_tools import CSMTools

# 版本常量定义
__version__ = "1.1.0"

# 实例化官方 MCP 服务与业务工具中台
mcp = MCPServer("labview-csm-mcp")
tools_service = CSMTools()

# =========================================================================
# Tool 1: csm_inspect_vi (纯只读 - 状态流转透视与运行态闲置体检)
# =========================================================================
@mcp.tool(
    name="csm_inspect_vi",
    description="【纯只读】透视目标 CSM VI 的全部状态列表、暴露的 API 接口及前台/运行态 (ExecState) 闲置状态，进行系统健康度体检。"
)
def csm_inspect_vi(vi_path: str) -> str:
    """
    Args:
        vi_path: 目标 CSM .vi 文件的绝对路径 (如 C:\\Path\\To\\Module.vi)
    """
    res = tools_service.csm_inspect_vi(vi_path)
    return json.dumps(res, ensure_ascii=False, indent=2)

# =========================================================================
# Tool 2: csm_create_module (受控写 - 8大正统母版克隆 + Auto 智能自适应选型)
# =========================================================================
@mcp.tool(
    name="csm_create_module",
    description="【受控写】基于官方 8 大正统出厂母版一键克隆脚手架，具备 Auto 自适应选型，并自动将新 VI 挂载点亮至 .lvproj 工程树。"
)
def csm_create_module(
    target_path: str,
    module_name: str = "",
    template_type: str = "auto"
) -> str:
    """
    Args:
        target_path: 新建模块的目标绝对路径 (必须在工作区内，严禁写 C 盘系统目录)
        module_name: 模块规范名称 (支持 Worker#、系统级 .、Chain$ 等前缀模式)
        template_type: 母版选型: 'auto'(智能推断-默认), 'worker', 'ui', 'worker_tiny', 'ui_tiny', 'worker_config', 'ui_config', 'dqmh', 'reuse'
    """
    res = tools_service.csm_create_module(target_path, module_name, template_type)
    return json.dumps(res, ensure_ascii=False, indent=2)

# =========================================================================
# Tool 3: csm_upsert_states (受控写 - 双通道复合幂等守卫 + 自动穿线缝合)
# =========================================================================
@mcp.tool(
    name="csm_upsert_states",
    description="【受控写】安全切削条件分支。内嵌双通道复合幂等守卫 (防 Duplicate Tag)、影子快照、自动穿线与任务卡烧录，严格杜绝虚报成功。"
)
def csm_upsert_states(vi_path: str, states: List[str]) -> str:
    """
    Args:
        vi_path: 目标 CSM .vi 文件的绝对路径
        states: 需注入的标准状态名称数组 (如 ['API: Query IDN', 'API: Read Voltage'])
    """
    res = tools_service.csm_upsert_states(vi_path, states)
    return json.dumps(res, ensure_ascii=False, indent=2)

# =========================================================================
# Tool 4: csm_verify_syntax (纯只读 - 全工程静态死锁检测与纯 VI 兜底)
# =========================================================================
@mcp.tool(
    name="csm_verify_syntax",
    description="【纯只读】纯 Python 秒级扫描全工程跨模块路由跳转，支持无 .lvcsm 纯 VI 兜底嗅探，出具拓扑死锁图与孤立状态诊断报告。"
)
def csm_verify_syntax(project_dir: str) -> str:
    """
    Args:
        project_dir: 待体检的 LabVIEW 项目目录绝对路径
    """
    res = tools_service.csm_verify_syntax(project_dir)
    return json.dumps(res, ensure_ascii=False, indent=2)

# =========================================================================
# Tool 5: csm_format_argument (纯工具 - 官方 4.1~4.3 参数转义防呆)
# =========================================================================
@mcp.tool(
    name="csm_format_argument",
    description="【纯工具】依据官方 4.1~4.3 规范将敏感路径、复杂错误簇及十六进制数据自动编码为 SAFESTR/ErrStr/HEXSTR 防呆格式。"
)
def csm_format_argument(arg_type: str, raw_value: str, extra_info: str = "") -> str:
    """
    Args:
        arg_type: 参数类型: 'safe_string' (路径/特殊符号), 'error' (错误簇), 'hex' (十六进制数据)
        raw_value: 待转义编码的原始文本值
        extra_info: 附加辅助信息
    """
    res = tools_service.csm_format_argument(arg_type, raw_value, extra_info)
    return json.dumps(res, ensure_ascii=False, indent=2)

# =========================================================================
# Tool 6: csm_add_to_project (受控写 - .lvproj XML 树原子追加点亮)
# =========================================================================
@mcp.tool(
    name="csm_add_to_project",
    description="【受控写】通过标准 XML 树解析对 .lvproj 工程树执行原子节点追加，实现从磁盘文件到工程浏览器的无感点亮。"
)
def csm_add_to_project(project_path: str, vi_path: str, target_folder: str = "") -> str:
    """
    Args:
        project_path: 目标 .lvproj 文件的绝对路径
        vi_path: 待挂载的目标 .vi 文件绝对路径
        target_folder: 目标虚拟文件夹名称 (留空表示根目录)
    """
    res = tools_service.csm_add_to_project(project_path, vi_path, target_folder)
    return json.dumps(res, ensure_ascii=False, indent=2)

# =========================================================================
# Tool 7: csm_set_state_script (受控写 - 任务卡方案 A 执行脚本注入)
# =========================================================================
@mcp.tool(
    name="csm_set_state_script",
    description="【受控写】依据任务卡方案 A，向目标状态分支安全设置 CSM DSL 执行脚本链与开发者业务注释。"
)
def csm_set_state_script(vi_path: str, state_name: str, script_text: str) -> str:
    """
    Args:
        vi_path: 目标 CSM .vi 文件的绝对路径
        state_name: 目标状态分支名称 (如 'Macro: Initialize', 'API: Start')
        script_text: 多行 CSM 消息流脚本文本
    """
    res = tools_service.csm_set_state_script(vi_path, state_name, script_text)
    return json.dumps(res, ensure_ascii=False, indent=2)

# =========================================================================
# 服务主执行入口 (支持 --stdio, --doctor, --version, doctor 命令)
# =========================================================================
def main():
    args = sys.argv[1:]

    # 1. 版本查询
    if "--version" in args or "-v" in args:
        print(f"labview-csm-mcp v{__version__} (Official MCP SDK 2.x)")
        sys.exit(0)

    # 2. 环境健康全栈体检 (csm doctor 或 csm-mcp --doctor)
    if "--doctor" in args or "doctor" in args:
        doctor = CSMDoctor()
        doctor.print_report()
        sys.exit(0)

    # 3. 驱动官方标准的 stdio 事件流通信协议
    if "--stdio" in args:
        logger.info(f"启动 labview-csm-mcp v{__version__} Stdio MCP 传输通道...")
        try:
            mcp.run(transport="stdio")
        except Exception as e:
            logger.error(f"MCP Stdio 运行异常: {e}", exc_info=True)
            raise
    else:
        print(f"=== labview-csm-mcp v{__version__} (Official MCP SDK 2.x) 就绪 ===")
        print("支持的 7 大原生 MCP Tools:")
        print("  - csm_inspect_vi: 状态透视与运行态闲置体检")
        print("  - csm_create_module: 8大出厂母版克隆 + Auto 智能选型 + .lvproj 自动挂载点亮")
        print("  - csm_upsert_states: 双通道复合幂等守卫 + 自动穿线 + 真实切削检验")
        print("  - csm_verify_syntax: 纯 Python 静态死锁拓扑扫描 + 纯 VI 兜底嗅探")
        print("  - csm_format_argument: 官方 4.1~4.3 SAFESTR/ErrStr 参数转义防呆")
        print("  - csm_add_to_project: .lvproj XML 工程树原子挂载")
        print("  - csm_set_state_script: 方案 A 状态执行脚本链安全注入")
        print("\n常用命令指引:")
        print("  1. 环境自检排错:  csm-mcp --doctor  (或 csm-mcp doctor)")
        print("  2. 查看当前版本:  csm-mcp --version")
        print("  3. 挂载启动服务:  csm-mcp --stdio    (供 Claude Desktop / Cursor 挂载)")

if __name__ == "__main__":
    main()
