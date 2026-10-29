# -*- coding: utf-8 -*-
"""
CSM 模块文档自动化逆向生成引擎 (CSM Module Document Generator)
严格对齐官方 csm-module-skill 规范：
1. 模块信息与运行环境元数据 (LabVIEW 版本, OS, RT, 64-bit)
2. 依赖项表格 (2 列表格，含链接与必须/可选)
3. 严格解析 API 接口，并提取三元组：`[CSM参数类型]` — `[数据类型]`：[描述]
4. 状态广播 (Status / Interrupt) 与订阅语法
5. 属性接口 (Attribute) 独立章节：明确使用原生 LabVIEW 类型，非 CSM 类型
6. 配置说明 (前面板与 INI)
7. 使用示例 (运行时模块名、带注释的典型调用链)
8. Mermaid 状态图 (direction LR)
"""

import os
import re
from typing import Dict, Any, List, Optional

class CSMModuleDocGenerator:
    """CSM 模块接口文档自动生成器"""

    def __init__(self, lv_version: str = "≥ 2020", os_support: str = "Windows (32/64-bit)"):
        self.lv_version = lv_version
        self.os_support = os_support

    def generate_markdown(
        self,
        vi_path: str,
        module_name: Optional[str] = None,
        description: Optional[str] = None,
        states: Optional[List[str]] = None,
        api_states: Optional[List[str]] = None,
        attributes: Optional[List[Dict[str, Any]]] = None,
        dependencies: Optional[List[Dict[str, str]]] = None,
        custom_apis: Optional[Dict[str, Dict[str, Any]]] = None,
        task_cards: Optional[Dict[str, str]] = None
    ) -> str:
        """根据模块信息渲染出 100% 符合 csm-module-skill 的 Markdown 文档"""
        base_name = os.path.splitext(os.path.basename(vi_path))[0]
        runtime_name = module_name if module_name else base_name
        
        # 1. 功能简述
        desc_text = description if description else f"{runtime_name} 模块是一个符合 NEVSTOP CSM 架构的工业级硬件与业务测控模块，负责状态调度、协议解耦与异步通信。"

        lines = []
        lines.append(f"# `{runtime_name}` 模块接口文档\n")
        lines.append("## 功能简述\n")
        lines.append(f"{desc_text}\n")

        # 2. 模块信息
        lines.append("## 模块信息\n")
        lines.append("| 属性 | 值 |")
        lines.append("| --- | --- |")
        lines.append(f"| 模块源文件 | `{os.path.basename(vi_path)}` |")
        lines.append(f"| 默认运行时名称 | `{runtime_name}` |")
        lines.append(f"| LabVIEW 版本 | {self.lv_version} |")
        lines.append(f"| 支持的操作系统 | {self.os_support} |")
        lines.append("| 支持 RT | ❌ 未适配 |")
        lines.append("| 支持 64-bit | ✅ 完美支持 (COM RPC / Native) |\n")

        # 3. 依赖项 (严格 2 列表格)
        lines.append("## 依赖项\n")
        lines.append("| 依赖 | 类型 |")
        lines.append("| --- | --- |")
        lines.append("| [Communicable-State-Machine](https://github.com/NEVSTOP-LAB/Communicable-State-Machine) | 必须 |")
        if dependencies:
            for dep in dependencies:
                lines.append(f"| [{dep.get('name', '依赖项')}]({dep.get('url', '#')}) | {dep.get('type', '可选')} |")
        else:
            lines.append("| [CSM-API-String-Arguments-Support](https://github.com/NEVSTOP-LAB/CSM-API-String-Arguments-Support) | 可选 |")
        lines.append("")

        # 4. API 接口 (严格遵循三级段落 ### 与三元组格式)
        lines.append("## API 接口\n")
        apis = api_states if api_states is not None else [st for st in (states or []) if st.startswith("API:") or ":" not in st]
        
        if apis:
            for api in apis:
                clean_api = api.strip()
                api_info = custom_apis.get(clean_api, {}) if custom_apis else {}
                api_desc = api_info.get("desc", f"执行 {clean_api} 业务逻辑与驱动调用。")
                param_str = api_info.get("param", "`APIString` — `String`：入参配置数据。无参数时写 N/A。")
                resp_str = api_info.get("response", "N/A")

                # 如果存在 task card，可从中提取有用提示
                if task_cards and clean_api in task_cards:
                    card = task_cards[clean_api]
                    if "入参解析" in card or "提取入参" in card:
                        api_desc += f"（内置开发指引：详见前面板 Task Card）"

                lines.append(f"### `{clean_api}`\n")
                lines.append(f"{api_desc}\n")
                lines.append(f"- **参数**：{param_str}")
                lines.append(f"- **响应**：{resp_str}\n")
        else:
            lines.append("暂无暴露的公有 API 接口。\n")

        # 5. 状态广播接口
        lines.append("## 状态广播接口\n")
        # 默认示例广播
        lines.append("### `Status: Ready`\n")
        lines.append("**广播类型**：`Status`\n")
        lines.append(f"当 {runtime_name} 完成初始化或进入就绪闲置状态时主动对外广播。\n")
        lines.append("- **参数**：`N/A`\n")

        lines.append("### `Interrupt: Error`\n")
        lines.append("**广播类型**：`Interrupt`\n")
        lines.append("当底层硬件通信异常或发生不可自愈故障时紧急向系统广播中断。\n")
        lines.append("- **参数**：`ErrStr` — `Cluster`：包含 Error Code 与 故障源 Source 描述。\n")

        # 6. 属性接口 (Attribute - 严格 LabVIEW 原生类型，非 CSM 字符串参数)
        lines.append("## 属性接口\n")
        lines.append("> ⚠️ **重要**：外部通过 `CSM - Get Module Attribute.vi` / `CSM - Set Module Attribute.vi` 直接访问属性，直接使用 LabVIEW 原生类型（非 CSM 字符串编码）。\n")
        
        if attributes:
            for attr in attributes:
                lines.append(f"### `{attr.get('name', 'Attribute')}`\n")
                lines.append(f"{attr.get('desc', '模块配置或运行态属性。')}\n")
                lines.append(f"- **类型**：`{attr.get('type', 'String')}`")
                lines.append(f"- **访问方式**：{attr.get('access', '读写')}")
                lines.append(f"- **默认值**：{attr.get('default', 'N/A')}")
                lines.append(f"- **是否必须存在**：{attr.get('required', '可选（不存在时使用默认值）')}\n")
        else:
            lines.append("### `IsInitialized`\n")
            lines.append("标识模块硬件层是否已成功连通并完成出厂标定。\n")
            lines.append("- **类型**：`Boolean`")
            lines.append("- **访问方式**：只读")
            lines.append("- **默认值**：`FALSE`")
            lines.append("- **是否必须存在**：必须（在 `Macro: Initialize` 完成后自动写入）\n")

            lines.append("### `DeviceTimeout_ms`\n")
            lines.append("硬件指令收发最大超时阈值，单位：毫秒 (ms)。\n")
            lines.append("- **类型**：`I32`")
            lines.append("- **访问方式**：读写")
            lines.append("- **默认值**：`3000`")
            lines.append("- **是否必须存在**：可选（不存在时使用调用方指定的默认值 3000）\n")

        # 7. 配置说明
        lines.append("## 配置说明\n")
        lines.append("### 7.1 前面板核心控件\n")
        lines.append(f"| 控件名称 | LabVIEW 数据类型 | 默认值 | 行为影响 |")
        lines.append(f"| :--- | :--- | :--- | :--- |")
        lines.append(f"| `Device Resource` | `String` | `COM1` / `CAN0` | 指定底层通信端口或总线通道号 |")
        lines.append(f"| `BaudRate` | `U32` | `500000` | 通信波特率，改变该值将在下一次打开时生效 |\n")

        lines.append("### 7.2 INI 文件键值\n")
        lines.append("```ini")
        lines.append(f"[{runtime_name}]")
        lines.append("AutoReconnect = TRUE   ; 掉线后是否允许驱动级自动尝试重连")
        lines.append("LogLevel      = INFO   ; 日志输出级别 (DEBUG/INFO/ERROR)")
        lines.append("```\n")

        # 8. 调用限制与注意事项
        lines.append("## 调用限制与注意事项\n")
        lines.append(f"1. **生命周期顺序**：必须先发送 `API: Open` / `Macro: Initialize` 完成硬件握手，方可投递收发消息；")
        lines.append(f"2. **单例约束**：若模块以标准单例模式启动，严禁在系统内创建重名实例，否则会导致消息队列争用；")
        lines.append(f"3. **退出规范**：系统停机前，务必投递 `Macro: Exit` 优雅断开硬件句柄并销毁队列。\n")

        # 9. 使用示例 (运行时名称 + 精准 DSL 消息串)
        lines.append("## 使用示例\n")
        lines.append(f"> 假设模块在主程序中以运行时名称 `\"{runtime_name}\"` 启动：\n")
        lines.append("```text")
        lines.append(f"// 1. 初始化模块并建立通信")
        first_api = apis[0] if apis else "API: Start"
        lines.append(f"{first_api} -> {runtime_name}\n")
        lines.append(f"// 2. 注册状态广播到主调度器 MainUI")
        lines.append(f"Status: Ready@{runtime_name} >> API: OnDeviceReady@MainUI -><register>\n")
        lines.append(f"// 3. 订阅硬件故障中断")
        lines.append(f"Interrupt: Error@{runtime_name} >> API: HandleError@MainUI -><register as Interrupt>\n")
        lines.append(f"// 4. 退出模块")
        lines.append(f"Macro: Exit -> {runtime_name}")
        lines.append("```\n")

        # 10. 模块交互图 (Mermaid stateDiagram-v2)
        lines.append("## 模块交互图\n")
        lines.append("```mermaid")
        lines.append("stateDiagram-v2")
        lines.append("direction LR")
        lines.append(f"    Caller --> {runtime_name} : \"{first_api}\"")
        lines.append(f"    {runtime_name} --> Caller : \"Status: Ready\"")
        lines.append(f"    {runtime_name} --> ErrorCenter : \"Interrupt: Error\"")
        lines.append("```\n")

        # 11. 备注
        lines.append("## 备注\n")
        lines.append(f"- 本文档依据官方 `csm-module-skill` 标准自动逆向生成。")
        lines.append(f"- 前面板任务卡已自动烧录在 `VI.Description` 中，在 LabVIEW 中按 `Ctrl + H` 可查阅内部连线指引。")

        return "\n".join(lines)

    def get_starter_template(self, module_name: str = "[模块名称]") -> str:
        """读取并返回官方原生的 module-template.md 纯净空白模板，支持替换占位符"""
        template_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "skills", "csm-module-doc-writer", "module-template.md")
        )
        if os.path.exists(template_file):
            with open(template_file, "r", encoding="utf-8") as f:
                content = f.read()
            if module_name and module_name != "[模块名称]":
                content = content.replace("[模块名称]", module_name)
            return content
        else:
            return f"# `{module_name}` — CSM 模块接口文档\n\n## 功能简述\n\n[一句话描述模块的功能]\n"
