# csm_agent_bridge_add_state 指导设计规范
# 本 VI 位于 csm_mcp/agent_vi/csm_agent_bridge_add_state.vi
# 作为 LabVIEW 本地平坦化跳板，负责在 LabVIEW 内部安全消化 CSM-Helper.lvclass 类调用。

### 1. 前面板控件 (Controls & Indicators)
- [输入] Target VI Path (String) : 目标 CSM 模块的完整文件路径
- [输入] New State Name (String)  : 需要注入的新状态分支名称 (如 "API: Query IDN")
- [输出] error out (Cluster)     : 执行错误簇 (status: Boolean, code: I32, source: String)

### 2. 程序框图连线 (Block Diagram Wiring)
调用链由 3 个官方特工 VI 直线串联而成：
1. `_csmHelper\API\Create From VI Reference.vi`
   - 入参：VI = Target VI Path
   - 出参：csmhelper out (连接至下一步的 CSM-Helper in)
2. `_csmHelper\API\Add State Frame.vi`
   - 入参：CSM-Helper in (来自上一步)
   - 入参：element = New State Name
   - 出参：CSM-Helper out (连接至下一步的 CSM-Helper in)
3. `_csmHelper\API\Destroy.vi`
   - 入参：CSM-Helper in (来自上一步)
   - 出参：error out (直接连至前面板指示器 error out)

### 3. 安全属性
- 属性勾选：Execution -> Reentrant Execution (Preallocated) 或 Non-reentrant
- 运行时行为：非模态、静默执行、不弹出任何对话框。
