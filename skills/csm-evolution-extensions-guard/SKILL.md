---
name: csm-evolution-extensions-guard
description: 独属于 CSM MCP 演进扩展能力【工程树联动 (csm_add_to_project) 与状态脚本注入 (csm_set_state_script)】的安全与质量控制规范。严格执行 .lvproj 结构完整性保护、CSM 状态跳转语法语义合法性前置拦截、P0 级 C 盘底座只读沙箱继承，以及工程文件自动备份回滚机制。
---

# CSM 演进能力扩展操作与安全治理规范 (CSM Evolution Extensions Guard)

本规范是专门针对 `csm_add_to_project`（工程树联动挂载）和 `csm_set_state_script`（分支 CSM 消息脚本写入）两大演进扩展工具的核心安全准则。
在编写、注册与调度这些演进工具时，**必须强制执行以下硬性约束，严禁破坏项目工程文件结构与 CSM 语法规则！**

---

## 零、 【P0 级最高红线：C盘原生库与官方 CSM 底座绝对只读继承】

> [!CAUTION] 【最高安全禁令：严禁修改/覆盖/删除任何 C 盘底层库与安装文件】
> 1. **全系统库绝对只读**：
>    * 严禁将任何新创建的 VI 挂载到 C 盘官方安装目录下的任何工程或库中；
>    * 严禁对 `C:\Program Files (x86)\National Instruments\`、`vi.lib`、`user.lib` 等系统底座执行任何写操作；
> 2. **写操作白名单限制**：
>    * 工程文件（`.lvproj`）与业务文件（`.vi`）必须 100% 位于用户当前工作区（如 `c:\Users\ASUS\Desktop\CSM\`）及其子目录下，任何指向系统盘的写操作一律触发 `SecurityViolationError` 物理阻断！

---

## 一、 【工程树挂载工具 (`csm_add_to_project`) 安全红线】

1. **XML 结构原子保护与备份**：
   * `.lvproj` 本质是 XML 文件。在对 `.lvproj` 进行任何节点追加前，**必须先在 `backups/` 目录下生成带时间戳的 `.bak` 备份文件**；
   * 采用标准 XML 解析库（`xml.etree.ElementTree`）进行内存树操作与合法性校验，严禁使用盲目的纯文本字符串拼接，杜绝破坏 LabVIEW 工程的 XML 闭合标签或声明头导致工程崩溃。
2. **虚拟文件夹（Virtual Folder）幂等挂载**：
   * 若目标虚拟文件夹（如 `CAN`, `VISA`）不存在，应安全创建 `<Item Name="Folder" Type="Folder">`；
   * 插入前检查该 VI 是否已在工程树中挂载，严禁重复插入相同路径产生冗余冲突项。

---

## 二、 【状态脚本注入工具 (`csm_set_state_script`) 语义守门红线】

当大模型为某个状态分支（如 `Macro: Initialize`）写入右侧 CSM 消息流时，Tool 必须严格扮演**“语法裁判”**：

1. **语法符号严格白名单校验**：
   * 每一行消息脚本文本必须 100% 符合 [csm-architect-standards](../csm-architect-standards/SKILL.md) 官方字典：
     * 同步调用必须带短横杠与@符：`-@ TargetModule`
     * 异步消息必须带尖括号：`-> TargetModule` 或 `->| TargetModule`
     * 状态广播必须带专用标签：`-<status>` 或 `-<interrupt>`
     * 动态订阅必须带专用标签：`-<register>` 或 `-<unregister>`
     * 单行注释必须以 `//` 开头
   * **红线拦截**：严禁出现未定义的野符号（如 `-->`, `==>`, `<-` 等）；一旦检测到，Tool 必须在写入前**直接拒执打回**，并给出修改指引！
2. **死锁先验防御拦截（Pre-Mutation Deadlock Guard）**：
   * 注入包含 `-@ TargetModule` 的同步阻塞调用前，自动执行死锁拓扑分析；
   * 若发现目标模块已经在反向同步等待当前模块，立即物理阻断并报警，杜绝产生双向同步死锁！
3. **动刀前影子备份保障**：
   * 必须在注入前对目标 VI 自动创建 `.bak` 影子副本，失败无条件自动原子回滚。
