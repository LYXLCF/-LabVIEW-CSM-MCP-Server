# -*- coding: utf-8 -*-
import os
import sys
import json
import asyncio
from typing import List, Optional

# 引入核心业务工具
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "tools")))
from csm_tools import CSMTools

class FastCSMMCPServer:
    """
    符合标准 MCP (Model Context Protocol) 规范的 CSM 专用服务器
    对外暴露 7 大核心 CSM 业务原语 Tool 与内置 Skill 架构规范
    深度对齐官方 0. Base Concepts/1~7 全部规范 (v1.1.0)
    """

    def __init__(self):
        self.tools = CSMTools()
        self.server_name = "labview-csm-mcp"
        self.version = "1.1.0"

    def get_tool_definitions(self):
        """暴露给 MCP 客户端的高阶工具元数据定义"""
        return [
            {
                "name": "csm_inspect_vi",
                "description": "【纯只读】透视目标 CSM VI 的状态流转结构、暴露的 API 接口、前台打开状态，以及模块系统健康度审计 (依据 1. JKISM vs CSM.vi)。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vi_path": {
                            "type": "string",
                            "description": "目标 CSM .vi 文件的绝对路径"
                        }
                    },
                    "required": ["vi_path"]
                }
            },
            {
                "name": "csm_create_module",
                "description": "【受控写】基于 NEVSTOP 官方出厂母版一键生成全新模块脚手架。内置 2. Module Naming Rules 命名守门人 (支持标准/Worker#/系统级./Chain$) 与 8 大母版类型选型。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target_path": {
                            "type": "string",
                            "description": "新建模块的目标绝对路径 (必须在工作区内，严禁写 C 盘)"
                        },
                        "module_name": {
                            "type": "string",
                            "description": "模块规范名称 (支持 Worker 模式如 'Motor#1', 系统级如 '.TCP_Router', Chain 如 'Pipeline$1')"
                        },
                        "template_type": {
                            "type": "string",
                            "enum": ["auto", "worker", "ui", "worker_tiny", "ui_tiny", "worker_config", "ui_config", "dqmh", "reuse"],
                            "default": "auto",
                            "description": "母版类型: 'auto'(智能自适应选型-默认), 'worker'(标准后台无UI), 'ui'(标准前台界面), 'worker_tiny'(紧凑后台), 'ui_tiny'(紧凑界面), 'dqmh'(高抗阻塞双循环)"
                        }
                    },
                    "required": ["target_path"]
                }
            },
            {
                "name": "csm_upsert_states",
                "description": "【受控写】安全向已有 CSM VI 注入新状态分支。内嵌语义守门人、前台互斥检查、影子临时备份与原子回滚机制。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vi_path": {
                            "type": "string",
                            "description": "目标 CSM .vi 文件的绝对路径"
                        },
                        "states": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "需新增的状态名称数组 (必须带 Macro:/API:/UI: 规范前缀，如 ['API: Query IDN'])"
                        }
                    },
                    "required": ["vi_path", "states"]
                }
            },
            {
                "name": "csm_verify_syntax",
                "description": "【纯只读】纯 Python 秒级扫描全项目所有 CSM 模块的 8 大路由跳转、检测双向同步死锁、系统级模块统计与语法健康度。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_dir": {
                            "type": "string",
                            "description": "待体检的 LabVIEW 项目目录绝对路径"
                        }
                    },
                    "required": ["project_dir"]
                }
            },
            {
                "name": "csm_format_argument",
                "description": "【纯工具】依据官方 4.1~4.3 规范将敏感路径/复杂错误/二进制数据编码为 SAFESTR、ErrStr 或 HEXSTR 格式，防止 DSL 断裂。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "arg_type": {
                            "type": "string",
                            "enum": ["safe_string", "revert_safe", "error", "parse_error", "hex"],
                            "description": "编码类型: 'safe_string'(转SAFESTR:%Hex), 'revert_safe'(还原), 'error'(转<ErrStr>), 'parse_error'(解析<ErrStr>), 'hex'(转HEXSTR)"
                        },
                        "raw_value": {
                            "type": "string",
                            "description": "待编码的原始字符串、路径或错误描述"
                        },
                        "extra_info": {
                            "type": "string",
                            "description": "额外参数 (如错误码数字，默认为 5000)"
                        }
                    },
                    "required": ["arg_type", "raw_value"]
                }
            },
            {
                "name": "csm_add_to_project",
                "description": "【受控写】将新建或现存的 CSM 模块安全挂载到 .lvproj 工程树指定虚拟文件夹下。动刀前自动创建工程 .bak 备份。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "目标 LabVIEW 工程文件 (.lvproj) 的绝对路径"
                        },
                        "vi_path": {
                            "type": "string",
                            "description": "待挂载的 CSM .vi 文件绝对路径"
                        },
                        "target_folder": {
                            "type": "string",
                            "description": "目标虚拟文件夹名称 (如 'CAN', 'VISA', 'Drivers'，若留空则挂载在根目录)"
                        }
                    },
                    "required": ["project_path", "vi_path"]
                }
            },
            {
                "name": "csm_set_state_script",
                "description": "【受控写】为指定 CSM VI 的特定状态分支注入/改写右侧 CSM 消息流脚本文本。前置执行官方语法白名单校验与路径安全防呆。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vi_path": {
                            "type": "string",
                            "description": "目标 CSM .vi 文件的绝对路径"
                        },
                        "state_name": {
                            "type": "string",
                            "description": "目标状态分支名称 (如 'Macro: Initialize', 'API: Start')"
                        },
                        "script_text": {
                            "type": "string",
                            "description": "多行 CSM 消息流脚本文本 (如 'API: Start -> CAN\\n<Ready> -> <status>')"
                        }
                    },
                    "required": ["vi_path", "state_name", "script_text"]
                }
            }
        ]

    def handle_call_tool(self, name: str, arguments: dict) -> dict:
        """分发并调度业务 Tool"""
        if name == "csm_inspect_vi":
            return self.tools.csm_inspect_vi(arguments.get("vi_path", ""))
        elif name == "csm_create_module":
            return self.tools.csm_create_module(
                arguments.get("target_path", ""),
                arguments.get("module_name", ""),
                arguments.get("template_type", "auto")
            )
        elif name == "csm_upsert_states":
            return self.tools.csm_upsert_states(arguments.get("vi_path", ""), arguments.get("states", []))
        elif name == "csm_verify_syntax":
            return self.tools.csm_verify_syntax(arguments.get("project_dir", ""))
        elif name == "csm_format_argument":
            return self.tools.csm_format_argument(
                arguments.get("arg_type", ""),
                arguments.get("raw_value", ""),
                arguments.get("extra_info", "")
            )
        elif name == "csm_add_to_project":
            return self.tools.csm_add_to_project(
                arguments.get("project_path", ""),
                arguments.get("vi_path", ""),
                arguments.get("target_folder", "")
            )
        elif name == "csm_set_state_script":
            return self.tools.csm_set_state_script(
                arguments.get("vi_path", ""),
                arguments.get("state_name", ""),
                arguments.get("script_text", "")
            )
        else:
            return {
                "success": False,
                "error_type": "UnknownToolError",
                "error_message": f"未知的 CSM MCP 工具: {name}"
            }

    def run_stdio(self):
        """标准 JSON-RPC stdio 通信入口 (对齐 MCP 标准规范)"""
        import sys
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                req_id = request.get("id")
                method = request.get("method")
                params = request.get("params", {})

                if method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"tools": self.get_tool_definitions()}
                    }
                elif method == "tools/call":
                    tool_name = params.get("name")
                    tool_args = params.get("arguments", {})
                    call_result = self.handle_call_tool(tool_name, tool_args)
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(call_result, ensure_ascii=False, indent=2)
                                }
                            ]
                        }
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method {method} not found"}
                    }

                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()

            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"Parse error: {e}"}
                }
                sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()

if __name__ == "__main__":
    server = FastCSMMCPServer()
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        server.run_stdio()
    else:
        print(f"=== {server.server_name} v{server.version} 就绪 ===")
        print("支持的 MCP Tools:")
        for t in server.get_tool_definitions():
            print(f"  - {t['name']}: {t['description']}")
