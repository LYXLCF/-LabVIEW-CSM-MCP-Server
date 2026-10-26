# ⚡ LabVIEW CSM MCP Server (工业级可通信状态机专有智能中台)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LabVIEW](https://img.shields.io/badge/LabVIEW-2020%2B%20(32%2F64bit)-orange.svg)](https://www.ni.com/labview/)
[![Protocol](https://img.shields.io/badge/Protocol-Model%20Context%20Protocol-green.svg)](https://modelcontextprotocol.io/)
[![Architecture](https://img.shields.io/badge/Architecture-Dual--Layer%20Bridge-purple.svg)]()
[![License](https://img.shields.io/badge/license-MulanPSL--2.0-blue.svg)](LICENSE)

> **让通用大模型（Claude / Cursor / Antigravity）直接读懂、编写与治理 LabVIEW 工业级状态机！**  
> 本项目是深度解构并数字化对齐 **NEVSTOP CSM-Wiki 正统哲学** 的工业级专有 Model Context Protocol (MCP) 服务端。专为工业自动化产线、机电设备驱动与分布式测控台架打造，彻底终结了传统 AI 面对 LabVIEW 图形化连线（G 语言）时的“致盲”与“连线破坏”难题。

---

## 📖 目录
- [💡 为什么需要本专有 MCP？](#-为什么需要本专有-mcp)
- [🛠️ 7 大核心业务功能详解 (功能有啥？)](#️-7-大核心业务功能详解-功能有啥)
- [📑 强势亮点：前面板 VI 说明与 API 步骤自动烧录 (自文档化)](#-强势亮点前面板-vi-说明与-api-步骤自动烧录-自文档化)
- [🚀 保姆级安装与使用指南 (怎么使用？)](#-保姆级安装与使用指南-怎么使用)
- [🎬 真实工业实战全流程演练](#-真实工业实战全流程演练)
- [📦 官方 8 大出厂母版全矩阵](#-官方-8-大出厂母版全矩阵)
- [📐 架构设计与底层突破](#-架构设计与底层突破)
- [❓ 常见问题排错 (FAQ)](#-常见问题排错-faq)

---

## 💡 为什么需要本专有 MCP？

| 对比维度 | 传统通用 AI 辅助 LabVIEW | 接入本 CSM 专有 MCP 之后 |
| :--- | :--- | :--- |
| **视觉与感知** | ❌ **严重致盲**：`.vi` 是二进制格式，AI 无法读取框图连线，只能瞎猜。 | ✅ **结构透视**：秒级解析 VI 内部全部状态分支、暴露的 API 及运行态。 |
| **代码生成方式** | ❌ **破坏性连线**：强行用 VI Scripting 盲画连线，节点重叠、移位寄存器断线（Broken VI）。 | ✅ **零断线切削**：内嵌隧道自动穿线补丁（`Connect Paired Tunnels`），自动缝合移位寄存器与错误线。 |
| **框架规范约束** | ❌ **胡乱发明语法**：捏造不存在的符号，破坏工业状态机调度拓扑。 | ✅ **正统规范强控**：严格内嵌 6 大治理 Skill，严格对齐官方 Base Concepts 1~7 规范。 |
| **工程协同能力** | ❌ **孤立生成文件**：生成 `.vi` 丢在磁盘上，工程师需要手动拖入项目。 | ✅ **工程树无感点亮**：自动解析并追加 `.lvproj` XML 树节点，打开 LabVIEW 项目直接就绪。 |
| **文档与维护性** | ❌ **无文档零注释**：按 `Ctrl+H` 即时帮助空空如也，外部调用与参数格式全靠猜。 | ✅ **原生烧录自文档化**：自动将 API 步骤与五步任务卡烧录至 `VI Description`，**按 `Ctrl+H` 前面板即显完整指引**！ |

---

## 📑 强势亮点：前面板 VI 说明与 API 步骤自动烧录 (自文档化)

在工业测控现场，最让团队头疼的往往不是写代码，而是**“别人写的 VI 没有任何文档，按 `Ctrl+H` 一片空白，外部调用不知道传什么参数，维护全靠猜”**。

本专有 MCP 打造了一套极具工业人文关怀的 **原生 VI 自文档化 (Auto-Documentation) 引擎**：
1. **自动烧录 `VI Description` (VI 说明)**：
   每次调用 `csm_upsert_states` 新增状态时，底层引擎不仅在框图内切削分支，同时自动提取该 API 的名称、入参规范与业务注释，格式化后写入 LabVIEW 原生的 `VI.Description` 属性并持久化保存。
2. **前面板 `Ctrl + H` 即时帮助零延迟唤出**：
   工程师无需切换回 Cursor 或打开网页查文档，在 LabVIEW 前面板按下 **`Ctrl + H`**（即时帮助窗口），或者右键图标查看 **VI 属性 ➔ 说明信息**，即可直接阅读该模块全部 API 的调用规范与 **五步连线开发任务卡**：
   - **Step 1: 解包驱动句柄** (Unbundle Driver Handle)
   - **Step 2: 提取状态入参** (Extract Arguments `>>`)
   - **Step 3: 调用核心硬件子 VI** (Call Hardware Core SubVI)
   - **Step 4: 缝合黄色错误簇链** (Wire Error Cluster Pipeline)
   - **Step 5: 寄存器数据回存** (Bundle Back to Shift Register)
3. **团队资产终身受惠**：
   代码交付给测试工程师、产线调试人员或外协单位时，VI 自带说明书，彻底消除了团队沟通鸿沟与“文档债务”！

---

## 🛠️ 7 大核心业务功能详解 (功能有啥？)

接入本服务后，AI 助手将自动获得以下 **7 大原子级工业调度原语**。在日常工作中，您**无需手动编写任何 Python 脚本**，只需在 AI 聊天框中用自然语言对 AI 提要求，AI 会自动组合调用底层工具：

---

### 1. `csm_inspect_vi` —— 模块状态机结构深度透视 (只读)
* **解决什么痛点**：接手别人写的老旧 CSM 模块，不知道里面有哪些状态、提供了哪些外部 API 接口。
* **自然语言 Prompt 示例**：
  > “帮我分析一下 `CAN_Controller.vi`，看看它目前实现了哪些状态分支，暴露了哪些外部可调用的 API？”
* **底层能力**：
  - 自动通过本地 COM 平坦化跳板提取目标 VI 的全部 Case 分支；
  - 智能分类标注 `API:`（公有接口）、`Macro:`（复合宏状态）与 `Private`（内部私有状态）；
  - **前台与运行态体检**：自动检测 `FPWinOpen`（是否在前台被打开）与 `ExecState`（是否正在运行中），杜绝动态冲突。

---

### 2. `csm_create_module` —— 8 大官方母版智能脚手架生成 (受控写)
* **解决什么痛点**：每次新建 CSM 模块都要去安装目录下找模板、重命名、修改连线板，繁琐且容易改坏母版。
* **自然语言 Prompt 示例**：
  > “请在 `Modules/Motor/` 目录下帮我新建一个名为 `Motor#1` 的电机驱动模块。”
* **底层能力**：
  - **物理级只读沙箱**：严格锁定 `C:\Program Files` 官方母版目录，仅在指定工作区无损克隆全新 VI；
  - **智能自适应选型 (Auto)**：根据模块命名语义自动识别（如输入 `Motor#1` 自动推荐并发 Worker 驱动模板，输入 `*UI*` 自动推荐双循环交互界面模板）；
  - **命名合规守门人**：自动校验是否符合官方规范（`#` 实例重入、`.` 系统级单例、`$` 链式管道）。

---

### 3. `csm_upsert_states` —— 零断线安全注入状态分支与任务卡烧录 (核心受控写)
* **解决什么痛点**：在已有 VI 中添加业务状态时，手动添加极费时间，而传统自动化工具新增分支会导致**移位寄存器（Shift Register）与错误连线断裂（Broken VI）**，且缺少调用指引。
* **自然语言 Prompt 示例**：
  > “请给 `CAN_Controller.vi` 增加两个新状态：`API: Query Status` 和 `API: Reset Device`，确保连线完整，并在前面板生成说明文档。”
* **底层能力**：
  - **双通道复合幂等拦截**：注入前比对已存在的 Case 标签，重复状态直接拦截，彻底杜绝 LabVIEW 抛出重名编译死锁；
  - **移位寄存器自动穿线补丁**：内置 `Connect Paired Tunnels.vi`，新增 Case 帧后毫秒级自动穿透并缝合移位寄存器隧道与错误线，**保证生成的代码 100% 原生可执行，绝不断线！**
  - **前面板 VI 说明自动烧录**：同步更新 `VI.Description`，按 `Ctrl+H` 前面板即显完整参数与步骤；
  - **自动影子备份**：动刀前毫秒级在 `backups/` 目录创建带时间戳的 `.bak` 快照，遇到异常原子回滚。

---

### 4. `csm_verify_syntax` —— 全项目静态拓扑扫描与双向死锁检测 (只读)
* **解决什么痛点**：CSM 多模块之间通过消息队列高频互发，一旦出现 `A 模块等待 B 模块` 且 `B 模块等待 A 模块` 的同步阻塞，系统现场瞬间卡死。
* **自然语言 Prompt 示例**：
  > “请全面扫描我的 `Test Control` 项目，检查所有 CSM 模块之间有没有双向同步死锁，或者未实现的状态调用。”
* **底层能力**：
  - 纯 Python 秒级解构全工程模块间的 8 类 DSL 消息跳转（`-@` 同步等待、`->|` 异步解耦、`<broadcast>` 广播等）；
  - 构建有向邻接表 `AdjacencyList`，毫秒级定位环路依赖死锁；
  - **孤立状态审计 (Orphan State)**：精准排查调用了某个状态但在目标 VI 中根本未实现分支的代码隐患；
  - **无 .lvcsm 兜底嗅探**：通吃无配置文件的历史外协老工程。

---

### 5. `csm_format_argument` —— 复杂参数安全编解码与防呆 (纯工具)
* **解决什么痛点**：CSM 消息参数串采用 `>>` 分隔，如果参数内容本身包含特殊符号（如 Windows 路径反斜杠 `\`、双引号、逗号、分号或换行符），会导致消息队列解析错位崩溃。
* **自然语言 Prompt 示例**：
  > “我需要把路径 `C:\Program Files\Config.ini` 和一个错误簇作为参数传给状态机，请帮我转成 CSM 安全参数。”
* **底层能力**：
  - 严格对齐官方 Base Concepts 4.1~4.3 规范；
  - 将敏感路径编码为 `SAFESTR(...)`，复杂错误簇编码为 `ErrStr(...)`，十六进制二进制数据编码为 `HEXSTR(...)`，保障通信无损。

---

### 6. `csm_add_to_project` —— LabVIEW 工程树原子级无感挂载 (受控写)
* **解决什么痛点**：通过脚本在磁盘生成了 VI，但是打开 LabVIEW 项目浏览器（`.lvproj`）却看不到，必须人工手动“右键 -> 添加文件”。
* **自然语言 Prompt 示例**：
  > “将刚才新建的 `Motor#1.vi` 自动添加到 `Test Control.lvproj` 工程的 `Drivers` 虚拟文件夹下。”
* **底层能力**：
  - 原生解析 `.lvproj` 的 XML 拓扑结构，自动定位目标 `<Folder>` 节点并追加 `<Item Type="VI">`；
  - 同步更新 `.lvcsm` 依赖映射，实现打开 LabVIEW 工程浏览器**直接点亮**。

---

### 7. `csm_set_state_script` —— 状态机 DSL 执行逻辑自动烧录 (受控写)
* **解决什么痛点**：分支建好了，但里面需要写标准的消息流转注释或执行序列（如初学者开发任务卡，提醒工程师下一步连线）。
* **自然语言 Prompt 示例**：
  > “在新建的 `API: Initialize` 状态分支里，烧录标准的消息流转逻辑和业务引导注释。”
* **底层能力**：
  - 将 CSM DSL 语法（如 `API: Start -> CAN\n<Ready> -> <status>`）直接烧录注入到目标 Case 分支内，提供初学者任务卡引导。

---

## 🚀 保姆级安装与使用指南 (怎么使用？)

只需简单四步，即可在 5 分钟内将 AI 助手武装为 LabVIEW 专家：

### 第一步：基础运行环境准备
* 操作系统：Windows 10 / 11
* LabVIEW：2020 及以上版本（支持 32 位或 64 位，实测 LabVIEW 2025 完美支持）
* Python：3.10 及以上（**推荐 64 位 Python 3.12**，得益于 Windows COM RPC，可无缝调度 32 位 LabVIEW）
* 安装 Python 核心依赖：
  ```bash
  pip install pywin32 mcp
  ```

### 第二步：配置 LabVIEW VI 服务器权限 (仅需配置一次)
为允许外部安全调度 LabVIEW 本地 COM 引擎，请确保 VI Server 处于开启状态：
1. 打开 LabVIEW，在顶部菜单栏依次点击：**工具 (Tools) ➔ 选项 (Options)**；
2. 在左侧分类中选择 **VI 服务器 (VI Server)**；
3. 在右侧勾选 **ActiveX** 访问复选框；
4. 在“机器访问列表 (Machine Access)”中添加本机权限（添加 `*` 允许本机访问）；
5. 点击“确定”保存设置。

---

### 第三步：在主流 AI 客户端中配置挂载

#### 方案 A：在 Cursor 中配置 (推荐)
1. 打开 Cursor，点击右上角齿轮 **Settings ➔ Features ➔ MCP Servers**；
2. 点击 **+ Add New MCP Server**，填写：
   - **Name**: `labview-csm-mcp`
   - **Type**: `command`
   - **Command**: `python C:\path\to\csm_mcp\server.py --stdio`
3. 或者直接在项目根目录创建 `.cursor/mcp.json`：
   ```json
   {
     "mcpServers": {
       "labview-csm-mcp": {
         "command": "python",
         "args": [
           "C:\Users\ASUS\Desktop\CSM\csm_mcp\server.py",
           "--stdio"
         ]
       }
     }
   }
   ```
4. 保存后，MCP 状态灯显示为绿色即代表挂载成功！

#### 方案 B：在 Claude Desktop 中配置
1. 打开配置文件 `%APPDATA%\Claude\claude_desktop_config.json`；
2. 加入以下内容：
   ```json
   {
     "mcpServers": {
       "labview-csm-mcp": {
         "command": "python",
         "args": [
           "C:\Users\ASUS\Desktop\CSM\csm_mcp\server.py",
           "--stdio"
         ]
       }
     }
   }
   ```
3. 重启 Claude Desktop 即可在对话工具栏中看到 7 大 CSM 专属工具。

---

### 第四步：终端独立自检（无需打开客户端即可测试）
在终端中执行以下命令，测试各组件通信是否正常：
```bash
cd csm_mcp

# 1. 运行服务自检
python server.py

# 2. 运行自动化测试套件
python tests/test_tools_layer.py
```
若控制台输出 `7 大核心 Tools 就绪` 且断言全部通过，即代表所有底层环境无懈可击！

---

## 🎬 真实工业实战全流程演练

安装配置完成后，在 Cursor / Claude 的对话界面中，您可以直接像与一位 LabVIEW 资深工程师搭档一样进行对话。以下是典型会话流程：

```text
🧑‍💻 工程师：
“我们现在要给新能源产线增加一个高压绝缘耐压测试仪模块。
请帮我在 Modules/ 下新建一个绝缘仪驱动模块，命名为 'Insulation#1'。
然后帮我添加三个基础业务状态：
1. 'API: Self Test' (仪器开机自检)
2. 'API: Start Test' (触发耐压输出)
3. 'API: Read Voltage' (读取当前回采高压)
最后把这个模块自动添加到项目工程树的 'Drivers' 文件夹下，并帮我生成前面板说明文档。”

🤖 AI 助手 (自动分发调度)：
思考：正在执行工业级 CSM 模块创建、状态切削与自文档化工作流...
1. [调用 csm_create_module]
   ➔ 智能自适应识别到 '#' 命名，匹配出厂标准 Worker 驱动母版；
   ➔ 安全克隆生成 Modules/Insulation#1.vi。
2. [调用 csm_upsert_states]
   ➔ 执行双重安全检查：前台无冲突、运行态处于 Idle；
   ➔ 自动创建时间戳影子快照 backups/Insulation#1_20261026.bak；
   ➔ 通过 Bridge VI 依次切削注入 'API: Self Test'、'API: Start Test'、'API: Read Voltage'；
   ➔ 调用 Connect Paired Tunnels 自动缝合移位寄存器隧道与错误簇；
   ➔ 🌟【强势亮点】同步烧录 VI Description (前面板说明)：将全套 API 调用规范与五步开发任务卡注入 VI 属性！
3. [调用 csm_add_to_project]
   ➔ 解析 MainProject.lvproj XML 树，在 'Drivers' 节点追加该 VI 引用。
4. [调用 csm_verify_syntax]
   ➔ 全工程静态扫描，确认新模块无孤立状态与死锁隐患。

🤖 回复工程师：
“已为您顺利创建 Insulation#1.vi 驱动模块，成功注入 3 个状态分支！
• 移位寄存器隧道已全部自动修复（100% 原生可执行，绝不断线）；
• 🌟 全套 API 步骤与参数规范已自动烧录至 VI Description！您在 LabVIEW 前面板按下 Ctrl+H 即可直接查看标准开发指引；
• 该模块已无感点亮至工程树。请在 LabVIEW 项目浏览器中直接双击体验！”
```

---

## 📦 官方 8 大出厂母版全矩阵

本项目严谨消化并 100% 物理寻址了 NEVSTOP CSM 官方出厂的 **8 大正统工程母版全矩阵**：

| 矩阵分类 | 模板标识 (template_type) | 官方物理文件名 | 最佳适用工况 |
| :--- | :--- | :--- | :--- |
| **① 出厂标准双子星** | `worker` | `CSM Module Template.vi` | 标准单/双循环高内聚状态机，VISA/CAN 设备驱动底座 |
| | `ui` | `CSM User Interface(UI) Module Template.vi` | 人机交互主控制台，事件结构 + 状态驱动双循环 |
| **② 极简微型双子星** | `worker_tiny` | `CSM Module Template - Tiny.vi` | 极简骨架、极低内存，后台轻量级数据采集与运算 |
| | `ui_tiny` | `CSM User Interface(UI) Template - Tiny.vi` | 极简交互，报警确认弹窗、参数输入微型对话框 |
| **③ 参数持久化双星** | `worker_config` | `CSM Module Template(+Configuration).vi` | 内嵌 INI 自动化读写，仪器配方、标定校准数据自动存取 |
| | `ui_config` | `CSM UI Module Template(+Configuration).vi` | 配方管理与参数调试交互界面 |
| **④ 分布式与复用架构**| `dqmh` | `CSM DQMH-Style Template.vi` | 对标 DQMH 请求/广播拓扑，跨网络分布式测试台架 |
| | `reuse` | `CSM Reuse Module.vi` | 标准可复用通用业务库，跨项目工程分包沉淀 |

---

## 📐 架构设计与底层突破

```text
┌────────────────────────────────────────────────────────┐
│     AI 客户端 (Cursor / Antigravity / Claude Desktop)   │
└───────────────────────────┬────────────────────────────┘
                            │ stdio (标准 JSON-RPC 消息管道)
┌───────────────────────────▼────────────────────────────┐
│      🐍 Python FastMCP 业务层 (csm_mcp / server.py)     │
│   ┌────────────────────────────────────────────────┐   │
│   │ 7 大业务原语 Tool + 6 大规范 Skill + 安全沙盒  │   │
│   └───────────────────────┬────────────────────────┘   │
└───────────────────────────┼────────────────────────────┘
                            │ COM / ActiveX (LocalServer32 跨位宽 RPC 穿透)
┌───────────────────────────▼────────────────────────────┐
│  ⚡ LabVIEW 本地平坦化跳板 (csm_agent_bridge_add_state.vi) │
│   ┌────────────────────────────────────────────────┐   │
│   │ 消化 LVOOP 私有类 ➔ 自动穿线 Connect Paired Tunnels│   │
│   └───────────────────────┬────────────────────────┘   │
└───────────────────────────┼────────────────────────────┘
                            │ VI Scripting (原地高精度切削)
┌───────────────────────────▼────────────────────────────┐
│       🎯 目标工业级 CSM 模块 (CAN / VISA / UI / Worker) │
└────────────────────────────────────────────────────────┘
```

1. **双层平坦化跳板**：LabVIEW COM 接口天然无法跨进程传递 LVOOP 私有类对象。我们研制了极简本地 Bridge VI，将外部输入降维为扁平字符串/路径，内部消化面向对象句柄；
2. **LocalServer32 跨位宽穿透**：Windows DCOM 列集封送（Marshalling）底层自动接管了 64 位 Python 与 32 位 LabVIEW 之间的内存转换，彻底打破了传统进程内 DLL 无法跨位宽调用的技术壁垒；
3. **隧道自动缝合 (Connect Paired Tunnels)**：在 Bridge VI 中链式集成穿线节点，切削新增分支的同时秒级缝合所有移位寄存器，彻底解决 VI 断线难题；
4. **前面板原生自文档化 (Auto-Documentation)**：在代码切削闭环的同时，自动为 VI Description 烧录结构化 Markdown 任务卡，消灭“文档债务”。

---

## ❓ 常见问题排错 (FAQ)

### Q1: 提示 `(-2147221005, '无效的类字符串')` 或 `Class not registered`？
* **原因**：Windows 注册表中未找到 `Labview.Application` COM 服务。
* **解决办法**：请至少以管理员身份启动运行一次 LabVIEW，LabVIEW 会自动向 Windows 注册 COM 接口。

### Q2: 提示 `打开VI引用报错 1004`？
* **原因**：传入的路径被当作了模糊字符串，或目标 VI 正在前台被编辑导致互斥锁生效。
* **解决办法**：确保传入的是合法的绝对磁盘路径，且该 VI 未在前台处于运行态（Run Mode）。

### Q3: 运行在低版本 LabVIEW（如 2020、2021）提示版本不兼容？
* **解决办法**：Bridge VI 内部仅有极度精炼的 3 个特工节点：
  `Create From VI Reference.vi` ➔ `Add State Frame.vi`（串联 `Connect Paired Tunnels.vi`） ➔ `Destroy.vi`。
  低版本用户只需在自己的 LabVIEW 中花 1 分钟新建同名 VI 拖入这 3 个原生节点保存，即可在任意版本中秒级复用！

### Q4: 如何在 LabVIEW 中查看 AI 自动生成的 API 步骤任务卡？
* **操作方式**：打开生成的 `.vi`，直接在键盘上按下 **`Ctrl + H`** 唤出即时帮助窗口；或在 VI 前面板右键右上角 VI 图标 ➔ 选择 **VI 属性 (VI Properties)** ➔ 下拉框切换至 **说明信息 (Documentation)**，即可看到完整的格式化 API 说明与任务卡！

---

## 📜 开源协议

本项目采用 [木兰宽松许可证第2版 (Mulan PSL v2)](LICENSE) 授权，欢迎工业自动化同行、高校科研人员及测控开发者自由使用与共建！
