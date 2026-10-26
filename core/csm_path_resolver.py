# -*- coding: utf-8 -*-
"""
LabVIEW 安装路径与 CSM 资产自适应定位引擎 (Path Resolver)
彻底根除路径写死、版本硬编码、盘符受限的采用门槛。

按 4 级自适应优先级探测：
1. 环境变量覆盖: LABVIEW_DIR (支持用户或 CI 自定义指定)
2. 注册表与 COM 完整性扫描 (优先匹配 8 大母版齐全的 32/64 位环境)
3. 盘符与全版本容灾扫描: (C/D/E/F 盘 LabVIEW 2020~2026 全系)
"""

import os
import sys
import winreg
from typing import Optional, Dict, List

class LabVIEWPathResolver:
    _cached_root: Optional[str] = None

    # CSM 相对资产路径映射字典 (标准出厂固定布局)
    TEMPLATE_RELATIVE_PATHS = {
        "worker": os.path.join("user.lib", "_NEVSTOP", "Communicable State Machine(CSM)", "CSM Module Template.vi"),
        "ui": os.path.join("user.lib", "_NEVSTOP", "Communicable State Machine(CSM)", "CSM User Interface(UI) Module Template.vi"),
        "worker_tiny": os.path.join("templates", "Communicable State Machine(CSM)", "CSM Module Template - Tiny.vi"),
        "ui_tiny": os.path.join("templates", "Communicable State Machine(CSM)", "CSM User Interface(UI) Module Template - Tiny.vi"),
        "worker_config": os.path.join("templates", "Communicable State Machine(CSM)", "CSM Module Template(+Configuration).vi"),
        "ui_config": os.path.join("templates", "Communicable State Machine(CSM)", "CSM User Interface(UI) Module Template(+Configuration).vi"),
        "dqmh": os.path.join("templates", "Communicable State Machine(CSM)", "CSM DQMH-Style Template.vi"),
        "reuse": os.path.join("examples", "NEVSTOP", "Communicable State Machine(CSM)", "1. Create a reuse Module", "CSM Reuse Module.vi")
    }

    HELPER_RELATIVE_PATHS = {
        "helper_dir": os.path.join("user.lib", "_NEVSTOP", "Communicable State Machine(CSM)", "_csmHelper", "API with lvcsm Support"),
        "read_states": os.path.join("user.lib", "_NEVSTOP", "Communicable State Machine(CSM)", "_csmHelper", "API with lvcsm Support", "Read CSM States By CSM-VI.vi"),
        "read_api": os.path.join("user.lib", "_NEVSTOP", "Communicable State Machine(CSM)", "_csmHelper", "API with lvcsm Support", "Read CSM API By CSM-VI.vi"),
    }

    @classmethod
    def count_available_templates(cls, root_path: str) -> int:
        """评估指定 LabVIEW 目录中就绪的 CSM 母版数量"""
        if not root_path or not os.path.isdir(root_path):
            return 0
        count = 0
        for rel in cls.TEMPLATE_RELATIVE_PATHS.values():
            if os.path.exists(os.path.join(root_path, rel)):
                count += 1
        return count

    @classmethod
    def get_labview_dir(cls, lv_app=None) -> str:
        """获取或解析 LabVIEW 安装根目录 (优先选择 CSM 资产最完备的安装目录)"""
        if cls._cached_root and os.path.exists(cls._cached_root):
            return cls._cached_root

        # -------------------------------------------------------------
        # 优先级 1: 环境变量显式覆盖 (LABVIEW_DIR)
        # -------------------------------------------------------------
        env_dir = os.environ.get("LABVIEW_DIR")
        if env_dir and os.path.isdir(env_dir):
            cls._cached_root = os.path.abspath(env_dir)
            return cls._cached_root

        # 收集所有潜在的 LabVIEW 安装候选路径
        all_candidates: List[str] = []

        # -------------------------------------------------------------
        # 注册表与 COM 收集
        # -------------------------------------------------------------
        reg_paths = cls._scan_registry_paths()
        for p in reg_paths:
            if p not in all_candidates:
                all_candidates.append(p)

        if lv_app is not None:
            try:
                app_dir = getattr(lv_app, "ApplicationDirectory", None)
                if app_dir and app_dir not in all_candidates:
                    all_candidates.insert(0, app_dir)
            except Exception:
                pass

        # 兜底常见盘符路径
        fallback_paths = cls._scan_fallback_paths()
        for p in fallback_paths:
            if p not in all_candidates and os.path.isdir(p):
                all_candidates.append(p)

        # -------------------------------------------------------------
        # 评分机制：寻找母版数量最多 (最完整) 的环境
        # -------------------------------------------------------------
        best_dir = None
        max_score = -1

        for cand in all_candidates:
            if not os.path.isdir(cand):
                continue
            score = cls.count_available_templates(cand)
            if score > max_score:
                max_score = score
                best_dir = cand
                if max_score >= len(cls.TEMPLATE_RELATIVE_PATHS):
                    # 已经找到 8/8 满配的安装路径，直接胜出
                    break

        if best_dir:
            cls._cached_root = os.path.abspath(best_dir)
            return cls._cached_root

        # 默认保底
        default_fallback = r"C:\Program Files (x86)\National Instruments\LabVIEW 2025"
        cls._cached_root = default_fallback
        return default_fallback

    @classmethod
    def _scan_registry_paths(cls) -> list:
        candidates = []
        # WOW6432Node (32位) 与 64 位原生注册表视图
        views = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\National Instruments\LabVIEW"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\National Instruments\LabVIEW")
        ]

        for hive, base_key in views:
            for sub_attempt in ["CurrentVersion", ""]:
                full_sub = f"{base_key}\\{sub_attempt}" if sub_attempt else base_key
                try:
                    with winreg.OpenKey(hive, full_sub) as k:
                        try:
                            val, _ = winreg.QueryValueEx(k, "Path")
                            if val and val.rstrip("\\/") not in candidates:
                                candidates.append(val.rstrip("\\/"))
                        except Exception:
                            pass
                        num_subkeys = winreg.QueryInfoKey(k)[0]
                        for i in range(num_subkeys):
                            sub_name = winreg.EnumKey(k, i)
                            try:
                                with winreg.OpenKey(k, sub_name) as ver_k:
                                    v_path, _ = winreg.QueryValueEx(ver_k, "Path")
                                    if v_path and v_path.rstrip("\\/") not in candidates:
                                        candidates.append(v_path.rstrip("\\/"))
                            except Exception:
                                pass
                except Exception:
                    pass
        return candidates

    @classmethod
    def _scan_fallback_paths(cls) -> list:
        drives = ["C", "D", "E", "F"]
        prog_folders = ["Program Files (x86)", "Program Files"]
        versions = ["2026", "2025", "2024", "2023", "2022", "2021", "2020"]
        cands = []
        for drv in drives:
            for pf in prog_folders:
                for v in versions:
                    path = f"{drv}:\\{pf}\\National Instruments\\LabVIEW {v}"
                    cands.append(path)
        return cands

    @classmethod
    def get_template_paths(cls, lv_app=None) -> Dict[str, str]:
        """获取所有 8 大母版的绝对路径映射"""
        root = cls.get_labview_dir(lv_app)
        return {
            name: os.path.join(root, rel)
            for name, rel in cls.TEMPLATE_RELATIVE_PATHS.items()
        }

    @classmethod
    def get_helper_paths(cls, lv_app=None) -> Dict[str, str]:
        """获取所有 CSM 官方平坦化 Helper VI 的绝对路径"""
        root = cls.get_labview_dir(lv_app)
        return {
            name: os.path.join(root, rel)
            for name, rel in cls.HELPER_RELATIVE_PATHS.items()
        }
