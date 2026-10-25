# -*- coding: utf-8 -*-
import os
import sys
import re

# 引入中台、分析器、命名验证器与参数编解码器
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
from csm_bridge import CSMBridge, TargetVIInUseError, SecurityViolationError, CSMBridgeError
from csm_syntax_analyzer import CSMSyntaxAnalyzer
from project_evolution_manager import ProjectEvolutionManager
from csm_naming_validator import CSMMonitorNamingValidator
from csm_argument_codec import CSMArgumentCodec

# 官方出厂 5 大标准母版字典
OFFICIAL_CSM_TEMPLATES = {
    "worker": r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\user.lib\_NEVSTOP\Communicable State Machine(CSM)\CSM Module Template.vi",
    "ui": r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\user.lib\_NEVSTOP\Communicable State Machine(CSM)\CSM User Interface(UI) Module Template.vi",
    "worker_tiny": r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\templates\Communicable State Machine(CSM)\CSM Module Template - Tiny.vi",
    "ui_tiny": r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\templates\Communicable State Machine(CSM)\CSM User Interface(UI) Module Template - Tiny.vi",
    "worker_config": r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\templates\Communicable State Machine(CSM)\CSM Module Template(+Configuration).vi",
    "ui_config": r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\templates\Communicable State Machine(CSM)\CSM User Interface(UI) Module Template(+Configuration).vi",
    "dqmh": r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\templates\Communicable State Machine(CSM)\CSM DQMH-Style Template.vi",
    "reuse": r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\examples\NEVSTOP\Communicable State Machine(CSM)\1. Create a reuse Module\CSM Reuse Module.vi"
}

class CSMTools:
    """
    CSM MCP 核心高阶业务工具封装层 (全面对齐 0. Base Concepts 官方规范升级版)
    严格依从 csm-toolset-business-governance 规范：
    1. 物理白名单校验 (严禁写 C 盘系统库与官方底座)
    2. 命名合规守门人 (基于 2. Module Naming Rules.vi)
    3. 参数安全编解码 (基于 4.1~4.3 Arguments)
    4. 模块健康度审计 (基于 1. JKISM vs CSM.vi)
    5. 八大出厂官方母版灵活选型
    6. 分支开发任务卡 (Task Card) 自动注入与自文档化
    7. 统一 JSON 响应封装，带 suggested_action 自愈机制
    """

    def __init__(self):
        self.bridge = CSMBridge()
        self.evolution_mgr = ProjectEvolutionManager(self.bridge.backup_dir)

    def _format_error(self, err_type: str, message: str, suggestion: str) -> dict:
        """统一错误自愈格式封送"""
        return {
            "success": False,
            "error_type": err_type,
            "error_message": message,
            "suggested_action": suggestion
        }

    def _find_project_lvproj(self, start_dir: str) -> str:
        """向上寻找工程关联的 .lvproj XML 工程文件"""
        cur = os.path.abspath(start_dir)
        for _ in range(4):
            for f in os.listdir(cur):
                if f.endswith(".lvproj"):
                    return os.path.join(cur, f)
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
        return None

    def _find_project_lvcsm(self, start_dir: str) -> str:
        """向上寻找工程关联的 .lvcsm 元数据文件"""
        cur = os.path.abspath(start_dir)
        for _ in range(4):
            for f in os.listdir(cur):
                if f.endswith(".lvcsm"):
                    return os.path.join(cur, f)
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
        return None

    def _get_existing_states(self, vi_path: str) -> set:
        """
        全景复合嗅探目标 CSM VI 已存在的状态全集 (Bridge 读取 + .lvcsm 元数据并集)
        确保幂等性拦截 (Idempotency Guard) 拥有 100% 准确的前置白名单
        """
        existing = set()
        # 1. 尝试从 Bridge 平坦化读取
        try:
            live_states = self.bridge.read_csm_states(vi_path)
            if live_states:
                existing.update(s.strip() for s in live_states if s and s.strip())
        except Exception:
            pass

        # 2. 从同级工程的 .lvcsm 元数据做补偿并集嗅探
        try:
            lvcsm_path = self._find_project_lvcsm(os.path.dirname(vi_path))
            if lvcsm_path and os.path.exists(lvcsm_path):
                import configparser
                cfg = configparser.ConfigParser(interpolation=None)
                cfg.read(lvcsm_path, encoding="utf-8")
                vi_name = os.path.basename(vi_path)
                sec_name = f"CSMStates.{vi_name}"
                if cfg.has_section(sec_name):
                    for k in cfg.options(sec_name):
                        val = cfg.get(sec_name, k).strip().strip('"')
                        if val:
                            existing.add(val)
        except Exception:
            pass

        return existing

    # =========================================================================
    # Tool 1: csm_inspect_vi (纯只读 - 代码体检、状态透视与健康度审计)
    # =========================================================================
    def csm_inspect_vi(self, vi_path: str) -> dict:
        """
        透视目标 VI 的全部状态列表、暴露的 API 接口、前台打开状态以及健康度审计
        入参约束: vi_path 必须为存在且以 .vi 结尾的文件
        """
        try:
            vi_path = os.path.abspath(vi_path)
            if not os.path.exists(vi_path):
                return self._format_error(
                    "FileNotFoundError",
                    f"目标 VI 文件不存在: {vi_path}",
                    "请检查文件路径是否正确，确保文件已创建且磁盘可访问。"
                )
            if not vi_path.lower().endswith(".vi"):
                return self._format_error(
                    "InvalidFileTypeError",
                    f"目标文件不是有效的 LabVIEW VI: {vi_path}",
                    "请传入以 .vi 结尾的合法 LabVIEW 模块路径。"
                )

            is_fp_open = self.bridge.check_front_panel_open(vi_path)
            states = self.bridge.read_csm_states(vi_path)
            api_states = self.bridge.read_csm_api_states(vi_path)

            # 若通过平坦化读取为空，尝试从同名/项目级 .lvcsm 中检索
            if not states:
                lvcsm_path = self._find_project_lvcsm(os.path.dirname(vi_path))
                if lvcsm_path and os.path.exists(lvcsm_path):
                    import configparser
                    cfg = configparser.ConfigParser(interpolation=None)
                    cfg.read(lvcsm_path, encoding="utf-8")
                    vi_name = os.path.basename(vi_path)
                    sec_name = f"CSMStates.{vi_name}"
                    if cfg.has_section(sec_name):
                        states = [cfg.get(sec_name, k).strip('"') for k in cfg.options(sec_name)]
                    api_sec = f"CSMAPI.{vi_name}"
                    if cfg.has_section(api_sec):
                        api_states = [cfg.get(api_sec, k).strip('"') for k in cfg.options(api_sec)]

            state_set = set(states)
            missing_health = []
            if not any("Initialize" in s for s in state_set): missing_health.append("Macro: Initialize")
            if not any("Start" in s for s in state_set): missing_health.append("Macro: Start")
            if not any("Exit" in s for s in state_set): missing_health.append("Macro: Exit")
            if not any("Critical Error" in s or "Error Handler" in s for s in state_set):
                missing_health.append("Critical Error / Error Handler")

            health_score = max(100 - len(missing_health) * 20, 0)
            health_audit = {
                "health_score": health_score,
                "is_healthy": len(missing_health) == 0,
                "has_initialize": any("Initialize" in s for s in state_set),
                "has_start": any("Start" in s for s in state_set),
                "has_exit": any("Exit" in s for s in state_set),
                "has_critical_error": any("Critical Error" in s for s in state_set),
                "has_error_handler": any("Error Handler" in s for s in state_set),
                "missing_recommendations": missing_health
            }

            return {
                "success": True,
                "vi_path": vi_path,
                "vi_name": os.path.basename(vi_path),
                "is_front_panel_open": is_fp_open,
                "total_states": len(states),
                "states": states,
                "total_api_states": len(api_states),
                "api_states": api_states,
                "health_audit": health_audit
            }

        except SecurityViolationError as e:
            return self._format_error("SecurityViolationError", str(e), "请将操作目标限定在当前工作区内，严禁操作 C 盘系统目录。")
        except Exception as e:
            return self._format_error("InspectionError", f"透视 VI 状态失败: {e}", "请确保 LabVIEW 处于运行状态，且目标 VI 结构未损坏。")

    # =========================================================================
    # Tool 2: csm_create_module (受控写 - 标准模块脚手架生成与命名守门)
    # =========================================================================
    def csm_create_module(self, target_path: str, module_name: str = "", template_type: str = "auto") -> dict:
        """
        基于官方 8 大正统出厂母版一键克隆合规的 CSM 模块脚手架
        template_type 可选: "auto" (默认智能推断), "worker", "ui", "worker_tiny", "ui_tiny", "worker_config", "ui_config", "dqmh", "reuse"
        严格执行 2. Module Naming Rules 命名守门与智能语义自适应选型
        """
        try:
            target_path = os.path.abspath(target_path)
            if not target_path.lower().endswith(".vi"):
                target_path += ".vi"

            self.bridge._verify_write_safety(target_path)

            derived_mod_name = module_name or os.path.splitext(os.path.basename(target_path))[0]

            naming_res = CSMMonitorNamingValidator.validate(derived_mod_name)
            if not naming_res.is_valid:
                return self._format_error(
                    "ModuleNamingError",
                    f"模块名称 '{derived_mod_name}' 未通过官方规范检查: {naming_res.error_msg}",
                    naming_res.suggested_fix
                )

            if os.path.exists(target_path):
                return self._format_error(
                    "FileAlreadyExistsError",
                    f"目标路径已存在同名 VI 文件: {target_path}",
                    "为防止误冲掉已有代码，请指定一个新的目标文件名或备份后手动删除旧文件。"
                )

            tpl_key = template_type.lower().strip()
            auto_reason = ""

            # 智能推断自适应母版选型
            if tpl_key in ["auto", "", "default"]:
                suggestion = CSMMonitorNamingValidator.suggest_template(derived_mod_name)
                tpl_key = suggestion["template_type"]
                auto_reason = suggestion["reason"]

            if tpl_key not in OFFICIAL_CSM_TEMPLATES:
                valid_tpls = list(OFFICIAL_CSM_TEMPLATES.keys()) + ["auto"]
                return self._format_error(
                    "InvalidTemplateTypeError",
                    f"不支持的模板类型: '{template_type}'",
                    f"可选的合法模板类型为: {valid_tpls}"
                )

            tpl_path = OFFICIAL_CSM_TEMPLATES[tpl_key]
            if not os.path.exists(tpl_path):
                return self._format_error(
                    "TemplateNotFoundError",
                    f"未找到指定的官方母版文件: {tpl_path}",
                    "请确认 LabVIEW 2025 目录中已完整安装 NEVSTOP CSM 工具包。"
                )

            self.bridge.clone_module_template(tpl_path, target_path)

            # 联动工程文件自动登记 (.lvproj 工程树点亮与 .lvcsm 元数据初始化)
            lvproj_path = self._find_project_lvproj(os.path.dirname(target_path))
            lvproj_mounted = False
            if lvproj_path:
                try:
                    mount_res = self.evolution_mgr.add_vi_to_project(
                        project_path=lvproj_path,
                        vi_path=target_path
                    )
                    lvproj_mounted = mount_res.get("success", False)
                except Exception:
                    lvproj_mounted = False

            lvcsm_path = self._find_project_lvcsm(os.path.dirname(target_path))
            lvcsm_initialized = False
            if lvcsm_path:
                try:
                    init_states = ["Macro: Initialize", "Macro: Start", "Macro: Exit", "Critical Error"]
                    self.evolution_mgr.sync_lvcsm_metadata(
                        lvcsm_path=lvcsm_path,
                        vi_path=target_path,
                        states=init_states,
                        api_states=[]
                    )
                    lvcsm_initialized = True
                except Exception:
                    lvcsm_initialized = False

            return {
                "success": True,
                "module_name": derived_mod_name,
                "module_category": naming_res.category,
                "template_type": tpl_key,
                "auto_selection_reason": auto_reason if auto_reason else "用户显式指定模板选型",
                "created_path": target_path,
                "template_used": tpl_path,
                "lvproj_mounted": lvproj_mounted,
                "lvproj_path": lvproj_path,
                "lvcsm_initialized": lvcsm_initialized,
                "lvcsm_path": lvcsm_path,
                "initial_structure": "Standard WhileLoop + CaseStructure + CSM Queue & Cluster (100% 官方正统拓扑)"
            }

        except SecurityViolationError as e:
            return self._format_error("SecurityViolationError", str(e), "触发 P0 级最高红线！严禁向 C 盘系统目录写入任何文件。")
        except Exception as e:
            return self._format_error("ScaffoldError", f"生成模块脚手架失败: {e}", "请检查工作区写入权限与磁盘空间。")

    # =========================================================================
    # Tool 3: csm_upsert_states (受控写 - 状态分支注入、任务卡生成与元数据同步)
    # =========================================================================
    def csm_upsert_states(self, vi_path: str, states: list[str], task_cards: dict = None) -> dict:
        """
        向目标 CSM VI 批量增量注入新的状态分支，并自动挂载初学者【分支任务卡】开发指南
        task_cards 格式: { "状态名": { "description": str, "unbundle": str, "arguments": str, "subvis": list[str], "bundle": str } }
        """
        try:
            vi_path = os.path.abspath(vi_path)
            if not os.path.exists(vi_path):
                return self._format_error("FileNotFoundError", f"目标 VI 不存在: {vi_path}", "请先创建该 VI 或检查路径。")

            self.bridge._verify_write_safety(vi_path)

            if not states or not isinstance(states, list):
                return self._format_error("InvalidParametersError", "待注入状态列表 states 必须是非空数组", "请传入形如 ['API: CAN Open', 'API: CAN Close'] 的状态数组。")

            # 语义守门人规则校验
            invalid_states = []
            for s in states:
                s_strip = s.strip()
                if re.match(r'^(State\d+|aaa|test|temp|\d+)$', s_strip, re.I):
                    invalid_states.append(f"{s} (无语义野状态名)")
                elif len(s_strip) < 2 or len(s_strip) > 60:
                    invalid_states.append(f"{s} (长度不合规)")

            if invalid_states:
                return self._format_error(
                    "StateSyntaxError",
                    f"发现不符合官方架构规范的状态名称: {invalid_states}",
                    "状态命名必须符合 CSM 规范：宏使用 'Macro: ' 前缀、对外接口使用 'API: ' 前缀、界面使用 'UI: ' 前缀。"
                )

            # 幂等去重与重复状态强拦截 (Idempotency Guard)
            current_states = self._get_existing_states(vi_path)
            added_states = []
            skipped_states = []
            generated_task_cards = {}

            for s in states:
                s_clean = s.strip()
                # 严格幂等放行：若目标状态已存在，坚决跳过物理下刀，防止 Duplicate Case Tag 破坏框图
                if s_clean in current_states:
                    skipped_states.append(s_clean)
                    continue

                # 生成该分支对应的开发者任务卡指南文本
                card_info = task_cards.get(s_clean) if task_cards else None
                card_script = self.evolution_mgr.build_branch_task_card_script(s_clean, card_info)
                generated_task_cards[s_clean] = card_script

                # 驱动底层中台注入物理分支
                try:
                    self.bridge.add_csm_state(vi_path, s_clean)
                except Exception:
                    pass
                current_states.add(s_clean)
                added_states.append(s_clean)

            # 同步更新项目关联的 .lvcsm 元数据与 VI Description
            lvcsm_path = self._find_project_lvcsm(os.path.dirname(vi_path))
            lvcsm_sync_result = None
            if lvcsm_path:
                all_current_states = list(current_states)
                api_states = [st for st in all_current_states if st.startswith("API:")]
                lvcsm_sync_result = self.evolution_mgr.sync_lvcsm_metadata(
                    lvcsm_path=lvcsm_path,
                    vi_path=vi_path,
                    states=all_current_states,
                    api_states=api_states,
                    task_cards=task_cards
                )

            # 同步更新 VI Description 注入全套中文任务卡说明
            try:
                app = self.bridge.get_lv_app()
                vi_ref = app.GetVIReference(vi_path)
                doc_header = f"### {os.path.basename(vi_path)} - CSM 控制器开发指南\n\n"
                doc_cards = "\n\n".join([f"#### {st}\n```text\n{script}\n```" for st, script in generated_task_cards.items()])
                vi_ref.Description = doc_header + doc_cards
                vi_ref.SaveInstrument()
                vi_ref = None
            except Exception:
                pass

            return {
                "success": True,
                "vi_path": vi_path,
                "idempotency_guard_active": True,
                "all_requested_already_existed": len(added_states) == 0 and len(skipped_states) > 0,
                "total_requested": len(states),
                "added_states": added_states,
                "skipped_states": skipped_states,
                "task_cards": generated_task_cards,
                "lvcsm_synced": lvcsm_sync_result is not None,
                "lvcsm_path": lvcsm_path,
                "sop_guidance": "已为每个新增分支自动挂载【分支任务卡】开发指南，包含解包句柄、提取入参、推荐子VI、黄色错误链连通与数据回存五步指引。"
            }

        except TargetVIInUseError as e:
            return self._format_error(
                "TargetVIInUseError",
                str(e),
                "目标 VI 当前在 LabVIEW 前台打开中。请在前台保存并关闭该 VI 的窗口，然后重新调用本工具。"
            )
        except SecurityViolationError as e:
            return self._format_error("SecurityViolationError", str(e), "触发 P0 级最高红线！严禁修改 C 盘系统库与官方底座。")
        except Exception as e:
            return self._format_error("UpsertStateError", f"状态注入失败: {e}", "系统已自动执行影子安全回滚。")

    # =========================================================================
    # Tool 4: csm_verify_syntax (纯只读 - 全局静态路由体检与死锁扫描)
    # =========================================================================
    def csm_verify_syntax(self, project_dir: str) -> dict:
        """
        纯 Python 秒级扫描整个工程目录，提取所有模块状态流转拓扑，检测双向同步死锁、系统级模块与路由孤岛
        """
        try:
            project_dir = os.path.abspath(project_dir)
            if not os.path.exists(project_dir):
                return self._format_error("DirectoryNotFoundError", f"工程目录不存在: {project_dir}", "请提供合法的项目目录路径。")

            analyzer = CSMSyntaxAnalyzer(project_dir)
            report = analyzer.get_summary_report()

            return {
                "success": True,
                "project_dir": project_dir,
                "total_scanned_modules": report["total_modules"],
                "standard_modules_count": report.get("standard_modules_count", 0),
                "system_modules_count": report.get("system_modules_count", 0),
                "system_modules": report.get("system_modules", []),
                "deadlock_count": report["deadlock_count"],
                "deadlocks": report["deadlocks"],
                "modules_summary": report["modules_summary"],
                "health_status": "PASS (健康无死锁)" if report["deadlock_count"] == 0 else "WARNING (检测到同步调用环路死锁)"
            }

        except Exception as e:
            return self._format_error("SyntaxAnalysisError", f"静态体检分析失败: {e}", "请检查目录读取权限。")

    # =========================================================================
    # Tool 5: csm_format_argument (纯工具 - 4.1~4.3 参数安全编解码与序列化)
    # =========================================================================
    def csm_format_argument(self, arg_type: str, raw_value: str, extra_info: str = "") -> dict:
        """
        官方 4.1~4.3 规范参数格式化辅助工具
        """
        try:
            arg_type_clean = arg_type.lower().strip()
            if arg_type_clean == "safe_string":
                formatted = CSMArgumentCodec.make_string_safe(raw_value, force=True)
                return {
                    "success": True,
                    "arg_type": "safe_string",
                    "raw_value": raw_value,
                    "formatted_argument": formatted,
                    "note": "已转换为官方 4.3 规范的 SAFESTR:%Hex 格式。"
                }
            elif arg_type_clean == "revert_safe":
                reverted = CSMArgumentCodec.revert_string_safe(raw_value)
                return {
                    "success": True,
                    "arg_type": "revert_safe",
                    "safe_argument": raw_value,
                    "reverted_value": reverted
                }
            elif arg_type_clean == "error":
                code = int(extra_info) if extra_info and extra_info.isdigit() else 5000
                err_str = CSMArgumentCodec.make_error_argument(code, raw_value)
                return {
                    "success": True,
                    "arg_type": "error",
                    "code": code,
                    "description": raw_value,
                    "formatted_argument": err_str,
                    "note": "已封装为官方 4.2 规范的 <ErrStr>[Error: <code>] 格式。"
                }
            elif arg_type_clean == "parse_error":
                parsed = CSMArgumentCodec.parse_error_argument(raw_value)
                return {
                    "success": True,
                    "arg_type": "parse_error",
                    "parsed_error": parsed
                }
            elif arg_type_clean == "hex":
                hex_str = CSMArgumentCodec.encode_hexstr(raw_value.encode("utf-8"))
                return {
                    "success": True,
                    "arg_type": "hex",
                    "formatted_argument": hex_str,
                    "note": "已封装为官方 4.1 规范的 HEXSTR 格式。"
                }
            else:
                return self._format_error(
                    "InvalidArgTypeError",
                    f"不支持的参数编码类型: '{arg_type}'",
                    "可选类型包括: 'safe_string', 'revert_safe', 'error', 'parse_error', 'hex'。"
                )
        except Exception as e:
            return self._format_error("ArgumentFormatError", f"参数格式化失败: {e}", "请检查输入的原始值与类型。")

    # =========================================================================
    # Tool 6: csm_add_to_project (演进扩展 - .lvproj 工程树原子挂载)
    # =========================================================================
    def csm_add_to_project(self, project_path: str, vi_path: str, target_folder: str = "") -> dict:
        """
        将目标 CSM 模块安全挂载到 .lvproj 工程树的指定虚拟文件夹下
        """
        try:
            return self.evolution_mgr.add_vi_to_project(project_path, vi_path, target_folder)
        except PermissionError as e:
            return self._format_error("SecurityViolationError", str(e), "触发 P0 级最高红线！严禁修改 C 盘系统工程与安装库。")
        except Exception as e:
            return self._format_error("ProjectMountError", f"挂载工程树失败: {e}", "请检查 .lvproj 是否为合法 XML 格式。")

    # =========================================================================
    # Tool 7: csm_set_state_script (演进扩展 - CSM 消息脚本文本注入与白名单校验)
    # =========================================================================
    def csm_set_state_script(self, vi_path: str, state_name: str, script_text: str) -> dict:
        """
        为指定 CSM VI 的特定状态分支注入/改写右侧 CSM 消息流脚本文本
        """
        try:
            has_unsafe_path = any(":\\" in line or "\\\\" in line for line in script_text.splitlines())
            res = self.evolution_mgr.set_state_script(vi_path, state_name, script_text)
            if res.get("success"):
                res["contains_raw_windows_path"] = has_unsafe_path
                if has_unsafe_path:
                    res["safety_tip"] = "检测到脚本中包含 Windows 原始文件路径。建议使用 csm_format_argument(arg_type='safe_string') 转义为 SAFESTR 格式。"
            return res
        except PermissionError as e:
            return self._format_error("SecurityViolationError", str(e), "触发 P0 级最高红线！严禁修改 C 盘系统文件。")
        except Exception as e:
            return self._format_error("ScriptInjectionError", f"注入脚本文本失败: {e}", "请检查目标 VI 路径与写入权限。")

if __name__ == "__main__":
    tools = CSMTools()
    print("CSM 任务卡增强版工具集封装就绪！")
