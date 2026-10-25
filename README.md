# LabVIEW CSM 专有 MCP 服务器 (LabVIEW Communicable State Machine MCP Server)

本项目是专为 **NI LabVIEW** 下的 **Communicable State Machine (CSM)** 框架量身打造的专有 Model Context Protocol (MCP) 服务器。
它将大模型的工具粒度从传统的“画图级（放置节点、连线）”直接提升到了**“CSM 业务原语级（状态透视、脚手架生成、安全加分支、静态死锁检测）”**，并搭载了严格的内置 Skill 规范矩阵与工业级安全防线。

---

## 🌟 核心架构与 4 大业务原语 Tool

| 工具名称 | 权限分级 | 核心业务职能与特性 |
| :--- | :--- | :--- |
| **`csm_inspect_vi`** | **纯只读 (ReadOnly)** | 零侵入透视目标 CSM VI 的全部状态列表、暴露的 API 接口及前台 `FPWinOpen` 打开状态。 |
| **`csm_create_module`** | **受控写 (Mutating)** | 严格基于 NEVSTOP 官方 8 大正统出厂母版（worker/ui/tiny/config/dqmh/reuse），一键克隆全新模块脚手架。 |
| **`csm_upsert_states`** | **受控写 (Mutating)** | 安全注入状态分支。内嵌 **语义合规守门人**（前缀校验）、**前台互斥检查**（防脏写）、**影子临时备份与原子回滚**（`.bak`）。 |
| **`csm_verify_syntax`** | **纯只读 (ReadOnly)** | 纯 Python 秒级扫描全项目所有模块的跳转路由（`-@`、`->`、`->|`、广播），检测双向同步死锁与语法健康度。 |

---

## 🛡️ 严格内置的 6 大治理与安全 Skill 矩阵

所有规范均完整内置在 `skills/` 目录下，开箱自解释，杜绝 AI 瞎想与越界：

1. **[csm-architect-standards](skills/csm-architect-standards/SKILL.md)**：依据 NEVSTOP CSM-Wiki 官方规范，严格约束正统语法（`-@` 同步、`->` 异步、`<status>` 广播），杜绝野符号与结构破坏。
2. **[csm-mcp-developer-governance](skills/csm-mcp-developer-governance/SKILL.md)**：开发元规则，强制执行影子备份、真机闭环验证与系统盘零污染。
3. **[csm-bridge-operations-guard](skills/csm-bridge-operations-guard/SKILL.md)**：COM 调度中台规范，强制 `Interactive=False` 防死锁与 `FPWinOpen` 前台互斥保护。
4. **[csm-toolset-business-governance](skills/csm-toolset-business-governance/SKILL.md)**：业务工具层规范，强类型校验、语义守门人与统一错误自愈格式。
5. **[csm-real-machine-verification-guard](skills/csm-real-machine-verification-guard/SKILL.md)**：现场真机质检规范，对断线与崩溃零容忍，确保现场环境零污染归位。

---

## 🛑 P0 级神圣不可侵犯最高红线 (Immutable Foundation)

系统底层与所有业务 Tool 均内嵌物理硬件级白名单拦截器：
* **严禁修改/删除 C 盘任何文件**：物理阻断向 `C:\Program Files (x86)\National Instruments\`、`vi.lib`、`user.lib`、官方原生 CSM 安装目录写入任何数据；
* **用户工作区沙箱**：所有写操作必须严格限定在当前用户工程工作区内！

---

## 🚀 启动与配置方式

### 1. 命令行直接运行测试
```powershell
python c:\Users\ASUS\Desktop\CSM\csm_mcp\server.py
```

### 2. 挂载到 AI 客户端 (Antigravity / Claude Desktop / Cursor)
在您的 MCP 配置文件中添加如下条目即可直接使用：
```json
{
  "mcpServers": {
    "labview-csm-mcp": {
      "command": "python",
      "args": [
        "c:\\Users\\ASUS\\Desktop\\CSM\\csm_mcp\\server.py",
        "--stdio"
      ]
    }
  }
}
```
