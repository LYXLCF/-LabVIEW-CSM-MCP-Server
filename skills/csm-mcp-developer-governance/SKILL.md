---
name: csm-mcp-developer-governance
description: CSM MCP 开发者工程管理与安全防线规范。作为本 MCP 工具集研发的元规则（Meta-Governance），严格约束研发行为必须 100% 遵守 csm-architect-standards 规范，强制执行影子备份、只读探查优先、严禁破坏用户源文件、前后台互斥防死锁及真机闭环验证。
---

# CSM MCP 研发与执行管理规范 (CSM MCP Developer Governance)

本规范是针对 **CSM MCP 工具集与服务本身** 开发、调试、演进与运行的**元规则与安全控制中枢**。
智能体在执行任何测绘、代码生成、COM 调度及 VI 操作时，**必须无条件执行以下治理基准，严禁任何违规跃迁与主观瞎搞！**

---

## 一、 【上位法依从原则 (Hierarchical Compliance)】

1. **绝对遵循架构规范**：
   * 所有针对 CSM VI 的分析、新增、生成逻辑，必须 100% 严格依从 [csm-architect-standards/SKILL.md](../csm-architect-standards/SKILL.md)。
   * 严禁臆造非官方定义的 CSM 语法符号（如未定义的箭头、野广播等）；
   * 严禁破坏 LabVIEW 模板的移位寄存器穿透线和错误链。

2. **严防“偷工减料与伪实现”**：
   * 严禁为了测试通过而编写 mock 假数据糊弄流程；
   * 必须基于真实的 LabVIEW 2025 运行环境与真实工程文件进行真机闭环验证。

---

## 二、 【底座与系统级安全最高红线 (Immutable Foundation & System Integrity - P0)】

> [!CAUTION] 【最高禁令：C盘系统库与官方原生底座绝对零污染、零覆写、只读保护】
> 1. **严禁破坏与篡改 C 盘任何文件**：
>    * 严禁以任何理由创建、写入、修改、覆写或删除 `C:\Program Files (x86)\National Instruments\`、`C:\Program Files\National Instruments\`、`C:\ProgramData\National Instruments\` 及系统盘下的任何底层驱动、运行时库、`vi.lib`、`user.lib`、`instr.lib` 或系统注册表！
> 2. **NEVSTOP CSM 官方原生安装库绝对只读（Read-Only Sanctuary）**：
>    * 安装在 `user.lib\_NEVSTOP\Communicable State Machine(CSM)\` 下的所有官方特工 VI、类（`CSM-Helper.lvclass`）、模板、菜单及配套脚本是不可动摇的**“出厂基石”**。
>    * 智能体仅被授权以纯只读方式获取其引用并作为工具调用，**绝对禁止调用任何 `SaveInstrument()` 保存修改至官方安装目录，绝对禁止删除、重命名或篡改官方原生源码中的任何连线与属性**！
> 3. **操作范围绝对限制在白名单工作区**：
>    * 所有的测试、生成、代码注入、跳板 VI 以及 `.bak` 备份，**只允许在当前用户工作区 `c:\Users\ASUS\Desktop\CSM\` 及其子目录内进行**。任何超出该工作区边界的写操作均构成严重系统安全违规，必须无条件立即阻断！

---

## 三、 【六大工程安全红线 (Safety & Sandbox Boundaries)】

1. **影子备份先行（Shadow Backup First）**：
   * 任何涉及对现有 `.vi` 文件执行写入、修改、注入分支操作的脚本，**在动刀前必须无条件在 `backups/` 目录下生成带时间戳的 `.bak` 文件**！
   * 一旦 COM 抛出异常或返回错误簇，必须由 Python 自动、无条件秒级回滚源文件，严禁留下半成品或脏状态！

2. **前台互斥检查（Concurrency & Lock Protection）**：
   * 调用 COM 操作业务 VI（如 `VISA.vi`）前，必须调用 `FPWinOpen` 检查用户是否在前台打开了该 VI；
   * 严禁在前台打开状态下强行后台写入导致内存与磁盘冲突（脏读脏写）。

3. **防死锁交互限制（Silent & Non-Modal Execution）**：
   * COM 操作必须确保无模态弹窗挂起（`Interactive = False`）；
   * 所有自动化探针与测量必须在 `finally` 块中显式释放 LabVIEW 引用句柄，严禁句柄泄露。

4. **跳板平坦化原则（Isolated OOP Barrier）**：
   * 严禁在外部 Python COM 中直接尝试传递或构造 LabVIEW 类（LVOOP）实例；
   * 类的实例化、操作与销毁必须严格封闭在 LabVIEW 本地跳板 VI（`agent_vi/`）内部，对外暴露的端子永远只能是纯字符串、数值或路径等基础类型。

5. **元数据强一致性（Metadata Synchronization）**：
   * 修改框图状态时，必须同步触发 `.lvcsm` 项目元数据及 VI 说明更新，杜绝“代码已加、元数据隐形”的脱节现象。

6. **只读探针零副作用（Zero-Side-Effect Probing）**：
   * 测绘探针脚本仅允许执行只读探查，严禁对官方 `user.lib` 中的任何母版及系统 VI 写入任何修改。
