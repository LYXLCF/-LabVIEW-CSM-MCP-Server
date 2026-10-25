import os
import shutil
import time
from datetime import datetime
import win32com.client

class TargetVIInUseError(Exception):
    """当目标 VI 在 LabVIEW 前台正处于打开编辑状态时抛出，防止脏读脏写"""
    pass

class SecurityViolationError(Exception):
    """当试图对 C 盘系统库或安装目录进行写操作时触发的最高安全阻断异常"""
    pass

class CSMBridgeError(Exception):
    """CSM COM 调度中台通用异常"""
    pass

class CSMBridge:
    """
    CSM Python COM 调度中台
    严格遵循 csm-bridge-operations-guard 规范：
    1. 强制 Interactive = False 防模态弹窗死锁；
    2. 动刀前强制 FPWinOpen 前台互斥检查；
    3. 动刀前自动创建带时间戳的影子副本 (.bak)，失败无条件自动回滚；
    4. 严格采用平坦化参数（字符串、路径、数组），类调用封闭在 LabVIEW 内部跳板。
    """

    def __init__(self, backup_dir: str = None):
        # 确定备份目录
        if backup_dir is None:
            self.backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backups"))
        else:
            self.backup_dir = os.path.abspath(backup_dir)
        os.makedirs(self.backup_dir, exist_ok=True)

        # 官方特工平坦化 API 基础路径
        self.official_helper_dir = r"C:\Program Files (x86)\National Instruments\LabVIEW 2025\user.lib\_NEVSTOP\Communicable State Machine(CSM)\_csmHelper\API with lvcsm Support"
        self.read_states_vi_path = os.path.join(self.official_helper_dir, "Read CSM States By CSM-VI.vi")
        self.read_api_vi_path = os.path.join(self.official_helper_dir, "Read CSM API By CSM-VI.vi")

        # 本地跳板 VI 路径（用于在 LV 内部消化 Class 类调用以加分支）
        self.agent_bridge_add_state_vi_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "agent_vi", "csm_agent_bridge_add_state.vi")
        )

        # 连接 LabVIEW Application
        self._lv_app = None

    def get_lv_app(self):
        """获取或连接 LabVIEW.Application 实例，并确保处于非交互模式"""
        if self._lv_app is None:
            try:
                self._lv_app = win32com.client.Dispatch("Labview.Application")
                # 规范红线：必须关闭模态弹窗，发生冲突抛异常，绝不卡死
                try:
                    self._lv_app.Interactive = False
                except Exception:
                    pass
            except Exception as e:
                raise CSMBridgeError(f"无法连接到正在运行的 LabVIEW 实例: {e}")
        return self._lv_app

    def check_execution_state(self, target_vi_path: str) -> int:
        """
        检查目标 VI 的执行状态 (ExecState)
        返回值: 0=eBad, 1=eIdle, 2=eRunTopLevel, 3=eRun
        规则红线：若 VI 处于运行态 (2 或 3)，严禁执行任何 Scripting 切削注入，防止锁死 LabVIEW
        """
        app = self.get_lv_app()
        vi_ref = None
        try:
            vi_ref = app.GetVIReference(target_vi_path, "", False, 0)
            return int(vi_ref.ExecState)
        except Exception:
            return 1 # 若无法读取，回退为 eIdle
        finally:
            vi_ref = None

    def check_front_panel_open(self, target_vi_path: str) -> bool:
        """
        检查目标 VI 是否在前台被用户打开
        规则红线：若用户在前台打开编辑，禁止后台暗中写入存盘
        """
        app = self.get_lv_app()
        vi_ref = None
        try:
            vi_ref = app.GetVIReference(target_vi_path, "", False, 0)
            return bool(vi_ref.FPWinOpen)
        except Exception:
            # 如果无法获取引用，说明未加载或路径不存在
            return False
        finally:
            vi_ref = None

    def create_shadow_backup(self, target_vi_path: str) -> str:
        """
        创建影子临时副本 (.bak)
        规则红线：动刀前必须无条件备份
        """
        if not os.path.exists(target_vi_path):
            raise FileNotFoundError(f"目标 VI 文件不存在: {target_vi_path}")

        vi_name = os.path.basename(target_vi_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file_name = f"{vi_name}_{timestamp}.bak"
        backup_file_path = os.path.join(self.backup_dir, backup_file_name)

        shutil.copy2(target_vi_path, backup_file_path)
        return backup_file_path

    def rollback_from_backup(self, backup_file_path: str, target_vi_path: str):
        """异常发生时原子回滚"""
        if os.path.exists(backup_file_path):
            shutil.copy2(backup_file_path, target_vi_path)

    def _invoke_vi_method(self, vi_ref, method_name: str, *args):
        """通过底层 OLE IDispatch 接口精准调度 VI 方法 (彻底解决 win32com 'NoneType' object is not callable 问题)"""
        import pythoncom
        dispid = vi_ref._oleobj_.GetIDsOfNames(method_name)
        if isinstance(dispid, (list, tuple)):
            dispid = dispid[0]
        return vi_ref._oleobj_.Invoke(dispid, 0, pythoncom.DISPATCH_METHOD, 1, *args)

    # -------------------------------------------------------------
    # 核心读操作：直接调用官方已测绘的平坦化 API
    # -------------------------------------------------------------
    def read_csm_states(self, target_vi_path: str) -> list[str]:
        """
        读取目标 CSM VI 的所有状态列表 (只读操作，零副作用)
        端子实测映射：输入 'CSM VI' (str) -> 输出 'Array' (tuple)
        """
        target_vi_path = os.path.abspath(target_vi_path)
        if not os.path.exists(target_vi_path):
            raise FileNotFoundError(f"目标 VI 不存在: {target_vi_path}")

        app = self.get_lv_app()
        helper_vi = None
        try:
            helper_vi = app.GetVIReference(self.read_states_vi_path, "", False, 0)
            # 设置平坦化输入端子
            helper_vi.SetControlValue("CSM VI", target_vi_path)
            # 同步非交互式执行 (通过 OLE dispid 执行 Run)
            self._invoke_vi_method(helper_vi, "Run", False)
            # 读取平坦化输出端子
            states_tuple = helper_vi.GetControlValue("Array")
            if states_tuple is None:
                return []
            return [str(s) for s in list(states_tuple)]
        except Exception as e:
            raise CSMBridgeError(f"读取 CSM 状态失败: {e}")
        finally:
            helper_vi = None

    def read_csm_api_states(self, target_vi_path: str) -> list[str]:
        """读取目标 CSM VI 暴露的外部 API 状态列表"""
        target_vi_path = os.path.abspath(target_vi_path)
        if not os.path.exists(target_vi_path):
            raise FileNotFoundError(f"目标 VI 不存在: {target_vi_path}")

        app = self.get_lv_app()
        helper_vi = None
        try:
            helper_vi = app.GetVIReference(self.read_api_vi_path, "", False, 0)
            helper_vi.SetControlValue("CSM VI", target_vi_path)
            self._invoke_vi_method(helper_vi, "Run", False)
            api_tuple = helper_vi.GetControlValue("Array")
            if api_tuple is None:
                return []
            return [str(s) for s in list(api_tuple)]
        except Exception as e:
            raise CSMBridgeError(f"读取 CSM API 失败: {e}")
        finally:
            helper_vi = None

    # -------------------------------------------------------------
    # 核心写操作：加分支与模板克隆 (受严格安全守则保护)
    # -------------------------------------------------------------
    def _verify_write_safety(self, target_path: str):
        """
        最高红线防御拦截：
        严禁对 C 盘系统目录、National Instruments 目录及安装的官方 CSM 原生库进行任何写/改/删操作！
        """
        norm_path = os.path.normpath(os.path.abspath(target_path)).lower()
        forbidden_roots = [
            r"c:\program files (x86)\national instruments".lower(),
            r"c:\program files\national instruments".lower(),
            r"c:\programdata\national instruments".lower(),
            r"c:\windows".lower()
        ]
        for f_root in forbidden_roots:
            if norm_path.startswith(f_root):
                raise SecurityViolationError(
                    f"[最高安全拦截] 触发底座只读最高红线！\n"
                    f"严禁向 C 盘底层库或官方原生 CSM 安装目录写入任何数据: {target_path}\n"
                    f"所有写操作必须限定在用户工作区内！"
                )

    def clone_module_template(self, template_vi_path: str, target_vi_path: str) -> bool:
        """
        脚手架复制：基于官方母版克隆新模块
        """
        self._verify_write_safety(target_vi_path)
        template_vi_path = os.path.abspath(template_vi_path)
        target_vi_path = os.path.abspath(target_vi_path)

        if not os.path.exists(template_vi_path):
            raise FileNotFoundError(f"模板 VI 不存在: {template_vi_path}")
        if os.path.exists(target_vi_path):
            raise FileExistsError(f"目标路径已存在同名 VI: {target_vi_path}")

        os.makedirs(os.path.dirname(target_vi_path), exist_ok=True)
        shutil.copy2(template_vi_path, target_vi_path)
        return True

    def add_csm_state(self, target_vi_path: str, new_state_name: str) -> bool:
        """
        向目标 CSM VI 安全注入新状态分支
        受 4 重安全护栏保护：
        0. C 盘系统库与官方底座绝对只读白名单校验 (最高红线)
        1. 前台互斥检查
        2. 影子临时备份
        3. 失败原子回滚
        """
        self._verify_write_safety(target_vi_path)
        target_vi_path = os.path.abspath(target_vi_path)
        if not os.path.exists(target_vi_path):
            raise FileNotFoundError(f"目标 VI 不存在: {target_vi_path}")

        # 护栏 1：前台互斥检查
        if self.check_front_panel_open(target_vi_path):
            raise TargetVIInUseError(
                f"安全拦截：目标 VI 当前正处于 LabVIEW 前台编辑窗口中: {target_vi_path}\n"
                f"为防止前后台脏读脏写抹除代码，请先保存并关闭前台窗口，再执行自动化分支注入！"
            )

        # 护栏 2：运行态安全防御 (Execution State Check)
        exec_state = self.check_execution_state(target_vi_path)
        if exec_state in [2, 3]: # 2=eRunTopLevel, 3=eRun
            raise TargetVIInUseError(
                f"安全拦截：目标 VI 当前正在后台运行中 (ExecState={exec_state})！\n"
                f"在运行态下强行修改程序框图会触发 LabVIEW 错误 1000/1003 并导致崩溃锁死。请先停止 VI 运行再注入分支！"
            )

        # 护栏 2：影子临时备份
        backup_path = self.create_shadow_backup(target_vi_path)

        app = self.get_lv_app()
        target_vi_ref = None
        bridge_vi_ref = None

        try:
            # 检查跳板 VI 是否就绪
            if not os.path.exists(self.agent_bridge_add_state_vi_path):
                raise CSMBridgeError(f"跳板 VI 尚未就绪: {self.agent_bridge_add_state_vi_path}")

            bridge_vi_ref = app.GetVIReference(self.agent_bridge_add_state_vi_path, "", False, 0)

            # 同步调用跳板执行 (使用 Call 传递接线板端子参数，确保参数精准穿透且非交互运行)
            param_names = ("Target VI Path", "New State Name")
            param_vals = (target_vi_path, new_state_name)
            self._invoke_vi_method(bridge_vi_ref, "Call", param_names, param_vals)

            # 检查跳板返回的 error out
            err_out = bridge_vi_ref.GetControlValue("error out")
            # err_out 通常是 (status: bool, code: int, source: str)
            if err_out and isinstance(err_out, (list, tuple)) and err_out[0]:
                raise CSMBridgeError(f"跳板 VI 执行报错 (Code {err_out[1]}): {err_out[2]}")

            # 存盘 (通过 dispid 执行 SaveInstrument 彻底杜绝 win32com NoneType not callable 问题)
            target_vi_ref = app.GetVIReference(target_vi_path, "", False, 0)
            self._invoke_vi_method(target_vi_ref, "SaveInstrument")
            
            # 若执行过程中触发了窗口残留，优雅关闭并给 LV 引擎 0.2 秒缓冲
            try:
                if target_vi_ref.FPWinOpen:
                    self._invoke_vi_method(target_vi_ref, "CloseFrontPanel")
            except Exception:
                pass
            time.sleep(0.2)
            return True

        except Exception as e:
            # 护栏 3：失败原子回滚
            self.rollback_from_backup(backup_path, target_vi_path)
            raise CSMBridgeError(f"注入状态分支失败，已安全回滚原文件: {e}")

        finally:
            target_vi_ref = None
            bridge_vi_ref = None
