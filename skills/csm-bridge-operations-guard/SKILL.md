---
name: csm-bridge-operations-guard
description: 独属于第二步【Python COM 调度中台 (csm_bridge.py)】的底层运行时操作安全与限制规范。强制实施 LabVIEW COM 句柄生命周期管理、前台互斥检查 (FPWinOpen)、影子临时副本与异常回滚机制、Interactive=False 防模态死锁，以及零破坏性操作红线。
---

# CSM COM 调度中台运行与安全限制规范 (CSM Bridge Operations Guard)

本规范是专门针对 `csm_mcp/core/csm_bridge.py` 调度中台的核心安全守则。
在编写、调用中台与 LabVIEW 交互的任何代码时，**必须强制执行以下硬性约束，任何违反操作均视为高危违规行为！**

---

## 零、 【核心红线：C盘原生库与官方 CSM 底座绝对只读保护 (P0 Absolute Immutable Boundary)】

> [!CAUTION] 【最高安全警报：严禁覆写/修改/删除任何 C 盘底层库与安装文件】
> 1. **全系统库只读红线**：
>    * 中台在调用任何底层特工 VI 时，**严格限定在纯只读（Read-Only）探查与受控引用范围**。
>    * **严禁执行任何指向 C 盘系统目录的 `SaveInstrument()`**！严禁覆写、删除或篡改 `C:\Program Files (x86)\National Instruments\` 下的任何 `vi.lib`、`user.lib`、`instr.lib`、`_NEVSTOP` 官方代码库或注册表！
> 2. **写操作白名单限制**：
>    * 所有写操作（包括克隆模块、状态分支注入、跳板运行、`.bak` 影子备份）的物理目标路径**必须严格限定在当前工作区（如 `c:\Users\ASUS\Desktop\CSM\`）内**！
>    * 中台内部必须对任何即将保存的目标路径执行白名单校验，一旦发现路径指向 `C:\Program Files` 等系统目录，立即抛出 `SecurityViolationError` 并物理熔断阻断！

---

## 一、 【前台互斥与脏读脏写防御 (Front-Panel Concurrency Guard)】

1. **写前状态探查（Mandatory Check Before Mutate）**：
   * 在对任何目标 VI（如 `VISA.vi`）执行状态注入、分支增加或框图修改前，必须首先调用 COM 属性检查：
     ```python
     is_open = vi_ref.FPWinOpen
     ```
   * **前台打开时（`FPWinOpen == True`）的红线处理**：
     * **严禁暗中修改并强行存盘**！否则用户前台随手一次 `Ctrl+S` 就会用旧内存镜像覆盖后台写入，造成不可逆的“代码吞没”；
     * **强制策略**：抛出明确异常或返回状态码 `TargetVIInUseError`，明确提示：“目标 VI 正处于前台编辑状态，请保存并关闭前台窗口后再执行自动化注入”，或由中台确认保存后平滑关闭前台窗口。

---

## 二、 【影子临时备份与原子回滚机制 (Shadow Backup & Rollback)】

1. **动刀前必须备份（Zero-Touch Without Backup）**：
   * 在对现有 VI 文件进行任何写操作（`SaveInstrument`）前，中台必须自动在 `csm_mcp/backups/` 目录下生成一份带时间戳的副本：
     `backups/<vi_name>_<YYYYMMDD_HHMMSS>.bak`
2. **原子异常回滚（Atomic Rollback on Error）**：
   * 必须采用标准的 `try ... except ...` 事务环绕模式；
   * 一旦 COM 调用发生异常、返回的 `error out.status == True`、或 LabVIEW 报告编译损坏，Python 中台必须**在 `except` 块中无条件将 `.bak` 文件覆盖还原回原目标路径**，并打印清晰告警，确保工作区永远不会留下半成品损坏文件。

---

## 三、 【防死锁与非模态运行红线 (Anti-Deadlock & Headless Execution)】

1. **禁用模态交互（Interactive = False）**：
   * 连接 LabVIEW 进程后，初始化阶段必须设置：
     ```python
     lv_app.Interactive = False
     ```
   * 杜绝 LabVIEW 触发“是否保存修改”、“依赖文件丢失”等需要人工点击确认的 Windows 模态弹窗，防止后台进程永久挂起。
2. **句柄释放承诺（Deterministic Resource Cleanup）**：
   * 所有的 `GetVIReference` 操作必须在 `finally` 块中完成显式置空释放（`vi_ref = None`）；
   * 严禁无节制打开 VI 引用而不释放，防止 LabVIEW 内部句柄池泄漏导致文件被系统级锁定。

---

## 四、 【接口平坦化输入输出约束 (Strict Flat Parameter Typing)】

1. **严禁越界传递类实例**：
   * 中台调用任何 VI，参数类型必须限定在：`str`（路径、名称）、`int`/`float`（数值）、`bool`、`list[str]`（平坦一维数组）；
   * 严禁尝试在 Python 内存中直接构造、解包或封送 LabVIEW LVOOP 类私有数据；复杂类调用必须交由 `agent_vi/` 本地跳板处理。

2. **静默执行与保存规范**：
   * 调用 `Run(False)` 必须以非交互方式异步或同步等待执行完成；
   * 修改确认无误后方可执行 `SaveInstrument()`，随后退出引用。
