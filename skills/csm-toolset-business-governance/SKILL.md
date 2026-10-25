---
name: csm-toolset-business-governance
description: 独属于第三步与演进升级【高阶 Tool 业务功能封装 (csm_mcp/tools/)】的高层调用与业务防线规范。严格约束 Tool 的入参强类型校验、命名合规守门 (基于官方 2. Module Naming Rules)、参数安全编解码 (基于 4.1~4.3 Arguments)、系统状态健康审计 (基于 1. JKISM vs CSM)、系统级模块保护 (基于 7. System-Level Module)，以及返回结构标准化 (JSON Schema)，防止 AI 工具滥用与状态污染。
---

# CSM 业务工具层封装与安全治理规范 (CSM Toolset Business Governance)

本规范是专门针对 `csm_mcp/tools/` 业务层（暴露给大模型与 MCP 客户端的高阶 Tool）的核心安全守则。
在封装、注册和调用任何业务工具时，**必须强制执行以下硬性约束，任何违规传参或越界行为均必须被前置拦截！**

---

## 零、 【P0 级最高红线：C盘原生库与官方 CSM 底座绝对只读继承】

> [!CAUTION] 【最高安全禁令：严禁修改/删除任何 C 盘底层库与安装文件】
> 1. **全业务工具严格继承底层安全拦截**：
>    * 所有涉及写操作的 Tool（如 `csm_create_module`、`csm_upsert_states`、`csm_set_state_script`），在接收外部入参路径（`vi_path` / `target_path`）后，**必须第一时间执行物理白名单检查**。
>    * 严禁目标路径指向 `C:\Program Files (x86)\National Instruments\`、`C:\Program Files\`、`C:\ProgramData\`、`C:\Windows\` 等系统盘目录！
> 2. **只允许操作工作区白名单**：
>    * 目标文件的读写操作仅限于用户指定的工程工作区（如 `c:\Users\ASUS\Desktop\CSM\`）及其子目录，越界直接抛出 `SecurityViolationError`。

---

## 一、 【模块命名守门规范 (Module Naming Gatekeeper)】
*(依据官方 `2. Module Naming Rules.vi` 建立强制检验)*

1. **非法字符严格禁止**：
   * 模块名称中严禁包含保留关键字：`~!@%^&*()[]{} +=| \ / ? ' " < > , \t \r \n`。
   * 一旦发现非法字符，Tool 层必须立即拦截并返回 `ModuleNamingError`，给出自愈提示。
2. **模式标识符规范识别**：
   * **`Worker` 模式**：以 `#` 结尾或包含 `#`（如 `Motor#1`），代表多实例并发工作者；
   * **`System-Level` 模式**：以 `.` 开头（如 `.TCP_Router`），代表系统级静默后台；
   * **`Submodule` 命名空间**：中间包含 `.`（如 `Chamber.Temp`）；
   * **`Chain` 模式**：包含 `$` 且紧跟数字（如 `Pipeline$1`），代表顺序接力管道。

---

## 二、 【参数安全编解码规范 (Safe Arguments & Serialization)】
*(依据官方 `4.1~4.3 Arguments` 建立参数防护)*

1. **`SAFESTR` 自动防呆**：
   * 参数若包含保留关键字（反斜杠 `\`、逗号 `,`、分号 `;`、冒号 `:`、换行符等，如 Windows 文件路径、网络 URL），严禁裸拼字符串！
   * 必须自动或通过工具转义为 `%Hex` 格式并加上 `SAFESTR` 前缀，防止 DSL 解析断裂。
2. **`ErrStr` 规范**：
   * 错误传递必须符合官方标准：`<ErrStr>[Error: <code>] <description>`。
3. **`HEXSTR` 复杂数据规范**：
   * 簇与复杂结构体通过十六进制安全字符串传输，确保纯文本总线无损流转。

---

## 三、 【模块健康度审计规范 (Health Audit)】
*(依据官方 `1. JKISM vs CSM.vi` 建立系统健康评估)*

在透视 VI (`csm_inspect_vi`) 时，除了返回状态列表外，必须输出 `health_audit`：
1. **基础宏完备性**：检查是否具备 `Macro: Initialize`、`Macro: Start`、`Macro: Exit`；
2. **错误接管完备性**：检查是否具备 `Critical Error` 与 `Error Handler`；
3. **系统响应支持**：标记是否支持 `Response` 与 `Async Response`。

---

## 四、 【核心 Tool 矩阵与权限分级】

| 工具名称 | 权限分级 | 核心业务职能 | 强类型入参约束 | 标准返回格式 (JSON) |
| :--- | :--- | :--- | :--- | :--- |
| **`csm_inspect_vi`** | **纯只读** | 透视全部状态、API、健康度审计与前台状态 | `vi_path`: 绝对文件路径 (.vi) | `{"success": true, "states": list, "health_audit": dict}` |
| **`csm_create_module`** | **受控写** | 基于官方母版克隆脚手架，含命名校验与模板选型 | `target_path`, `module_name`, `template_type` | `{"success": true, "module_category": str, "template_used": str}` |
| **`csm_upsert_states`** | **受控写** | 批量向 VI 注入状态分支（带命名守门与幂等去重） | `vi_path`, `states`: list[str] | `{"success": true, "added_states": list, "skipped_states": list}` |
| **`csm_verify_syntax`** | **纯只读** | 纯 Python 全局静态分析死锁、DSL 语法与系统级模块链路 | `project_dir`: 目标目录 | `{"deadlock_count": int, "system_modules": list, ...}` |
| **`csm_set_state_script`** | **受控写** | 注入状态流转脚本，带 DSL 语法审查与 SAFESTR 自动转义 | `vi_path`, `state_name`, `script_text` | `{"success": true, "escaped_safe_args": bool}` |
| **`csm_format_argument`** | **纯工具** | 将原始路径/错误/数据编码为合规的 SAFESTR/ErrStr/HEXSTR | `arg_type`, `raw_value` | `{"success": true, "formatted_argument": str}` |
| **`csm_add_to_project`** | **受控写** | 原生挂载 VI 到 .lvproj XML 虚拟文件夹 | `project_path`, `vi_path`, `target_folder` | `{"success": true, "virtual_folder": str}` |
