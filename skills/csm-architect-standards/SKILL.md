---
name: csm-architect-standards
description: 专门依据 NEVSTOP CSM (Communicable State Machine) 官方 Wiki 与最佳实践规范，指导 AI 进行 LabVIEW 模块化架构设计、状态命名、消息路由编写与死锁防御。强约束 AI 杜绝主观臆造复杂语法、杜绝破坏状态机拓扑、杜绝同步死锁，限制 AI 严格在 CSM 官方正统范式内输出。
---

# 可通信状态机 (CSM) 架构设计与 DSL 规范 (CSM Architect Standards)

本规范专门用于对齐 [NEVSTOP CSM-Wiki](https://nevstop-lab.github.io/CSM-Wiki/) 官方技术底座。
当 AI 助手思考、设计、生成或修改任何基于 Communicable State Machine (CSM) 框架的 LabVIEW 代码、状态流转脚本及模块拓扑时，**必须强制执行以下红线与工程准则，严禁主观臆造任何未经官方定义的语法！**

---

## 零、 【基石神圣不可侵犯红线：C盘原生环境与官方底座绝对只读 (Zero-Touch System Baseline)】

> [!CAUTION] 【最高安全禁令：严禁修改、污染、删除任何 C 盘底层库与 CSM 官方原生源码】
> 1. **全系统底座只读沙箱**：
>    * 严禁修改或删除 `C:\Program Files (x86)\National Instruments\`、`C:\ProgramData\` 下的任何 `vi.lib`、`user.lib`、`instr.lib`、系统 VI 或依赖项！
>    * 安装在 `user.lib\_NEVSTOP\Communicable State Machine(CSM)\` 下的所有官方特工 VI、类（`CSM-Helper.lvclass`）、模板、菜单及配套脚本是绝对不可改动的**出厂基石**，**仅限纯只读引用与调用，严禁调用 Save 保存覆盖，严禁破坏其原生拓扑结构**！
> 2. **创作边界严格限制在用户工作区**：
>    * 所有架构生成、模块克隆、分支注入及业务 VI 修改，必须严格发生在用户指定的工程工作区（如 `c:\Users\ASUS\Desktop\CSM\`）内，严禁越界修改系统底座！

---

## 一、 【核心铁律：杜绝 AI 主观瞎想与过度设计 (Anti-Hallucination & Scope Restraint)】

1. **结构不可动摇原则（95% 拓扑固化）**：
   * CSM 是基于 JKI State Machine (JKISM) 的严格模式演进。标准结构永远是：
     * **外层 `While Loop`** + **移位寄存器**（数据簇 `Cluster` 与状态队列 `State Queue`）；
     * **核心主 `Case Structure`**；
     * **右侧出口连接 `Parse State Queue++.vi` 或 `Build State String with Arguments++.vi`**。
   * **红线禁令**：严禁 AI 自行引入任何非标准的并发循环（除非规范许可的 Side Loop）、严禁删除移位寄存器中的穿透连线、严禁私自修改状态选择器的枚举连线拓扑！

2. **状态粒度适度原则（KISS & YAGNI）**：
   * 严禁为一个纯计算或两行数学逻辑拆出 5~6 个碎片化状态分支；
   * 严禁把耗时阻塞死循环（如无限重试）写死在单个 Case 分支内；耗时操作必须借助轮询状态机转移、定时器检查（Check Timeout.vi）或 Side Loop 处理。

---

## 二、 【CSM 正统消息路由语法字典 (The Canonical CSM DSL)】

在 CSM 条件结构右侧的“字符串常量”中，AI 生成的每一行脚本文本**必须 100% 遵守以下标准语法，严禁臆造新符号**：

| 语法格式 | 消息类型 | 行为语义与约束 |
| :--- | :--- | :--- |
| `State: Name >> arguments` | **本地顺序消息** | 在当前模块内部排队执行。`>>` 右侧为参数。 |
| `API: Name >> arguments -@ TargetModule` | **同步阻塞调用 (Sync)** | 发送消息给目标模块并**强制等待其执行完毕及返回响应**。超时时间由全局配置决定。 |
| `API: Name >> arguments -> TargetModule` | **异步调用 (Async with Reply)** | 向目标模块投递消息，不阻塞当前流程，目标完成或出错时异步回调。 |
| `API: Name >> arguments ->\| TargetModule` | **无应答异步 (Fire & Forget)** | 纯单向投递，目标模块执行完毕后绝不回调。 |
| `Status >> arguments -><status>` | **普通状态广播 (Broadcast)** | 向系统广播本模块的常规状态变更（如 `<Ready>`, `<Busy>`）。 |
| `Interrupt >> arguments -><interrupt>` | **中断状态广播 (Interrupt)** | 广播高优先级中断状态，触发订阅者优先处理。 |
| `Status@Source >> API@Handler -><register>` | **动态状态订阅 (Register)** | 将 `Source` 模块的 `Status` 事件动态绑定到 `Handler` 模块的 `API` 状态。 |
| `Status@Source >> API@Handler -><unregister>` | **取消订阅 (Unregister)** | 解除两者的事件监听绑定。 |
| `// 注释内容` | **单行注释** | `//` 右侧的所有文本均被框架忽略。 |

> [!CAUTION] 严禁混淆箭头方向与符号！
> * 同步阻塞必须带短横杠与@符：`-@ TargetModule`
> * 异步带右尖括号：`-> TargetModule`
> * 单向丢弃带竖线：`->| TargetModule`
> * 严禁使用未定义的 `-->`, `==>`, `<-` 等野符号！

---

## 三、 【状态命名标准化规范 (State Naming Conventions)】

所有 Case Structure 的分支名称（`Frame Name`）必须严格遵循前缀命名法，杜绝出现无语义的 `State1`, `DoSomething`：

1. **`Macro:` 宏指令分支**：
   * 用于模块生命周期总控与复合流程调度；
   * **标准四大天王**（每个模块模板必备）：
     * `Macro: Initialize`：模块启动、内存簇复位、读取配置文件；
     * `Macro: Start`：启动定时器、使能硬件总线；
     * `Macro: Exit`：释放 VISA/CAN/TCP 硬件资源、注销广播注册表、通知退出事件；
     * `Error Handler`：统一错误接管，处理软硬件异常，发布错误状态。
2. **`API:` 外部公开接口分支**：
   * 只有对外暴露、允许其他模块通过 `-@` 或 `->` 调用的状态才使用 `API:` 前缀；
   * 示例：`API: Write Data`, `API: Open VISA`, `API: Reset Device`。
3. **`UI:` 界面与交互分支**：
   * 负责前面板控件更新、按钮事件响应、界面渲染；
   * 示例：`UI: Update Chart`, `UI: Enable Buttons`, `UI: Refresh Table`。
4. **内部业务处理分支**：
   * 模块私有状态，不带 `API:` 前缀；
   * 示例：`Parse Hex Packet`, `Check Buffer Size`, `Poll Register`。

---

## 四、 【死锁防御与安全性红线 (Deadlock Prevention Rules)】

AI 在设计 CSM 调用链时，必须进行**死锁先验分析**：

1. **禁止双向同步死锁（Mutual Sync Block）**：
   * **红线**：严禁模块 A 在执行某个状态时使用 `-@ B`（同步等 B），而模块 B 在处理该请求期间又使用 `-@ A`（同步等 A）！
   * **修正准则**：模块间双向交互必须改为：A 异步发 `->| B`，B 处理完后再异步回调 `->| A`，或者通过全局广播 `<status>` 解耦！
2. **退出宏级联死锁防范**：
   * 当主控模块执行 `Macro: Exit` 关闭子模块时：
     ```text
     Macro: Exit -@ SubModuleA
     Macro: Exit -@ SubModuleB
     ```
   * 必须确保子模块内部的 `Macro: Exit` 不会反向等待主控模块的反馈，且每个子模块应设置合理的退出超时（Wait for Module to Exit）。
3. **参数特殊字符必须使用 Safe Arguments**：
   * 当参数（Arguments）包含换行符、空格、制表符、单双引号或特殊标点时，严禁裸拼字符串！
   * 必须通过官方 `CSM - Make String Arguments Safe.vi`（或 Python 端的等效 Base64/Hex 编解码）转义，杜绝解析断裂。

---

## 五、 【元数据与自文档化规范 (Metadata Synchronization)】

依据 NEVSTOP 官方规范，CSM 具备高内聚自文档化特性：
1. **名实相符**：新增一个 `API:` 分支时，必须同步在 VI Description（或 `.lvcsm` 项目元数据文件）中登记该 API 的作用及入参格式说明；
2. **杜绝孤立分支**：新增分支如果既非 `API:` 外部接口，又没有在任何宏或事件中被内部调用，属于无效死代码，必须予以告警或清理。
